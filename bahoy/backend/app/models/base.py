"""
Bahoy - Base para modelos SQLAlchemy
Define la clase base declarativa y mixins comunes para todos los modelos.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos de Bahoy."""
    pass


class TimestampMixin:
    """
    Mixin que agrega campos de auditoría created_at y updated_at.
    Se hereda en los modelos que necesitan rastrear cuándo fueron creados/modificados.
    """

    # Fecha de creación del registro
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Fecha de última actualización del registro
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UUIDMixin:
    """
    Mixin que agrega un campo id de tipo UUID como clave primaria.
    Usa uuid4 para generar identificadores únicos universales.
    """

    # Identificador único universal generado automáticamente
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
