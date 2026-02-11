"""
Bahoy - Modelo Source (Fuentes de datos)
Representa las fuentes externas de donde se obtienen los eventos (scrapers).
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class SourceFrequency(str, enum.Enum):
    """Frecuencia con la que se ejecuta el scraper de la fuente."""
    DIARIA = "diaria"
    SEMANAL = "semanal"


class Source(Base, UUIDMixin, TimestampMixin):
    """
    Modelo para las fuentes de datos externas.
    Cada fuente representa un sitio web del que se extraen eventos.
    """

    __tablename__ = "sources"

    # Nombre identificador de la fuente (ej: "Agenda BA", "Alternativa Teatral")
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # URL base del sitio web fuente (ej: "https://turismo.buenosaires.gob.ar")
    url_base: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Frecuencia de ejecución del scraper
    frecuencia: Mapped[SourceFrequency | None] = mapped_column(
        ENUM(SourceFrequency, name="source_frequency", create_type=True),
        nullable=True,
    )

    # Indica si la fuente está activa y debe ser scrapeada
    activa: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Timestamp de la última vez que se ejecutó el scraper para esta fuente
    ultima_ejecucion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -- Relaciones --
    # Eventos obtenidos de esta fuente
    eventos = relationship("Event", back_populates="source")

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, nombre='{self.nombre}', activa={self.activa})>"
