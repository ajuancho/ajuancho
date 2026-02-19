"""
Bahoy - Modelo Interaction (Interacciones usuario-evento)
Registra cada interacción de un usuario con un evento para alimentar
el sistema de recomendaciones.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ENUM, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class InteractionType(str, enum.Enum):
    """Tipos de interacción posibles entre usuario y evento."""
    VISTA = "vista"              # El usuario vio el detalle del evento
    CLIC = "clic"                # El usuario hizo clic en el evento desde un listado
    GUARDADO = "guardado"        # El usuario guardó el evento como favorito
    COMPARTIDO = "compartido"    # El usuario compartió el evento
    ASISTIO = "asistio"          # El usuario marcó que asistió al evento


class Interaction(Base, UUIDMixin):
    """
    Modelo para registrar interacciones de usuarios con eventos.
    Cada registro representa una acción específica (vista, clic, guardado, etc.)
    que se usa para calcular recomendaciones personalizadas.
    """

    __tablename__ = "interactions"

    # FK al usuario que realizó la interacción
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # FK al evento con el que interactuó el usuario
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False,
    )

    # Tipo de interacción realizada
    tipo: Mapped[InteractionType] = mapped_column(
        ENUM(InteractionType, name="interaction_type", create_type=True),
        nullable=False,
    )

    # Momento exacto en que ocurrió la interacción
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Contexto adicional de la interacción en formato JSON.
    # Estructura esperada:
    # {
    #     "dispositivo": "mobile",
    #     "ubicacion": "Palermo",
    #     "referrer": "busqueda",
    #     "session_id": "abc123"
    # }
    contexto: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # -- Relaciones --
    # Usuario que realizó la interacción
    user = relationship("User", back_populates="interacciones")

    # Evento con el que se interactuó
    event = relationship("Event", back_populates="interacciones")

    __table_args__ = (
        # Índice para obtener todas las interacciones de un usuario
        Index("ix_interactions_user_id", "user_id"),
        # Índice para obtener todas las interacciones sobre un evento
        Index("ix_interactions_event_id", "event_id"),
        # Índice para filtrar por tipo de interacción
        Index("ix_interactions_tipo", "tipo"),
        # Índice para consultas temporales (ej: interacciones de la última semana)
        Index("ix_interactions_timestamp", "timestamp"),
        # Índice compuesto para consultas frecuentes: "¿qué hizo este usuario con este evento?"
        Index("ix_interactions_user_event", "user_id", "event_id"),
    )

    def __repr__(self) -> str:
        return f"<Interaction(id={self.id}, user_id={self.user_id}, event_id={self.event_id}, tipo='{self.tipo}')>"
