"""
Bahoy Backend - Fixtures compartidos para pytest.

Este módulo provee fixtures reutilizables para todos los tests:
  - Modelos ORM con datos realistas de Buenos Aires
  - Mock de AsyncSession para evitar dependencia de base de datos
  - Helpers para crear embeddings deterministas

Ejecutar la suite completa:
    docker-compose exec backend pytest

O desde el host (con entorno activado):
    cd bahoy/backend
    pytest
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from app.models.category import Category
from app.models.event import EMBEDDING_DIMENSION, Event
from app.models.interaction import Interaction, InteractionType
from app.models.user import User
from app.models.venue import Venue, VenueType


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de construcción
# ─────────────────────────────────────────────────────────────────────────────


def make_uuid() -> uuid.UUID:
    """Genera un UUID4 aleatorio."""
    return uuid.uuid4()


def make_embedding(seed: int = 0, dim: int = EMBEDDING_DIMENSION) -> list[float]:
    """
    Genera un embedding normalizado de dimensión `dim`.
    Determinista gracias al seed.
    """
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype(float)
    return (v / np.linalg.norm(v)).tolist()


def make_db_result(rows: list[Any]) -> MagicMock:
    """
    Simula el objeto resultado de db.execute().

    Soporta:
      - result.all()               → rows
      - result.scalars().all()     → rows
      - result.scalar_one_or_none()→ rows[0] if rows else None
    """
    result = MagicMock()
    result.all.return_value = rows
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result.scalars.return_value = scalars_mock
    result.scalar_one_or_none.return_value = rows[0] if rows else None
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures de modelos ORM
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_category() -> Category:
    """Categoría 'Teatro' sin padre (categoría raíz)."""
    cat = Category()
    cat.id = make_uuid()
    cat.nombre = "Teatro"
    cat.icono = "theater_comedy"
    cat.parent_id = None
    cat.subcategorias = []
    cat.eventos = []
    return cat


@pytest.fixture
def sample_category_musica() -> Category:
    """Categoría 'Música' para tests multi-categoría."""
    cat = Category()
    cat.id = make_uuid()
    cat.nombre = "Música"
    cat.icono = "music_note"
    cat.parent_id = None
    cat.subcategorias = []
    cat.eventos = []
    return cat


@pytest.fixture
def sample_venue() -> Venue:
    """Venue 'Teatro San Martín' en San Nicolás."""
    venue = Venue()
    venue.id = make_uuid()
    venue.nombre = "Teatro San Martín"
    venue.direccion = "Corrientes 1530, CABA"
    venue.barrio = "San Nicolás"
    venue.latitud = -34.6037
    venue.longitud = -58.3816
    venue.tipo = VenueType.TEATRO
    venue.capacidad = 800
    venue.eventos = []
    return venue


@pytest.fixture
def sample_venue_palermo() -> Venue:
    """Venue en Palermo para tests de filtros por barrio."""
    venue = Venue()
    venue.id = make_uuid()
    venue.nombre = "Centro Cultural Konex"
    venue.direccion = "Sarmiento 3131, CABA"
    venue.barrio = "Palermo"
    venue.latitud = -34.5979
    venue.longitud = -58.4144
    venue.tipo = VenueType.CENTRO_CULTURAL
    venue.capacidad = 1500
    venue.eventos = []
    return venue


@pytest.fixture
def sample_event(sample_category, sample_venue) -> Event:
    """Evento 'Hamlet' con todos los campos completos."""
    event = Event()
    event.id = make_uuid()
    event.titulo = "Hamlet - Teatro Cervantes"
    event.descripcion = (
        "La obra teatral más famosa de Shakespeare con elenco de primer nivel. "
        "Función con actores y actrices de la escena argentina."
    )
    event.categoria_id = sample_category.id
    event.categoria = sample_category
    event.venue_id = sample_venue.id
    event.venue = sample_venue
    event.fecha_inicio = datetime.now(timezone.utc) + timedelta(days=7)
    event.fecha_fin = None
    event.precio_min = Decimal("3000.00")
    event.precio_max = Decimal("6000.00")
    event.es_gratuito = False
    event.tags = ["teatro", "drama", "nocturno"]
    event.subcategorias = ["Drama"]
    event.embedding = make_embedding(seed=42)
    event.imagen_url = "https://example.com/hamlet.jpg"
    event.url_fuente = "https://turismo.buenosaires.gob.ar/evento/hamlet-123"
    event.source_hash = "abc123def456"
    event.source_id = None
    event.interacciones = []
    return event


@pytest.fixture
def sample_event_gratuito(sample_category_musica, sample_venue_palermo) -> Event:
    """Evento gratuito de música al aire libre."""
    event = Event()
    event.id = make_uuid()
    event.titulo = "Concierto de Bandas en Parque Centenario"
    event.descripcion = "Show en el parque. Entrada libre y gratuita para toda la familia."
    event.categoria_id = sample_category_musica.id
    event.categoria = sample_category_musica
    event.venue_id = sample_venue_palermo.id
    event.venue = sample_venue_palermo
    event.fecha_inicio = datetime.now(timezone.utc) + timedelta(days=3)
    event.fecha_fin = None
    event.precio_min = Decimal("0.00")
    event.precio_max = Decimal("0.00")
    event.es_gratuito = True
    event.tags = ["gratuito", "familiar", "al aire libre"]
    event.subcategorias = ["Rock"]
    event.embedding = make_embedding(seed=7)
    event.imagen_url = None
    event.url_fuente = None
    event.source_hash = "free_concierto_001"
    event.source_id = None
    event.interacciones = []
    return event


@pytest.fixture
def sample_user() -> User:
    """Usuario con preferencias explícitas de teatro y música."""
    user = User()
    user.id = make_uuid()
    user.email = "test@bahoy.ar"
    user.nombre = "Usuario Test"
    user.ubicacion_habitual = "Palermo"
    user.preferencias = {
        "categorias_favoritas": ["teatro", "música"],
        "barrios_preferidos": ["Palermo", "San Telmo"],
        "rango_precios": {"min": 0, "max": 8000},
        "tags_interes": ["familiar"],
    }
    user.interacciones = []
    return user


@pytest.fixture
def sample_user_nuevo() -> User:
    """Usuario recién registrado, sin preferencias ni historial."""
    user = User()
    user.id = make_uuid()
    user.email = "nuevo@bahoy.ar"
    user.nombre = "Nuevo Usuario"
    user.preferencias = None
    user.ubicacion_habitual = None
    user.interacciones = []
    return user


@pytest.fixture
def sample_interaction(sample_user, sample_event) -> Interaction:
    """Interacción GUARDADO entre usuario y evento."""
    inter = Interaction()
    inter.id = make_uuid()
    inter.user_id = sample_user.id
    inter.event_id = sample_event.id
    inter.tipo = InteractionType.GUARDADO
    inter.timestamp = datetime.now(timezone.utc)
    inter.contexto = {"dispositivo": "mobile", "referrer": "busqueda"}
    inter.user = sample_user
    inter.event = sample_event
    return inter


# ─────────────────────────────────────────────────────────────────────────────
# Fixture de base de datos mock
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db() -> AsyncMock:
    """AsyncMock de AsyncSession. Configura .execute() en cada test."""
    return AsyncMock()
