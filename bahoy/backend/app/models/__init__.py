"""
Bahoy - Modelos de datos
Este paquete contiene los modelos de SQLAlchemy para la base de datos.

Importar todos los modelos aquí asegura que SQLAlchemy los registre
correctamente al momento de crear las tablas o ejecutar migraciones con Alembic.
"""

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.category import Category
from app.models.event import Event
from app.models.impression import RecommendationImpression
from app.models.interaction import Interaction, InteractionType
from app.models.source import Source, SourceFrequency
from app.models.user import User
from app.models.venue import Venue, VenueType

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "Event",
    "User",
    "Interaction",
    "InteractionType",
    "RecommendationImpression",
    "Venue",
    "VenueType",
    "Category",
    "Source",
    "SourceFrequency",
]
