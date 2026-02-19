"""
Bahoy - Modelo RecommendationImpression (Impresiones de recomendaciones)
Registra cada vez que se muestran recomendaciones a un usuario,
permitiendo calcular métricas como CTR, diversidad y cobertura.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class RecommendationImpression(Base, UUIDMixin):
    """
    Registro de una sesión de recomendación mostrada al usuario.
    Cada registro representa una lista de eventos recomendados presentada al usuario
    en un momento dado, junto con el tipo de algoritmo que los generó.
    """

    __tablename__ = "recommendation_impressions"

    # FK al usuario que recibió las recomendaciones
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Lista de IDs de eventos recomendados (guardados como strings de UUID)
    # Estructura: ["uuid1", "uuid2", ...]
    event_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # Tipo de algoritmo de recomendación usado
    # Valores: "personalizadas", "populares", "similares", "contenido", "hibrido"
    tipo_recomendacion: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Momento en que se mostraron las recomendaciones
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # -- Relaciones --
    user = relationship("User")

    __table_args__ = (
        # Índice para consultar impresiones por usuario
        Index("ix_impressions_user_id", "user_id"),
        # Índice para consultas temporales (filtrar por período)
        Index("ix_impressions_timestamp", "timestamp"),
        # Índice para filtrar por tipo de recomendación
        Index("ix_impressions_tipo", "tipo_recomendacion"),
    )

    def __repr__(self) -> str:
        return (
            f"<RecommendationImpression("
            f"id={self.id}, user_id={self.user_id}, "
            f"events={len(self.event_ids)}, tipo='{self.tipo_recomendacion}')>"
        )
