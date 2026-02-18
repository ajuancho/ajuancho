"""
Bahoy - Servicio de Recomendaciones
Motor de recomendación de eventos culturales.

Fase 1: Filtrado explícito por preferencias declaradas del usuario.
"""

import uuid
from collections import Counter
from datetime import datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.event import Event
from app.models.interaction import Interaction, InteractionType
from app.models.user import User
from app.models.venue import Venue


class RecommenderService:
    """
    Motor de recomendaciones de eventos culturales de Buenos Aires.
    Fase 1: filtrado explícito basado en preferencias declaradas del usuario.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─────────────────────────────────────────────────────────────────────────
    # Métodos públicos
    # ─────────────────────────────────────────────────────────────────────────

    async def recomendar_para_usuario(
        self, user_id: str, limite: int = 10
    ) -> list[dict[str, Any]]:
        """
        Recomendaciones personalizadas basadas en preferencias explícitas.

        Algoritmo:
        1. Cargar preferencias del usuario
        2. Filtrar eventos futuros que coincidan con categorías favoritas
        3. Puntuar también por barrios preferidos
        4. Considerar rango de precio
        5. Filtrar por disponibilidad (fechas futuras)
        6. Ordenar por relevancia (puntaje)
        7. Diversificar (máximo 3 eventos por categoría)
        """
        user = await self._get_user(user_id)
        if not user:
            return []

        prefs = user.preferencias or {}
        categorias_fav = [c.lower() for c in prefs.get("categorias_favoritas", [])]
        barrios_fav = [b.lower() for b in prefs.get("barrios_preferidos", [])]
        rango = prefs.get("rango_precio") or prefs.get("rango_precios") or {}
        precio_max: float | None = rango.get("max")
        precio_min_pref: float | None = rango.get("min")
        tags_interes = [t.lower() for t in prefs.get("tags_interes", [])]

        # Sin preferencias declaradas → popular
        if not categorias_fav and not barrios_fav and not tags_interes:
            return await self.recomendar_populares(limite)

        ahora = datetime.now(timezone.utc)

        # ── Consulta con filtros DB ──────────────────────────────────────────
        # Filtramos por categorías en la DB (el filtro más discriminante).
        # Los filtros de barrio y tags se aplican en Python al puntuar.
        query = (
            select(Event)
            .options(selectinload(Event.venue), selectinload(Event.categoria))
            .join(Category, Event.categoria_id == Category.id, isouter=True)
            .where(Event.fecha_inicio >= ahora)
        )

        if categorias_fav:
            query = query.where(
                func.lower(Category.nombre).in_(categorias_fav)
            )

        if precio_max is not None:
            query = query.where(
                or_(Event.es_gratuito.is_(True), Event.precio_min <= precio_max)
            )

        query = query.order_by(Event.fecha_inicio.asc()).limit(limite * 5)
        result = await self.db.execute(query)
        candidatos = list(result.scalars().all())

        # Si no hay candidatos con categorías favoritas, usar todos los futuros
        if not candidatos:
            candidatos = await self._get_eventos_futuros(ahora, limite * 5)

        if not candidatos:
            return await self.recomendar_populares(limite)

        # ── Puntuar y generar razones ────────────────────────────────────────
        scored: list[tuple[float, Event, str]] = []
        for event in candidatos:
            puntaje, razon = self._puntuar_evento(
                event,
                categorias_fav,
                barrios_fav,
                precio_min_pref,
                precio_max,
                tags_interes,
            )
            scored.append((puntaje, event, razon))

        scored.sort(key=lambda x: x[0], reverse=True)

        return self._diversificar(scored, max_por_categoria=3, limite=limite)

    async def recomendar_similares(
        self, event_id: str, limite: int = 5
    ) -> list[dict[str, Any]]:
        """
        Eventos similares a uno dado.
        Usa: misma categoría + embeddings vectoriales (si disponibles) + fechas cercanas.
        """
        evento_ref = await self._get_evento(event_id)
        if not evento_ref:
            return []

        ahora = datetime.now(timezone.utc)

        query = (
            select(Event)
            .options(selectinload(Event.venue), selectinload(Event.categoria))
            .where(Event.id != evento_ref.id, Event.fecha_inicio >= ahora)
        )

        if evento_ref.categoria_id:
            query = query.where(Event.categoria_id == evento_ref.categoria_id)

        # Ordenar por similitud vectorial si hay embedding; si no, por fecha
        if evento_ref.embedding is not None:
            query = query.order_by(
                Event.embedding.cosine_distance(evento_ref.embedding)
            )
        else:
            query = query.order_by(Event.fecha_inicio.asc())

        query = query.limit(limite)
        result = await self.db.execute(query)
        candidatos = list(result.scalars().all())

        cat_nombre = (
            evento_ref.categoria.nombre if evento_ref.categoria else "mismo género"
        )
        titulo_ref = evento_ref.titulo[:40]

        return [
            {
                "event": self._serializar_evento(e),
                "razon": (
                    f"Similar a '{titulo_ref}' · categoría: {cat_nombre}"
                ),
            }
            for e in candidatos
        ]

    async def recomendar_populares(
        self, limite: int = 10
    ) -> list[dict[str, Any]]:
        """
        Eventos más populares para usuarios sin historial o sin preferencias.

        Puntuación de popularidad:
          guardado/asistió: ×3 · compartido: ×2 · vista: ×1 · clic: ×0.5
        Se complementa con los próximos eventos si hay pocos con interacciones.
        """
        ahora = datetime.now(timezone.utc)

        # Contar interacciones agrupadas por evento y tipo
        rows_result = await self.db.execute(
            select(
                Interaction.event_id,
                Interaction.tipo,
                func.count(Interaction.id).label("n"),
            ).group_by(Interaction.event_id, Interaction.tipo)
        )
        rows = rows_result.all()

        pesos = {
            InteractionType.GUARDADO: 3.0,
            InteractionType.ASISTIO: 3.0,
            InteractionType.COMPARTIDO: 2.0,
            InteractionType.VISTA: 1.0,
            InteractionType.CLIC: 0.5,
        }

        puntajes: dict[uuid.UUID, float] = {}
        for row in rows:
            eid = row.event_id
            puntajes[eid] = puntajes.get(eid, 0.0) + pesos.get(row.tipo, 0.5) * row.n

        eventos: list[Event] = []

        if puntajes:
            top_ids = sorted(puntajes, key=lambda eid: puntajes[eid], reverse=True)
            result = await self.db.execute(
                select(Event)
                .options(selectinload(Event.venue), selectinload(Event.categoria))
                .where(
                    Event.id.in_(top_ids[: limite * 3]),
                    Event.fecha_inicio >= ahora,
                )
                .order_by(Event.fecha_inicio.asc())
                .limit(limite)
            )
            eventos = list(result.scalars().all())

        # Completar con próximos eventos si faltan
        if len(eventos) < limite:
            ya_incluidos = {e.id for e in eventos}
            extra_result = await self.db.execute(
                select(Event)
                .options(selectinload(Event.venue), selectinload(Event.categoria))
                .where(
                    Event.fecha_inicio >= ahora,
                    Event.id.notin_(ya_incluidos) if ya_incluidos else True,
                )
                .order_by(Event.fecha_inicio.asc())
                .limit(limite - len(eventos))
            )
            eventos += list(extra_result.scalars().all())

        return [
            {
                "event": self._serializar_evento(e),
                "razon": "Evento popular en la comunidad Bahoy",
            }
            for e in eventos[:limite]
        ]

    async def recomendar_por_contexto(
        self, contexto: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Recomendaciones contextuales sin necesidad de historial del usuario.

        Claves reconocidas en `contexto`:
          - query  : texto libre ("esta noche", "gratis", "con niños", "fin de semana")
          - barrio : nombre de barrio (str)
          - gratis : solo gratuitos (bool)
        """
        ahora = datetime.now(timezone.utc)
        query_text = (contexto.get("query") or "").lower()
        razones: list[str] = []

        filtros: list[Any] = [Event.fecha_inicio >= ahora]

        # ── Gratuito ─────────────────────────────────────────────────────────
        if contexto.get("gratis") or any(
            k in query_text for k in ("gratis", "gratuito", "gratis", "free")
        ):
            filtros.append(Event.es_gratuito.is_(True))
            razones.append("evento gratuito")

        # ── Con niños / familiar ──────────────────────────────────────────────
        if any(
            k in query_text
            for k in ("niños", "ninos", "familiar", "familia", "kids", "infantil")
        ):
            filtros.append(
                or_(
                    Event.tags.contains(["familiar"]),
                    Event.tags.contains(["niños"]),
                    Event.tags.contains(["familia"]),
                    Event.tags.contains(["infantil"]),
                )
            )
            razones.append("apto para niños y familia")

        # ── Esta noche ────────────────────────────────────────────────────────
        if "esta noche" in query_text or (
            "noche" in query_text and "esta noche" not in query_text
        ):
            hoy = ahora.date()
            inicio_noche = datetime.combine(hoy, time(19, 0), tzinfo=timezone.utc)
            fin_noche = datetime.combine(hoy, time(23, 59), tzinfo=timezone.utc)
            filtros += [
                Event.fecha_inicio >= inicio_noche,
                Event.fecha_inicio <= fin_noche,
            ]
            razones.append("esta noche")

        # ── Hoy ───────────────────────────────────────────────────────────────
        elif "hoy" in query_text:
            hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
            hoy_fin = ahora.replace(hour=23, minute=59, second=59, microsecond=0)
            filtros += [
                Event.fecha_inicio >= hoy_inicio,
                Event.fecha_inicio <= hoy_fin,
            ]
            razones.append("hoy")

        # ── Fin de semana ─────────────────────────────────────────────────────
        elif any(k in query_text for k in ("fin de semana", "finde", "weekend")):
            dias_hasta_sabado = (5 - ahora.weekday()) % 7 or 7
            sabado = (ahora + timedelta(days=dias_hasta_sabado)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            fin_domingo = sabado + timedelta(days=1, hours=23, minutes=59, seconds=59)
            filtros += [
                Event.fecha_inicio >= sabado,
                Event.fecha_inicio <= fin_domingo,
            ]
            razones.append("este fin de semana")

        # ── Barrio específico ─────────────────────────────────────────────────
        barrio = contexto.get("barrio")
        stmt = (
            select(Event)
            .options(selectinload(Event.venue), selectinload(Event.categoria))
        )

        if barrio:
            stmt = stmt.join(Venue, Event.venue_id == Venue.id).where(
                *filtros, func.lower(Venue.barrio) == barrio.lower()
            )
            razones.append(f"en {barrio}")
        else:
            stmt = stmt.where(*filtros)

        stmt = stmt.order_by(Event.fecha_inicio.asc()).limit(20)
        result = await self.db.execute(stmt)
        eventos = list(result.scalars().all())

        razon_str = (
            "Seleccionado porque: " + " · ".join(razones)
            if razones
            else "Próximamente en Buenos Aires"
        )

        return [
            {"event": self._serializar_evento(e), "razon": razon_str}
            for e in eventos
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers privados
    # ─────────────────────────────────────────────────────────────────────────

    async def _get_user(self, user_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        return result.scalar_one_or_none()

    async def _get_evento(self, event_id: str) -> Event | None:
        result = await self.db.execute(
            select(Event)
            .options(selectinload(Event.venue), selectinload(Event.categoria))
            .where(Event.id == uuid.UUID(event_id))
        )
        return result.scalar_one_or_none()

    async def _get_eventos_futuros(
        self, desde: datetime, limite: int
    ) -> list[Event]:
        result = await self.db.execute(
            select(Event)
            .options(selectinload(Event.venue), selectinload(Event.categoria))
            .where(Event.fecha_inicio >= desde)
            .order_by(Event.fecha_inicio.asc())
            .limit(limite)
        )
        return list(result.scalars().all())

    def _puntuar_evento(
        self,
        event: Event,
        categorias_fav: list[str],
        barrios_fav: list[str],
        precio_min_pref: float | None,
        precio_max: float | None,
        tags_interes: list[str],
    ) -> tuple[float, str]:
        """
        Calcula el puntaje de relevancia y genera el texto de razón.

        Pesos:
          categoría favorita   → +5
          barrio preferido     → +3
          precio dentro rango  → +2
          evento gratuito      → +2 (si hay filtro de precio)
          tag de interés       → +1.5 por coincidencia
          proximidad ≤3 días   → +2
          proximidad ≤7 días   → +1
        """
        puntaje = 0.0
        razones: list[str] = []

        cat_nombre = (
            event.categoria.nombre.lower() if event.categoria else ""
        )
        if cat_nombre and cat_nombre in categorias_fav:
            puntaje += 5.0
            razones.append(f"eventos de {event.categoria.nombre}")  # type: ignore[union-attr]

        barrio_evento = (
            event.venue.barrio.lower()
            if event.venue and event.venue.barrio
            else ""
        )
        if barrio_evento and barrio_evento in barrios_fav:
            puntaje += 3.0
            razones.append(f"en {event.venue.barrio}")  # type: ignore[union-attr]

        if precio_max is not None:
            if event.es_gratuito:
                puntaje += 2.0
                razones.append("gratuito")
            elif event.precio_min is not None and float(event.precio_min) <= precio_max:
                puntaje += 2.0
                razones.append("dentro de tu rango de precio")

        event_tags = [t.lower() for t in (event.tags or [])]
        matches = set(tags_interes) & set(event_tags)
        if matches:
            puntaje += len(matches) * 1.5
            razones.append(f"etiquetado: {', '.join(sorted(matches))}")

        if event.fecha_inicio:
            dias = (event.fecha_inicio - datetime.now(timezone.utc)).days
            if dias <= 3:
                puntaje += 2.0
            elif dias <= 7:
                puntaje += 1.0

        if razones:
            razon = "Porque te gustan: " + " · ".join(razones)
        else:
            razon = "Próximamente en Buenos Aires"

        return puntaje, razon

    def _diversificar(
        self,
        scored: list[tuple[float, Event, str]],
        max_por_categoria: int,
        limite: int,
    ) -> list[dict[str, Any]]:
        """
        Selecciona los mejores eventos garantizando diversidad de categorías.
        Permite hasta `max_por_categoria` eventos de la misma categoría.
        """
        contador: Counter[str] = Counter()
        resultado: list[dict[str, Any]] = []

        for _puntaje, event, razon in scored:
            if len(resultado) >= limite:
                break
            cat_key = str(event.categoria_id) if event.categoria_id else "sin_categoria"
            if contador[cat_key] < max_por_categoria:
                contador[cat_key] += 1
                resultado.append(
                    {"event": self._serializar_evento(event), "razon": razon}
                )

        return resultado

    def _serializar_evento(self, event: Event) -> dict[str, Any]:
        """Convierte un objeto Event ORM a un dict JSON-serializable."""
        return {
            "id": str(event.id),
            "titulo": event.titulo,
            "descripcion": event.descripcion,
            "categoria": event.categoria.nombre if event.categoria else None,
            "subcategorias": event.subcategorias,
            "fecha_inicio": (
                event.fecha_inicio.isoformat() if event.fecha_inicio else None
            ),
            "fecha_fin": event.fecha_fin.isoformat() if event.fecha_fin else None,
            "venue": (
                {
                    "id": str(event.venue.id),
                    "nombre": event.venue.nombre,
                    "barrio": event.venue.barrio,
                    "direccion": event.venue.direccion,
                }
                if event.venue
                else None
            ),
            "precio_min": (
                float(event.precio_min) if event.precio_min is not None else None
            ),
            "precio_max": (
                float(event.precio_max) if event.precio_max is not None else None
            ),
            "es_gratuito": event.es_gratuito,
            "imagen_url": event.imagen_url,
            "url_fuente": event.url_fuente,
            "tags": event.tags,
        }
