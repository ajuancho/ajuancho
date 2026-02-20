"""
Bahoy - Servicio de Análisis de Sesgos
Detecta y cuantifica cinco tipos de sesgo en el sistema de recomendaciones:
popularidad, geográfico, precio, burbuja de filtro y fuente.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.impression import RecommendationImpression
from app.models.interaction import Interaction
from app.models.source import Source
from app.models.venue import Venue


# ─────────────────────────────────────────────────────────────────────────────
# Umbrales de alerta
# ─────────────────────────────────────────────────────────────────────────────

# Un evento se considera "popular" si tiene más de esta cantidad de interacciones
_UMBRAL_POPULARIDAD = 10

# Si más del 80 % de las recomendaciones son de eventos populares → alerta
_ALERTA_POPULARIDAD = 0.80

# Si la diversidad de categorías por usuario cae por debajo de este valor → alerta
_ALERTA_BURBUJA = 0.40

# Buckets de precio en pesos argentinos
_PRECIO_BUCKETS = [
    ("gratuito", 0, 0),
    ("economico", 1, 999),
    ("moderado", 1000, 2999),
    ("premium", 3000, float("inf")),
]

# Porcentaje mínimo de recomendaciones que deben ser de eventos poco populares
_CUOTA_NO_POPULARES = 0.20

# Mínimo de categorías distintas que debe haber por conjunto de recomendaciones
_MIN_CATEGORIAS_POR_REC = 2

# Porcentaje máximo que puede ocupar una sola fuente en las recomendaciones
_MAX_CUOTA_FUENTE = 0.50


class BiasAnalyzer:
    """
    Analiza sesgos en el sistema de recomendaciones de Bahoy.

    Sesgos detectados:
    - Popularidad: ¿el sistema solo recomienda eventos muy conocidos?
    - Geográfico: ¿se favorecen ciertos barrios?
    - Precio: ¿se favorecen ciertos rangos de precio?
    - Burbuja de filtro: ¿los usuarios solo ven lo que ya les gusta?
    - Fuente: ¿dominan eventos de ciertas fuentes?
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers internos
    # ─────────────────────────────────────────────────────────────────────────

    async def _obtener_event_ids_recomendados(
        self, since: datetime
    ) -> list[str]:
        """Devuelve la lista plana de event_ids aparecidos en impresiones recientes."""
        result = await self.db.execute(
            select(RecommendationImpression.event_ids).where(
                RecommendationImpression.timestamp >= since
            )
        )
        all_event_ids: list[str] = []
        for row in result.scalars().all():
            if row:
                all_event_ids.extend(str(eid) for eid in row)
        return all_event_ids

    @staticmethod
    def _clasificar_precio(precio_min: float | None, es_gratuito: bool) -> str:
        """Clasifica un evento en uno de los buckets de precio."""
        if es_gratuito or precio_min == 0:
            return "gratuito"
        if precio_min is None:
            return "sin_informacion"
        for nombre, minimo, maximo in _PRECIO_BUCKETS:
            if nombre == "gratuito":
                continue
            if minimo <= precio_min <= maximo:
                return nombre
        return "premium"

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Sesgo de popularidad
    # ─────────────────────────────────────────────────────────────────────────

    async def analizar_popularidad(self, periodo_dias: int = 30) -> dict[str, Any]:
        """
        Analiza el sesgo de popularidad en las recomendaciones.

        Compara cuántos de los eventos recomendados son "populares"
        (tienen más de _UMBRAL_POPULARIDAD interacciones en el período)
        frente al total de eventos del catálogo con esa condición.

        Returns:
            Diccionario con métricas, distribución y flag de alerta.
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        # Eventos recomendados en el período
        event_ids_recomendados = await self._obtener_event_ids_recomendados(since)
        if not event_ids_recomendados:
            return {
                "sesgo": "popularidad",
                "periodo_dias": periodo_dias,
                "total_recomendados": 0,
                "populares_recomendados": 0,
                "porcentaje_populares": 0.0,
                "umbral_interacciones": _UMBRAL_POPULARIDAD,
                "alerta": False,
                "descripcion": "Sin datos de recomendaciones en el período.",
            }

        # Conteo de interacciones por evento en el período
        inter_result = await self.db.execute(
            select(Interaction.event_id, func.count(Interaction.id).label("total"))
            .where(Interaction.timestamp >= since)
            .group_by(Interaction.event_id)
        )
        interacciones_por_evento: dict[str, int] = {
            str(row.event_id): row.total for row in inter_result
        }

        # Clasificar cada slot de recomendación
        populares = sum(
            1
            for eid in event_ids_recomendados
            if interacciones_por_evento.get(eid, 0) > _UMBRAL_POPULARIDAD
        )

        total = len(event_ids_recomendados)
        porcentaje = round(populares / total, 4) if total else 0.0
        alerta = porcentaje > _ALERTA_POPULARIDAD

        # Distribución de interacciones en los eventos recomendados únicos
        conteos = [interacciones_por_evento.get(eid, 0) for eid in set(event_ids_recomendados)]
        distribucion = {
            "0_interacciones": sum(1 for c in conteos if c == 0),
            "1_a_5": sum(1 for c in conteos if 1 <= c <= 5),
            "6_a_10": sum(1 for c in conteos if 6 <= c <= 10),
            "mas_de_10": sum(1 for c in conteos if c > 10),
        }

        return {
            "sesgo": "popularidad",
            "periodo_dias": periodo_dias,
            "total_slots_recomendados": total,
            "eventos_unicos_recomendados": len(set(event_ids_recomendados)),
            "populares_recomendados": populares,
            "porcentaje_populares": porcentaje,
            "umbral_interacciones": _UMBRAL_POPULARIDAD,
            "distribucion_por_interacciones": distribucion,
            "alerta": alerta,
            "descripcion": (
                f"{porcentaje:.1%} de las recomendaciones son de eventos populares "
                f"(>{_UMBRAL_POPULARIDAD} interacciones). "
                + ("⚠ Supera el umbral de alerta." if alerta else "Dentro del rango aceptable.")
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Sesgo geográfico
    # ─────────────────────────────────────────────────────────────────────────

    async def analizar_geografico(self, periodo_dias: int = 30) -> dict[str, Any]:
        """
        Analiza la distribución geográfica de las recomendaciones por barrio.

        Compara la representación de cada barrio en las recomendaciones
        con su representación en el catálogo total de eventos.

        Returns:
            Diccionario con distribución de barrios, sobrerepresentación y alerta.
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        # Distribución de barrios en el catálogo completo
        catalogo_result = await self.db.execute(
            select(Venue.barrio, func.count(Event.id).label("total"))
            .join(Event, Event.venue_id == Venue.id)
            .where(Venue.barrio.isnot(None))
            .group_by(Venue.barrio)
        )
        catalogo_por_barrio: dict[str, int] = {
            row.barrio: row.total for row in catalogo_result
        }
        total_catalogo = sum(catalogo_por_barrio.values())

        # Eventos recomendados y sus barrios
        event_ids_recomendados = await self._obtener_event_ids_recomendados(since)
        if not event_ids_recomendados:
            return {
                "sesgo": "geografico",
                "periodo_dias": periodo_dias,
                "distribucion_catalogo": {},
                "distribucion_recomendaciones": {},
                "sobrerepresentacion": {},
                "alerta": False,
                "descripcion": "Sin datos de recomendaciones en el período.",
            }

        uuids_recomendados = list({uuid.UUID(eid) for eid in event_ids_recomendados if eid})

        barrio_result = await self.db.execute(
            select(Venue.barrio, func.count(Event.id).label("total"))
            .join(Event, Event.venue_id == Venue.id)
            .where(
                Event.id.in_(uuids_recomendados),
                Venue.barrio.isnot(None),
            )
            .group_by(Venue.barrio)
        )
        rec_por_barrio: dict[str, int] = {
            row.barrio: row.total for row in barrio_result
        }
        total_rec = sum(rec_por_barrio.values()) or 1

        # Proporciones
        prop_catalogo = {
            b: round(c / total_catalogo, 4) for b, c in catalogo_por_barrio.items()
        } if total_catalogo else {}
        prop_rec = {b: round(c / total_rec, 4) for b, c in rec_por_barrio.items()}

        # Sobrerepresentación = prop_rec / prop_catalogo  (>1 significa más recomendado que presente)
        sobrerepresentacion: dict[str, float] = {}
        for barrio, prop in prop_rec.items():
            cat_prop = prop_catalogo.get(barrio, 0.0)
            sobrerepresentacion[barrio] = round(prop / cat_prop, 2) if cat_prop > 0 else float("inf")

        # Alerta si algún barrio tiene sobrerepresentación mayor a 3x
        barrios_sobre = {b: v for b, v in sobrerepresentacion.items() if v > 3.0}
        alerta = len(barrios_sobre) > 0

        return {
            "sesgo": "geografico",
            "periodo_dias": periodo_dias,
            "total_eventos_catalogo": total_catalogo,
            "total_slots_recomendados_con_barrio": total_rec,
            "distribucion_catalogo": prop_catalogo,
            "distribucion_recomendaciones": prop_rec,
            "sobrerepresentacion": sobrerepresentacion,
            "barrios_sobrerepresentados": barrios_sobre,
            "alerta": alerta,
            "descripcion": (
                f"{len(barrios_sobre)} barrio(s) sobrerepresentados (>3x) en recomendaciones. "
                + ("⚠ Requiere atención." if alerta else "Distribución geográfica aceptable.")
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Sesgo de precio
    # ─────────────────────────────────────────────────────────────────────────

    async def analizar_precio(self, periodo_dias: int = 30) -> dict[str, Any]:
        """
        Analiza la distribución de rangos de precio en las recomendaciones
        frente al catálogo completo.

        Returns:
            Distribución por bucket de precio y comparativa con catálogo.
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        # Distribución de precio en el catálogo
        catalogo_result = await self.db.execute(
            select(Event.precio_min, Event.es_gratuito)
        )
        catalogo_buckets: dict[str, int] = defaultdict(int)
        for row in catalogo_result:
            bucket = self._clasificar_precio(
                float(row.precio_min) if row.precio_min is not None else None,
                bool(row.es_gratuito),
            )
            catalogo_buckets[bucket] += 1
        total_catalogo = sum(catalogo_buckets.values()) or 1

        # Precio de eventos recomendados
        event_ids_recomendados = await self._obtener_event_ids_recomendados(since)
        if not event_ids_recomendados:
            return {
                "sesgo": "precio",
                "periodo_dias": periodo_dias,
                "distribucion_catalogo": {},
                "distribucion_recomendaciones": {},
                "alerta": False,
                "descripcion": "Sin datos de recomendaciones en el período.",
            }

        uuids_recomendados = list({uuid.UUID(eid) for eid in event_ids_recomendados if eid})

        precio_result = await self.db.execute(
            select(Event.precio_min, Event.es_gratuito)
            .where(Event.id.in_(uuids_recomendados))
        )
        rec_buckets: dict[str, int] = defaultdict(int)
        for row in precio_result:
            bucket = self._clasificar_precio(
                float(row.precio_min) if row.precio_min is not None else None,
                bool(row.es_gratuito),
            )
            rec_buckets[bucket] += 1
        total_rec = sum(rec_buckets.values()) or 1

        prop_catalogo = {b: round(c / total_catalogo, 4) for b, c in catalogo_buckets.items()}
        prop_rec = {b: round(c / total_rec, 4) for b, c in rec_buckets.items()}

        # Alerta si la diferencia absoluta entre catalogo y recomendaciones supera 0.30
        max_diferencia = max(
            (abs(prop_rec.get(b, 0) - prop_catalogo.get(b, 0)) for b in set(prop_catalogo) | set(prop_rec)),
            default=0.0,
        )
        alerta = max_diferencia > 0.30

        return {
            "sesgo": "precio",
            "periodo_dias": periodo_dias,
            "total_eventos_catalogo": total_catalogo,
            "total_eventos_unicos_recomendados": len(uuids_recomendados),
            "distribucion_catalogo": prop_catalogo,
            "distribucion_recomendaciones": prop_rec,
            "max_diferencia_proporcional": round(max_diferencia, 4),
            "alerta": alerta,
            "descripcion": (
                f"Diferencia máxima de {max_diferencia:.1%} entre rangos de precio "
                "en recomendaciones vs catálogo. "
                + ("⚠ Sesgo de precio detectado." if alerta else "Distribución de precios aceptable.")
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Burbuja de filtro
    # ─────────────────────────────────────────────────────────────────────────

    async def analizar_burbuja_de_filtro(self, periodo_dias: int = 30) -> dict[str, Any]:
        """
        Evalúa si los usuarios están atrapados en una burbuja de filtro.

        Mide la diversidad de categorías por usuario a lo largo del tiempo.
        Alerta si la diversidad promedio cae por debajo de _ALERTA_BURBUJA.

        Returns:
            Diversidad promedio por usuario, tendencia y alertas individuales.
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        # Impresiones del período con user_id y event_ids
        imp_result = await self.db.execute(
            select(
                RecommendationImpression.user_id,
                RecommendationImpression.event_ids,
                RecommendationImpression.timestamp,
            )
            .where(RecommendationImpression.timestamp >= since)
            .order_by(RecommendationImpression.user_id, RecommendationImpression.timestamp)
        )
        impressions = imp_result.all()

        if not impressions:
            return {
                "sesgo": "burbuja_de_filtro",
                "periodo_dias": periodo_dias,
                "diversidad_promedio_global": 0.0,
                "usuarios_con_baja_diversidad": [],
                "alerta": False,
                "descripcion": "Sin datos de recomendaciones en el período.",
            }

        # Recopilar event_ids únicos para lookup de categorías
        all_uuids: set[uuid.UUID] = set()
        for _, event_ids, _ in impressions:
            if event_ids:
                for eid in event_ids:
                    try:
                        all_uuids.add(uuid.UUID(str(eid)))
                    except (ValueError, AttributeError):
                        continue

        cat_result = await self.db.execute(
            select(Event.id, Event.categoria_id).where(Event.id.in_(all_uuids))
        )
        event_to_cat: dict[str, str | None] = {
            str(row.id): str(row.categoria_id) if row.categoria_id else None
            for row in cat_result
        }

        # Diversidad por usuario: promedio de diversidades por impresión
        diversidad_por_usuario: dict[str, list[float]] = defaultdict(list)
        for user_id, event_ids, _ in impressions:
            if not event_ids:
                continue
            categorias = [
                event_to_cat.get(str(eid))
                for eid in event_ids
                if event_to_cat.get(str(eid)) is not None
            ]
            if not categorias:
                continue
            diversidad = len(set(categorias)) / len(event_ids)
            diversidad_por_usuario[str(user_id)].append(diversidad)

        if not diversidad_por_usuario:
            return {
                "sesgo": "burbuja_de_filtro",
                "periodo_dias": periodo_dias,
                "diversidad_promedio_global": 0.0,
                "usuarios_con_baja_diversidad": [],
                "alerta": False,
                "descripcion": "Sin suficientes datos para calcular diversidad.",
            }

        promedios_por_usuario = {
            uid: round(sum(vals) / len(vals), 4)
            for uid, vals in diversidad_por_usuario.items()
        }
        diversidad_global = round(
            sum(promedios_por_usuario.values()) / len(promedios_por_usuario), 4
        )

        usuarios_baja_diversidad = [
            {"user_id": uid, "diversidad_promedio": v}
            for uid, v in promedios_por_usuario.items()
            if v < _ALERTA_BURBUJA
        ]
        alerta = diversidad_global < _ALERTA_BURBUJA or len(usuarios_baja_diversidad) > 0

        return {
            "sesgo": "burbuja_de_filtro",
            "periodo_dias": periodo_dias,
            "total_usuarios_analizados": len(promedios_por_usuario),
            "diversidad_promedio_global": diversidad_global,
            "umbral_alerta": _ALERTA_BURBUJA,
            "usuarios_con_baja_diversidad": usuarios_baja_diversidad,
            "total_usuarios_burbuja": len(usuarios_baja_diversidad),
            "alerta": alerta,
            "descripcion": (
                f"Diversidad promedio global: {diversidad_global:.2f}. "
                f"{len(usuarios_baja_diversidad)} usuario(s) con diversidad < {_ALERTA_BURBUJA}. "
                + ("⚠ Burbuja de filtro detectada." if alerta else "Diversidad de categorías saludable.")
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Sesgo de fuente
    # ─────────────────────────────────────────────────────────────────────────

    async def analizar_fuente(self, periodo_dias: int = 30) -> dict[str, Any]:
        """
        Analiza si las recomendaciones están dominadas por eventos de ciertas fuentes.

        Compara la proporción de fuentes en las recomendaciones con la del catálogo.

        Returns:
            Distribución por fuente en recomendaciones vs catálogo y alertas.
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        # Distribución de fuentes en el catálogo
        catalogo_result = await self.db.execute(
            select(Source.nombre, func.count(Event.id).label("total"))
            .join(Event, Event.source_id == Source.id)
            .group_by(Source.nombre)
        )
        catalogo_por_fuente: dict[str, int] = {
            row.nombre: row.total for row in catalogo_result
        }
        total_catalogo = sum(catalogo_por_fuente.values()) or 1

        # Fuentes de eventos recomendados
        event_ids_recomendados = await self._obtener_event_ids_recomendados(since)
        if not event_ids_recomendados:
            return {
                "sesgo": "fuente",
                "periodo_dias": periodo_dias,
                "distribucion_catalogo": {},
                "distribucion_recomendaciones": {},
                "alerta": False,
                "descripcion": "Sin datos de recomendaciones en el período.",
            }

        uuids_recomendados = list({uuid.UUID(eid) for eid in event_ids_recomendados if eid})

        fuente_result = await self.db.execute(
            select(Source.nombre, func.count(Event.id).label("total"))
            .join(Event, Event.source_id == Source.id)
            .where(Event.id.in_(uuids_recomendados))
            .group_by(Source.nombre)
        )
        rec_por_fuente: dict[str, int] = {
            row.nombre: row.total for row in fuente_result
        }
        total_rec = sum(rec_por_fuente.values()) or 1

        prop_catalogo = {f: round(c / total_catalogo, 4) for f, c in catalogo_por_fuente.items()}
        prop_rec = {f: round(c / total_rec, 4) for f, c in rec_por_fuente.items()}

        fuentes_dominantes = {f: v for f, v in prop_rec.items() if v > _MAX_CUOTA_FUENTE}
        alerta = len(fuentes_dominantes) > 0

        return {
            "sesgo": "fuente",
            "periodo_dias": periodo_dias,
            "total_eventos_catalogo": total_catalogo,
            "total_eventos_unicos_recomendados": len(uuids_recomendados),
            "distribucion_catalogo": prop_catalogo,
            "distribucion_recomendaciones": prop_rec,
            "fuentes_dominantes": fuentes_dominantes,
            "umbral_dominancia": _MAX_CUOTA_FUENTE,
            "alerta": alerta,
            "descripcion": (
                f"{len(fuentes_dominantes)} fuente(s) superan el {_MAX_CUOTA_FUENTE:.0%} "
                "del total de recomendaciones. "
                + ("⚠ Sesgo de fuente detectado." if alerta else "Distribución de fuentes equilibrada.")
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Reporte completo
    # ─────────────────────────────────────────────────────────────────────────

    async def generar_reporte_completo(self, periodo_dias: int = 30) -> dict[str, Any]:
        """
        Genera un reporte unificado con todos los sesgos detectados.

        Args:
            periodo_dias: Días hacia atrás a analizar.

        Returns:
            Diccionario con análisis de cada sesgo, resumen de alertas y
            sugerencias de mitigación.
        """
        popularidad = await self.analizar_popularidad(periodo_dias)
        geografico = await self.analizar_geografico(periodo_dias)
        precio = await self.analizar_precio(periodo_dias)
        burbuja = await self.analizar_burbuja_de_filtro(periodo_dias)
        fuente = await self.analizar_fuente(periodo_dias)

        sesgos = {
            "popularidad": popularidad,
            "geografico": geografico,
            "precio": precio,
            "burbuja_de_filtro": burbuja,
            "fuente": fuente,
        }

        alertas_activas = [nombre for nombre, datos in sesgos.items() if datos.get("alerta")]

        mitigaciones = self.sugerir_mitigaciones(sesgos)

        return {
            "generado_en": datetime.now(timezone.utc).isoformat(),
            "periodo_dias": periodo_dias,
            "resumen": {
                "total_sesgos_analizados": len(sesgos),
                "alertas_activas": alertas_activas,
                "total_alertas": len(alertas_activas),
                "estado_general": "critico" if len(alertas_activas) >= 3 else (
                    "advertencia" if alertas_activas else "saludable"
                ),
            },
            "sesgos": sesgos,
            "mitigaciones_sugeridas": mitigaciones,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Sugerencias de mitigación
    # ─────────────────────────────────────────────────────────────────────────

    def sugerir_mitigaciones(self, reporte: dict[str, Any]) -> list[str]:
        """
        Genera sugerencias de mitigación basadas en los sesgos detectados.

        Recibe el diccionario de sesgos (o el reporte completo) y devuelve
        una lista de acciones concretas y priorizadas.

        Args:
            reporte: Diccionario con los análisis de cada tipo de sesgo.
                     Puede ser el campo ``sesgos`` del reporte completo o
                     el reporte completo en sí.

        Returns:
            Lista de strings con acciones de mitigación sugeridas.
        """
        # Admitir tanto el reporte completo como solo el dict de sesgos
        sesgos = reporte.get("sesgos", reporte)
        sugerencias: list[str] = []

        # ── Popularidad ──────────────────────────────────────────────────────
        pop = sesgos.get("popularidad", {})
        if pop.get("alerta"):
            pct = pop.get("porcentaje_populares", 0)
            cuota = int(_CUOTA_NO_POPULARES * 100)
            sugerencias.append(
                f"[POPULARIDAD] Forzar al menos el {cuota}% de recomendaciones de eventos "
                f"con pocas interacciones (actualmente solo el {(1 - pct):.1%} son poco conocidos). "
                "Implementar 'exploration boost' en el algoritmo híbrido."
            )
            sugerencias.append(
                "[POPULARIDAD] Aplicar penalización logarítmica a la puntuación de eventos "
                f"con >{_UMBRAL_POPULARIDAD} interacciones para nivelar el campo de juego."
            )

        # ── Geográfico ───────────────────────────────────────────────────────
        geo = sesgos.get("geografico", {})
        if geo.get("alerta"):
            barrios_sobre = geo.get("barrios_sobrerepresentados", {})
            barrios_str = ", ".join(barrios_sobre.keys()) if barrios_sobre else "desconocidos"
            sugerencias.append(
                f"[GEOGRAFICO] Limitar la proporción de recomendaciones de los barrios "
                f"sobrerepresentados ({barrios_str}). "
                "Implementar cuotas geográficas proporcionales al catálogo."
            )
            sugerencias.append(
                "[GEOGRAFICO] Enriquecer el catálogo de eventos en barrios subrepresentados "
                "priorizando esas fuentes en las próximas ejecuciones de scrapers."
            )

        # ── Precio ───────────────────────────────────────────────────────────
        precio = sesgos.get("precio", {})
        if precio.get("alerta"):
            diff = precio.get("max_diferencia_proporcional", 0)
            sugerencias.append(
                f"[PRECIO] Sesgo de precio detectado (diferencia máxima {diff:.1%}). "
                "Normalizar la distribución de precios en las recomendaciones para "
                "reflejar la diversidad del catálogo."
            )
            sugerencias.append(
                "[PRECIO] Garantizar que cada conjunto de recomendaciones incluya al menos "
                "un evento gratuito o de bajo costo cuando el usuario no haya indicado "
                "preferencias de precio."
            )

        # ── Burbuja de filtro ─────────────────────────────────────────────────
        burbuja = sesgos.get("burbuja_de_filtro", {})
        if burbuja.get("alerta"):
            n_usuarios = burbuja.get("total_usuarios_burbuja", 0)
            sugerencias.append(
                f"[BURBUJA] {n_usuarios} usuario(s) con baja diversidad de categorías. "
                f"Asegurar al menos {_MIN_CATEGORIAS_POR_REC} categorías distintas "
                "por conjunto de recomendaciones."
            )
            sugerencias.append(
                "[BURBUJA] Introducir un 'serendipity slot': reservar 1-2 posiciones en cada "
                "recomendación para eventos de categorías que el usuario no ha explorado "
                "en los últimos 14 días."
            )

        # ── Fuente ───────────────────────────────────────────────────────────
        fuente = sesgos.get("fuente", {})
        if fuente.get("alerta"):
            dominantes = fuente.get("fuentes_dominantes", {})
            fuentes_str = ", ".join(dominantes.keys()) if dominantes else "desconocidas"
            cuota = int(_MAX_CUOTA_FUENTE * 100)
            sugerencias.append(
                f"[FUENTE] Las fuentes '{fuentes_str}' superan el {cuota}% de las recomendaciones. "
                "Implementar rotación de fuentes: limitar cada fuente a un máximo del "
                f"{cuota}% por conjunto de recomendaciones."
            )

        if not sugerencias:
            sugerencias.append(
                "No se detectaron sesgos significativos. "
                "El sistema de recomendaciones opera dentro de los parámetros saludables."
            )

        return sugerencias

    # ─────────────────────────────────────────────────────────────────────────
    # Mitigaciones aplicables al generar recomendaciones
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def aplicar_cuota_no_populares(
        recomendaciones: list[dict],
        interacciones_por_evento: dict[str, int],
        cuota: float = _CUOTA_NO_POPULARES,
    ) -> list[dict]:
        """
        Garantiza que al menos ``cuota`` fracción de las recomendaciones
        sean de eventos poco populares.

        Mueve eventos poco populares al frente si la cuota no se cumple.

        Args:
            recomendaciones: Lista de dicts con al menos la clave ``event_id``.
            interacciones_por_evento: Mapa event_id → nº de interacciones.
            cuota: Fracción mínima de eventos poco populares (default 0.20).

        Returns:
            Lista reordenada respetando la cuota.
        """
        if not recomendaciones:
            return recomendaciones

        populares = [
            r for r in recomendaciones
            if interacciones_por_evento.get(str(r.get("event_id", "")), 0) > _UMBRAL_POPULARIDAD
        ]
        no_populares = [
            r for r in recomendaciones
            if interacciones_por_evento.get(str(r.get("event_id", "")), 0) <= _UMBRAL_POPULARIDAD
        ]

        total = len(recomendaciones)
        min_no_populares = max(1, int(total * cuota))

        # Si ya hay suficientes no populares, devolver en orden original
        if len(no_populares) >= min_no_populares:
            return recomendaciones

        # Intercalar: colocar no_populares disponibles primero, luego populares
        resultado = no_populares + populares
        return resultado[:total]

    @staticmethod
    def aplicar_diversidad_categorias(
        recomendaciones: list[dict],
        min_categorias: int = _MIN_CATEGORIAS_POR_REC,
    ) -> list[dict]:
        """
        Reordena recomendaciones para garantizar al menos ``min_categorias``
        categorías distintas en las primeras posiciones.

        Args:
            recomendaciones: Lista de dicts con clave ``categoria_id``.
            min_categorias: Número mínimo de categorías distintas al inicio.

        Returns:
            Lista reordenada con diversidad garantizada.
        """
        if not recomendaciones:
            return recomendaciones

        resultado: list[dict] = []
        resto: list[dict] = []
        categorias_vistas: set = set()

        for rec in recomendaciones:
            cat = rec.get("categoria_id")
            if cat not in categorias_vistas and len(categorias_vistas) < min_categorias:
                resultado.append(rec)
                categorias_vistas.add(cat)
            else:
                resto.append(rec)

        return resultado + resto

    @staticmethod
    def aplicar_rotacion_fuentes(
        recomendaciones: list[dict],
        max_cuota_fuente: float = _MAX_CUOTA_FUENTE,
    ) -> list[dict]:
        """
        Limita que una única fuente ocupe más de ``max_cuota_fuente`` del total.

        Desplaza el exceso al final del listado sin descartarlo.

        Args:
            recomendaciones: Lista de dicts con clave ``source_id``.
            max_cuota_fuente: Fracción máxima permitida por fuente.

        Returns:
            Lista con rotación de fuentes aplicada.
        """
        if not recomendaciones:
            return recomendaciones

        total = len(recomendaciones)
        max_por_fuente = max(1, int(total * max_cuota_fuente))

        conteo_fuente: dict[str, int] = defaultdict(int)
        resultado: list[dict] = []
        exceso: list[dict] = []

        for rec in recomendaciones:
            fuente = str(rec.get("source_id", "desconocida"))
            if conteo_fuente[fuente] < max_por_fuente:
                resultado.append(rec)
                conteo_fuente[fuente] += 1
            else:
                exceso.append(rec)

        return resultado + exceso
