"""
Bahoy - Modelo Event (Eventos culturales)
Modelo principal que representa los eventos culturales de Buenos Aires.
Incluye soporte para búsqueda vectorial mediante pgvector.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

# Dimensión del vector de embedding (384 para all-MiniLM-L6-v2 u otros modelos ligeros)
EMBEDDING_DIMENSION = 384


class Event(Base, UUIDMixin, TimestampMixin):
    """
    Modelo principal para eventos culturales.
    Cada registro representa un evento (obra de teatro, concierto, exposición, etc.)
    con toda su información asociada y un embedding vectorial para recomendaciones.
    """

    __tablename__ = "events"

    # Nombre/título del evento (ej: "Hamlet - Teatro San Martín")
    titulo: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Descripción completa del evento con detalles, sinopsis, etc.
    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # FK a la categoría principal del evento (ej: "Teatro", "Música")
    categoria_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )

    # Lista de subcategorías como texto libre (ej: ["drama", "clásico"])
    subcategorias: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Fecha y hora de inicio del evento
    fecha_inicio: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Fecha y hora de fin del evento (NULL si es un evento puntual)
    fecha_fin: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # FK al lugar donde se realiza el evento
    venue_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("venues.id"),
        nullable=True,
    )

    # Precio mínimo de entrada (0 si es gratuito)
    precio_min: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    # Precio máximo de entrada
    precio_max: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    # Indica si el evento es gratuito
    es_gratuito: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # URL original del evento en la fuente (para referencia y deduplicación)
    url_fuente: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # URL de la imagen principal del evento
    imagen_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Etiquetas descriptivas del evento (ej: ["familiar", "al aire libre", "accesible"])
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Vector de embedding de 384 dimensiones para búsqueda semántica y recomendaciones.
    # Se genera a partir del título + descripción usando un modelo de sentence-transformers.
    embedding = mapped_column(
        Vector(EMBEDDING_DIMENSION),
        nullable=True,
    )

    # FK a la fuente de donde se obtuvo el evento (scraper)
    source_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=True,
    )

    # Hash único del evento en la fuente original para detectar duplicados.
    # Se calcula a partir de título + fecha + venue para evitar importar el mismo evento dos veces.
    source_hash: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
    )

    # -- Relaciones --
    # Categoría principal del evento
    categoria = relationship("Category", back_populates="eventos")

    # Lugar donde se realiza el evento
    venue = relationship("Venue", back_populates="eventos")

    # Fuente de la que se obtuvo el evento
    source = relationship("Source", back_populates="eventos")

    # Interacciones de usuarios con este evento
    interacciones = relationship("Interaction", back_populates="event")

    __table_args__ = (
        # Índice para buscar eventos por fecha de inicio (consultas de agenda)
        Index("ix_events_fecha_inicio", "fecha_inicio"),
        # Índice para filtrar por categoría
        Index("ix_events_categoria_id", "categoria_id"),
        # Índice para filtrar por lugar
        Index("ix_events_venue_id", "venue_id"),
        # Índice para filtrar eventos gratuitos
        Index("ix_events_es_gratuito", "es_gratuito"),
        # Índice para buscar por fuente
        Index("ix_events_source_id", "source_id"),
        # Índice único para evitar duplicados por hash de la fuente
        Index("ix_events_source_hash", "source_hash", unique=True),
        # Índice para búsquedas por rango de fechas (inicio y fin)
        Index("ix_events_fecha_rango", "fecha_inicio", "fecha_fin"),
        # Índice GIN para búsquedas en el array de tags
        Index("ix_events_tags", "tags", postgresql_using="gin"),
        # Índice vectorial HNSW para búsqueda de vecinos cercanos en el embedding.
        # Usa distancia coseno para comparar similitud semántica entre eventos.
        Index(
            "ix_events_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, titulo='{self.titulo[:50]}...')>"
