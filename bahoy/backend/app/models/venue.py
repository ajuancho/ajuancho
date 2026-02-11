"""
Bahoy - Modelo Venue (Lugares)
Representa los espacios físicos donde se realizan los eventos culturales.
"""

import enum

from sqlalchemy import Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class VenueType(str, enum.Enum):
    """Tipos de lugar donde se realizan eventos."""
    TEATRO = "teatro"
    MUSEO = "museo"
    BAR = "bar"
    RESTAURANTE = "restaurante"
    CENTRO_CULTURAL = "centro_cultural"
    OTRO = "otro"


class Venue(Base, UUIDMixin, TimestampMixin):
    """
    Modelo para los lugares/espacios donde ocurren eventos.
    Almacena información geográfica y descriptiva de cada venue.
    """

    __tablename__ = "venues"

    # Nombre del lugar (ej: "Teatro Colón", "Centro Cultural Recoleta")
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Dirección completa del lugar (ej: "Cerrito 628, CABA")
    direccion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Coordenada de latitud para geolocalización
    latitud: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Coordenada de longitud para geolocalización
    longitud: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Barrio donde se ubica el lugar (ej: "Palermo", "San Telmo")
    barrio: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Tipo de establecimiento
    tipo: Mapped[VenueType | None] = mapped_column(
        ENUM(VenueType, name="venue_type", create_type=True),
        nullable=True,
    )

    # Capacidad máxima de personas (opcional)
    capacidad: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # -- Relaciones --
    # Eventos que se realizan en este lugar
    eventos = relationship("Event", back_populates="venue")

    __table_args__ = (
        # Índice para búsquedas por barrio (frecuente en filtros)
        Index("ix_venues_barrio", "barrio"),
        # Índice para búsquedas por nombre del lugar
        Index("ix_venues_nombre", "nombre"),
        # Índice para búsquedas geográficas por coordenadas
        Index("ix_venues_coordenadas", "latitud", "longitud"),
    )

    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, nombre='{self.nombre}', barrio='{self.barrio}')>"
