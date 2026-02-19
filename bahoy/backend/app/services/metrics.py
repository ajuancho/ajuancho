"""
Bahoy - Servicio de Métricas de Recomendación
Evalúa la calidad del sistema de recomendaciones mediante cinco métricas clave:
CTR, Tasa de Guardado, Diversidad, Cobertura y Precision@K.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.impression import RecommendationImpression
from app.models.interaction import Interaction, InteractionType


# Tipos de interacción que se consideran "positivas" (el usuario mostró interés real)
_INTERACCIONES_POSITIVAS = [
    InteractionType.CLIC,
    InteractionType.GUARDADO,
    InteractionType.ASISTIO,
    InteractionType.COMPARTIDO,
]


class MetricsService:
    """
    Servicio de evaluación de métricas del sistema de recomendaciones.

    Métricas implementadas:
    - CTR (Click-Through Rate): ratio de clics sobre impresiones
    - Tasa de Guardado: porcentaje de recomendaciones guardadas
    - Diversidad: variedad de categorías en las recomendaciones
    - Cobertura: porcentaje del catálogo que el sistema recomienda
    - Precision@K: precisión en las K primeras recomendaciones
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─────────────────────────────────────────────────────────────────────────
    # Registro de impresiones
    # ─────────────────────────────────────────────────────────────────────────

    async def registrar_impresion(
        self,
        user_id: uuid.UUID | str,
        event_ids: list[uuid.UUID | str],
        tipo_recomendacion: str,
    ) -> RecommendationImpression:
        """
        Guarda que se mostraron estas recomendaciones al usuario.

        Args:
            user_id: ID del usuario que recibió las recomendaciones
            event_ids: Lista de IDs de eventos recomendados
            tipo_recomendacion: Tipo de algoritmo usado (ej: "hibrido", "populares")

        Returns:
            El registro de impresión creado
        """
        impresion = RecommendationImpression(
            user_id=uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id,
            event_ids=[str(eid) for eid in event_ids],
            tipo_recomendacion=tipo_recomendacion,
        )
        self.db.add(impresion)
        await self.db.commit()
        await self.db.refresh(impresion)
        return impresion

    # ─────────────────────────────────────────────────────────────────────────
    # Métricas individuales
    # ─────────────────────────────────────────────────────────────────────────

    async def calcular_ctr(self, periodo_dias: int = 7) -> float:
        """
        Calcula el CTR (Click-Through Rate) de los últimos N días.

        CTR = total de clics / total de slots de eventos recomendados mostrados

        Args:
            periodo_dias: Número de días hacia atrás a analizar

        Returns:
            CTR como flotante entre 0.0 y 1.0
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        # Total de slots de impresión (cada event_id mostrado cuenta como 1)
        imp_result = await self.db.execute(
            select(RecommendationImpression.event_ids)
            .where(RecommendationImpression.timestamp >= since)
        )
        all_event_ids = imp_result.scalars().all()
        total_impresiones = sum(len(eids) for eids in all_event_ids if eids)

        if total_impresiones == 0:
            return 0.0

        # Total de clics en el mismo período
        clics_result = await self.db.execute(
            select(func.count(Interaction.id))
            .where(
                Interaction.tipo == InteractionType.CLIC,
                Interaction.timestamp >= since,
            )
        )
        total_clics = clics_result.scalar() or 0

        return round(total_clics / total_impresiones, 4)

    async def calcular_tasa_guardado(self, periodo_dias: int = 7) -> float:
        """
        Calcula la tasa de guardado de los últimos N días.

        Tasa de guardado = guardados / slots de eventos recomendados mostrados

        Args:
            periodo_dias: Número de días hacia atrás a analizar

        Returns:
            Tasa de guardado como flotante entre 0.0 y 1.0
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        imp_result = await self.db.execute(
            select(RecommendationImpression.event_ids)
            .where(RecommendationImpression.timestamp >= since)
        )
        all_event_ids = imp_result.scalars().all()
        total_impresiones = sum(len(eids) for eids in all_event_ids if eids)

        if total_impresiones == 0:
            return 0.0

        guardados_result = await self.db.execute(
            select(func.count(Interaction.id))
            .where(
                Interaction.tipo == InteractionType.GUARDADO,
                Interaction.timestamp >= since,
            )
        )
        total_guardados = guardados_result.scalar() or 0

        return round(total_guardados / total_impresiones, 4)

    async def calcular_diversidad(self, periodo_dias: int = 7) -> float:
        """
        Calcula la diversidad promedio de las recomendaciones.

        Diversidad por impresión = categorías distintas / total eventos recomendados
        Diversidad global = promedio de diversidades por impresión

        Un valor de 1.0 indica que todos los eventos recomendados son de categorías
        distintas; 0.0 indica que todos son de la misma categoría.

        Args:
            periodo_dias: Número de días hacia atrás a analizar

        Returns:
            Diversidad promedio como flotante entre 0.0 y 1.0
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        imp_result = await self.db.execute(
            select(RecommendationImpression.event_ids)
            .where(RecommendationImpression.timestamp >= since)
        )
        impressions_event_ids = imp_result.scalars().all()

        if not impressions_event_ids:
            return 0.0

        # Recopilar todos los event_ids únicos para una sola consulta de categorías
        all_event_uuids: set[uuid.UUID] = set()
        for event_ids in impressions_event_ids:
            if event_ids:
                for eid in event_ids:
                    try:
                        all_event_uuids.add(uuid.UUID(str(eid)))
                    except (ValueError, AttributeError):
                        continue

        if not all_event_uuids:
            return 0.0

        # Obtener categorías de todos los eventos en una sola consulta
        cat_result = await self.db.execute(
            select(Event.id, Event.categoria_id)
            .where(Event.id.in_(all_event_uuids))
        )
        event_to_category: dict[str, uuid.UUID | None] = {
            str(row.id): row.categoria_id for row in cat_result
        }

        # Calcular diversidad por impresión
        diversidades = []
        for event_ids in impressions_event_ids:
            if not event_ids:
                continue

            categorias = [
                event_to_category.get(str(eid))
                for eid in event_ids
                if event_to_category.get(str(eid)) is not None
            ]

            if not categorias:
                continue

            distintas = len(set(categorias))
            total = len(event_ids)
            diversidades.append(distintas / total)

        if not diversidades:
            return 0.0

        return round(sum(diversidades) / len(diversidades), 4)

    async def calcular_cobertura(self) -> float:
        """
        Calcula la cobertura del catálogo.

        Cobertura = eventos recomendados alguna vez / total de eventos en el catálogo

        Args: (sin período — usa todo el historial)

        Returns:
            Cobertura como flotante entre 0.0 y 1.0
        """
        # Obtener todos los event_ids que han aparecido en alguna impresión
        imp_result = await self.db.execute(
            select(RecommendationImpression.event_ids)
        )
        all_impressions = imp_result.scalars().all()

        eventos_recomendados: set[str] = set()
        for event_ids in all_impressions:
            if event_ids:
                eventos_recomendados.update(str(eid) for eid in event_ids)

        # Total de eventos en el catálogo
        total_result = await self.db.execute(
            select(func.count(Event.id))
        )
        total_eventos = total_result.scalar() or 0

        if total_eventos == 0:
            return 0.0

        return round(len(eventos_recomendados) / total_eventos, 4)

    async def calcular_precision_at_k(
        self, k: int = 10, periodo_dias: int = 7
    ) -> float:
        """
        Calcula Precision@K: de las K primeras recomendaciones, cuántas resultaron
        en una interacción positiva del usuario.

        Se considera interacción positiva: clic, guardado, asistencia o compartido.

        Args:
            k: Número de recomendaciones a evaluar por impresión
            periodo_dias: Número de días hacia atrás a analizar

        Returns:
            Precision@K promedio como flotante entre 0.0 y 1.0
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        imp_result = await self.db.execute(
            select(
                RecommendationImpression.user_id,
                RecommendationImpression.event_ids,
                RecommendationImpression.timestamp,
            )
            .where(RecommendationImpression.timestamp >= since)
        )
        impressions = imp_result.all()

        if not impressions:
            return 0.0

        # Recopilar todos los pares (user_id, event_id) para una sola consulta
        # de interacciones positivas
        all_user_ids: set[uuid.UUID] = set()
        all_event_uuids: set[uuid.UUID] = set()

        for user_id, event_ids, _ in impressions:
            if event_ids:
                all_user_ids.add(user_id)
                for eid in event_ids[:k]:
                    try:
                        all_event_uuids.add(uuid.UUID(str(eid)))
                    except (ValueError, AttributeError):
                        continue

        if not all_event_uuids:
            return 0.0

        # Obtener todas las interacciones positivas relevantes en una sola consulta
        inter_result = await self.db.execute(
            select(Interaction.user_id, Interaction.event_id)
            .where(
                Interaction.user_id.in_(all_user_ids),
                Interaction.event_id.in_(all_event_uuids),
                Interaction.tipo.in_(_INTERACCIONES_POSITIVAS),
                Interaction.timestamp >= since,
            )
        )
        # Crear un set de pares (user_id, event_id) con interacción positiva
        interacciones_positivas: set[tuple[str, str]] = {
            (str(row.user_id), str(row.event_id)) for row in inter_result
        }

        # Calcular precision@k por impresión
        precisiones = []
        for user_id, event_ids, _ in impressions:
            if not event_ids:
                continue

            k_events = event_ids[:k]
            if not k_events:
                continue

            positivos = sum(
                1
                for eid in k_events
                if (str(user_id), str(eid)) in interacciones_positivas
            )
            precisiones.append(positivos / k)

        if not precisiones:
            return 0.0

        return round(sum(precisiones) / len(precisiones), 4)

    # ─────────────────────────────────────────────────────────────────────────
    # Reporte completo
    # ─────────────────────────────────────────────────────────────────────────

    async def generar_reporte(self, periodo_dias: int = 30) -> dict[str, Any]:
        """
        Genera un reporte completo de métricas del sistema de recomendaciones.

        Calcula todas las métricas disponibles para el período especificado
        y las devuelve en un diccionario estructurado.

        Args:
            periodo_dias: Número de días hacia atrás a analizar

        Returns:
            Diccionario con todas las métricas, totales y metadatos del reporte
        """
        since = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        # Calcular todas las métricas en paralelo conceptual
        # (se ejecutan secuencialmente dado el modelo async de SQLAlchemy)
        ctr = await self.calcular_ctr(periodo_dias)
        tasa_guardado = await self.calcular_tasa_guardado(periodo_dias)
        diversidad = await self.calcular_diversidad(periodo_dias)
        cobertura = await self.calcular_cobertura()
        precision_k = await self.calcular_precision_at_k(k=10, periodo_dias=periodo_dias)

        # Totales del período para contexto
        imp_result = await self.db.execute(
            select(func.count(RecommendationImpression.id))
            .where(RecommendationImpression.timestamp >= since)
        )
        total_impresiones = imp_result.scalar() or 0

        inter_result = await self.db.execute(
            select(func.count(Interaction.id))
            .where(Interaction.timestamp >= since)
        )
        total_interacciones = inter_result.scalar() or 0

        # Interacciones por tipo
        tipos_result = await self.db.execute(
            select(Interaction.tipo, func.count(Interaction.id).label("total"))
            .where(Interaction.timestamp >= since)
            .group_by(Interaction.tipo)
        )
        interacciones_por_tipo = {
            row.tipo.value: row.total for row in tipos_result
        }

        # Distribución por tipo de recomendación
        tipos_rec_result = await self.db.execute(
            select(
                RecommendationImpression.tipo_recomendacion,
                func.count(RecommendationImpression.id).label("total"),
            )
            .where(RecommendationImpression.timestamp >= since)
            .group_by(RecommendationImpression.tipo_recomendacion)
        )
        impresiones_por_tipo = {
            row.tipo_recomendacion: row.total for row in tipos_rec_result
        }

        return {
            "periodo_dias": periodo_dias,
            "generado_en": datetime.now(timezone.utc).isoformat(),
            "metricas": {
                "ctr": ctr,
                "tasa_guardado": tasa_guardado,
                "diversidad": diversidad,
                "cobertura": cobertura,
                "precision_at_10": precision_k,
            },
            "totales": {
                "impresiones": total_impresiones,
                "interacciones": total_interacciones,
                "interacciones_por_tipo": interacciones_por_tipo,
                "impresiones_por_tipo_recomendacion": impresiones_por_tipo,
            },
        }
