"""
Bahoy Backend - Tests de modelos SQLAlchemy.

Verifica:
  - Creación de instancias con todos los campos
  - Campos requeridos y valores por defecto
  - Relaciones entre modelos (evento-venue, evento-categoría)
  - Campo vector (embedding de 384 dimensiones)
  - Tipos de datos (enums, arrays, Decimal)

Nota: estos tests operan sobre objetos Python en memoria, sin conectar
a la base de datos. Las restricciones de NOT NULL y UNIQUE se verifican
al insertar en PostgreSQL; aquí probamos el comportamiento del ORM.

Ejecutar:
    docker-compose exec backend pytest tests/test_models.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import numpy as np
import pytest

from app.models.base import TimestampMixin, UUIDMixin
from app.models.category import Category
from app.models.event import EMBEDDING_DIMENSION, Event
from app.models.interaction import Interaction, InteractionType
from app.models.user import User
from app.models.venue import Venue, VenueType


# ─────────────────────────────────────────────────────────────────────────────
# Helpers locales
# ─────────────────────────────────────────────────────────────────────────────


def _make_embedding(seed: int = 0) -> list[float]:
    rng = np.random.default_rng(seed)
    v = rng.random(EMBEDDING_DIMENSION).astype(float)
    return (v / np.linalg.norm(v)).tolist()


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Modelo Event
# ─────────────────────────────────────────────────────────────────────────────


class TestEventModel:
    """Tests del modelo principal Event."""

    def test_crear_evento_campos_completos(self, sample_event):
        """Instanciar un Event con todos los campos asignados."""
        assert sample_event.titulo == "Hamlet - Teatro Cervantes"
        assert sample_event.descripcion is not None
        assert sample_event.precio_min == Decimal("3000.00")
        assert sample_event.precio_max == Decimal("6000.00")
        assert sample_event.es_gratuito is False
        assert sample_event.imagen_url is not None
        assert sample_event.url_fuente is not None
        assert sample_event.source_hash == "abc123def456"

    def test_campo_titulo(self):
        """El campo titulo acepta hasta 500 caracteres."""
        event = Event()
        event.titulo = "T" * 500
        assert len(event.titulo) == 500

    def test_campo_descripcion_opcional(self):
        """La descripción puede ser None."""
        event = Event()
        event.titulo = "Evento mínimo"
        event.descripcion = None
        assert event.descripcion is None

    def test_evento_gratuito(self):
        """Es_gratuito puede ser True con precio_min en cero."""
        event = Event()
        event.titulo = "Festival Gratuito"
        event.es_gratuito = True
        event.precio_min = Decimal("0.00")
        assert event.es_gratuito is True
        assert event.precio_min == Decimal("0.00")

    def test_evento_con_precio(self):
        """Precio puede ser Decimal con dos decimales."""
        event = Event()
        event.titulo = "Concierto"
        event.precio_min = Decimal("1500.50")
        event.precio_max = Decimal("4000.00")
        assert float(event.precio_min) == pytest.approx(1500.50)
        assert float(event.precio_max) == pytest.approx(4000.00)

    def test_relacion_evento_categoria(self, sample_event, sample_category):
        """La relación Event → Category funciona correctamente."""
        assert sample_event.categoria is sample_category
        assert sample_event.categoria_id == sample_category.id
        assert sample_event.categoria.nombre == "Teatro"

    def test_relacion_evento_venue(self, sample_event, sample_venue):
        """La relación Event → Venue funciona correctamente."""
        assert sample_event.venue is sample_venue
        assert sample_event.venue_id == sample_venue.id
        assert sample_event.venue.nombre == "Teatro San Martín"

    def test_campo_embedding_dimension_correcta(self, sample_event):
        """El embedding debe tener exactamente EMBEDDING_DIMENSION (384) elementos."""
        assert sample_event.embedding is not None
        assert len(sample_event.embedding) == EMBEDDING_DIMENSION

    def test_campo_embedding_valores_flotantes(self, sample_event):
        """Todos los valores del embedding son floats."""
        assert all(isinstance(v, float) for v in sample_event.embedding)

    def test_campo_embedding_normalizado(self, sample_event):
        """El embedding generado por el fixture tiene norma ≈ 1."""
        norma = np.linalg.norm(sample_event.embedding)
        assert norma == pytest.approx(1.0, abs=1e-6)

    def test_campo_embedding_puede_ser_none(self):
        """El embedding es opcional (nullable)."""
        event = Event()
        event.titulo = "Sin embedding"
        event.embedding = None
        assert event.embedding is None

    def test_campo_embedding_dimension_constante(self):
        """La dimensión del embedding es 384."""
        assert EMBEDDING_DIMENSION == 384

    def test_tags_como_lista(self, sample_event):
        """Tags es una lista de strings."""
        assert isinstance(sample_event.tags, list)
        assert all(isinstance(t, str) for t in sample_event.tags)

    def test_tags_pueden_filtrarse(self, sample_event):
        """Los tags del fixture contienen valores conocidos."""
        assert "teatro" in sample_event.tags
        assert "drama" in sample_event.tags

    def test_subcategorias_como_lista(self, sample_event):
        """Subcategorias es una lista."""
        assert isinstance(sample_event.subcategorias, list)
        assert "Drama" in sample_event.subcategorias

    def test_tags_pueden_ser_none(self):
        """El campo tags puede ser None."""
        event = Event()
        event.titulo = "Sin tags"
        event.tags = None
        assert event.tags is None

    def test_fecha_inicio_con_timezone(self, sample_event):
        """La fecha de inicio tiene timezone."""
        assert sample_event.fecha_inicio.tzinfo is not None

    def test_fecha_fin_opcional(self, sample_event):
        """La fecha de fin puede ser None (evento puntual)."""
        assert sample_event.fecha_fin is None

    def test_source_hash_unico_por_evento(self):
        """Dos eventos pueden tener source_hash distintos."""
        e1 = Event()
        e1.titulo = "Evento 1"
        e1.source_hash = "hash_aaa"

        e2 = Event()
        e2.titulo = "Evento 2"
        e2.source_hash = "hash_bbb"

        assert e1.source_hash != e2.source_hash

    def test_repr_contiene_nombre_clase(self, sample_event):
        """__repr__ incluye 'Event'."""
        assert "Event" in repr(sample_event)

    def test_categoria_none_no_falla(self):
        """Un evento puede existir sin categoría asignada."""
        event = Event()
        event.titulo = "Evento sin categoría"
        event.categoria = None
        event.categoria_id = None
        assert event.categoria is None


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Modelo Venue
# ─────────────────────────────────────────────────────────────────────────────


class TestVenueModel:
    """Tests del modelo Venue (lugares)."""

    def test_crear_venue_completo(self, sample_venue):
        """Venue con todos los campos tiene los valores esperados."""
        assert sample_venue.nombre == "Teatro San Martín"
        assert sample_venue.direccion == "Corrientes 1530, CABA"
        assert sample_venue.barrio == "San Nicolás"
        assert sample_venue.capacidad == 800

    def test_venue_tipo_teatro(self, sample_venue):
        """El tipo del venue es el enum VenueType.TEATRO."""
        assert sample_venue.tipo == VenueType.TEATRO

    def test_venue_todos_los_tipos_enum(self):
        """Todos los tipos del enum VenueType son accesibles."""
        tipos = list(VenueType)
        assert VenueType.TEATRO in tipos
        assert VenueType.MUSEO in tipos
        assert VenueType.BAR in tipos
        assert VenueType.RESTAURANTE in tipos
        assert VenueType.CENTRO_CULTURAL in tipos
        assert VenueType.OTRO in tipos

    def test_venue_coordenadas_son_floats(self, sample_venue):
        """Latitud y longitud son floats."""
        assert isinstance(sample_venue.latitud, float)
        assert isinstance(sample_venue.longitud, float)

    def test_venue_coordenadas_buenos_aires(self, sample_venue):
        """Las coordenadas están dentro del rango esperado para CABA."""
        assert -35.0 < sample_venue.latitud < -34.0
        assert -59.0 < sample_venue.longitud < -58.0

    def test_venue_barrio_opcional(self):
        """El barrio puede ser None."""
        venue = Venue()
        venue.nombre = "Lugar sin barrio"
        venue.barrio = None
        assert venue.barrio is None

    def test_venue_repr_contiene_nombre(self, sample_venue):
        """__repr__ incluye 'Venue'."""
        assert "Venue" in repr(sample_venue)

    def test_venue_relacion_eventos(self, sample_venue, sample_event):
        """Venue referencia al evento a través de la relación."""
        assert sample_event.venue is sample_venue


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Modelo Category
# ─────────────────────────────────────────────────────────────────────────────


class TestCategoryModel:
    """Tests del modelo Category con jerarquía padre-hijo."""

    def test_crear_categoria_raiz(self, sample_category):
        """Categoría raíz tiene parent_id = None."""
        assert sample_category.nombre == "Teatro"
        assert sample_category.parent_id is None

    def test_jerarquia_padre_hijo(self, sample_category):
        """Subcategoría tiene parent_id apuntando a la categoría padre."""
        subcat = Category()
        subcat.id = uuid.uuid4()
        subcat.nombre = "Comedia"
        subcat.parent_id = sample_category.id

        assert subcat.parent_id == sample_category.id
        assert subcat.nombre == "Comedia"

    def test_multiples_subcategorias(self, sample_category):
        """Una categoría puede tener múltiples subcategorías."""
        nombres = ["Drama", "Comedia", "Musical", "Infantil"]
        subcats = []
        for nombre in nombres:
            sc = Category()
            sc.id = uuid.uuid4()
            sc.nombre = nombre
            sc.parent_id = sample_category.id
            subcats.append(sc)

        for sc in subcats:
            assert sc.parent_id == sample_category.id

    def test_icono_opcional(self, sample_category):
        """El icono es opcional (puede ser None)."""
        cat = Category()
        cat.id = uuid.uuid4()
        cat.nombre = "Sin icono"
        cat.icono = None
        assert cat.icono is None

    def test_categoria_repr(self, sample_category):
        """__repr__ incluye 'Category'."""
        assert "Category" in repr(sample_category)

    def test_diferentes_categorias_tienen_ids_distintos(
        self, sample_category, sample_category_musica
    ):
        """Dos categorías distintas tienen IDs únicos."""
        assert sample_category.id != sample_category_musica.id
        assert sample_category.nombre != sample_category_musica.nombre


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Modelo User
# ─────────────────────────────────────────────────────────────────────────────


class TestUserModel:
    """Tests del modelo User."""

    def test_crear_usuario_con_preferencias(self, sample_user):
        """Usuario con preferencias tiene estructura correcta."""
        assert sample_user.email == "test@bahoy.ar"
        assert sample_user.nombre == "Usuario Test"
        assert isinstance(sample_user.preferencias, dict)

    def test_preferencias_estructura_completa(self, sample_user):
        """Las preferencias contienen las claves esperadas."""
        prefs = sample_user.preferencias
        assert "categorias_favoritas" in prefs
        assert "barrios_preferidos" in prefs
        assert "rango_precios" in prefs
        assert "tags_interes" in prefs

    def test_preferencias_categorias_son_lista(self, sample_user):
        """Las categorías favoritas son una lista de strings."""
        cats = sample_user.preferencias["categorias_favoritas"]
        assert isinstance(cats, list)
        assert "teatro" in cats
        assert "música" in cats

    def test_preferencias_rango_precio(self, sample_user):
        """El rango de precios tiene min y max."""
        rango = sample_user.preferencias["rango_precios"]
        assert "min" in rango
        assert "max" in rango
        assert rango["min"] <= rango["max"]

    def test_usuario_nuevo_sin_preferencias(self, sample_user_nuevo):
        """Usuario nuevo tiene preferencias = None."""
        assert sample_user_nuevo.preferencias is None
        assert sample_user_nuevo.ubicacion_habitual is None

    def test_ubicacion_habitual(self, sample_user):
        """El campo ubicacion_habitual almacena el barrio del usuario."""
        assert sample_user.ubicacion_habitual == "Palermo"

    def test_user_repr(self, sample_user):
        """__repr__ incluye 'User'."""
        assert "User" in repr(sample_user)

    def test_diferentes_usuarios_tienen_emails_distintos(
        self, sample_user, sample_user_nuevo
    ):
        """Dos usuarios tienen emails distintos."""
        assert sample_user.email != sample_user_nuevo.email


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Modelo Interaction
# ─────────────────────────────────────────────────────────────────────────────


class TestInteractionModel:
    """Tests del modelo Interaction (usuario ↔ evento)."""

    def test_crear_interaccion_guardado(self, sample_interaction):
        """Interacción GUARDADO tiene los campos esperados."""
        assert sample_interaction.tipo == InteractionType.GUARDADO
        assert sample_interaction.contexto is not None

    def test_todos_los_tipos_de_interaccion(self):
        """El enum InteractionType tiene los 5 tipos definidos."""
        tipos = set(InteractionType)
        assert InteractionType.VISTA in tipos
        assert InteractionType.CLIC in tipos
        assert InteractionType.GUARDADO in tipos
        assert InteractionType.COMPARTIDO in tipos
        assert InteractionType.ASISTIO in tipos
        assert len(tipos) == 5

    def test_interaccion_vista(self, sample_user, sample_event):
        """Una interacción de tipo VISTA se puede crear."""
        inter = Interaction()
        inter.id = uuid.uuid4()
        inter.user_id = sample_user.id
        inter.event_id = sample_event.id
        inter.tipo = InteractionType.VISTA
        assert inter.tipo == InteractionType.VISTA

    def test_interaccion_clic(self, sample_user, sample_event):
        """Una interacción de tipo CLIC se puede crear."""
        inter = Interaction()
        inter.id = uuid.uuid4()
        inter.user_id = sample_user.id
        inter.event_id = sample_event.id
        inter.tipo = InteractionType.CLIC
        assert inter.tipo.value == "clic"

    def test_interaccion_referencia_usuario_correcto(
        self, sample_interaction, sample_user
    ):
        """La interacción apunta al usuario correcto."""
        assert sample_interaction.user_id == sample_user.id

    def test_interaccion_referencia_evento_correcto(
        self, sample_interaction, sample_event
    ):
        """La interacción apunta al evento correcto."""
        assert sample_interaction.event_id == sample_event.id

    def test_contexto_opcional(self, sample_user, sample_event):
        """El contexto puede ser None."""
        inter = Interaction()
        inter.id = uuid.uuid4()
        inter.user_id = sample_user.id
        inter.event_id = sample_event.id
        inter.tipo = InteractionType.VISTA
        inter.contexto = None
        assert inter.contexto is None

    def test_interaccion_repr(self, sample_interaction):
        """__repr__ incluye 'Interaction'."""
        assert "Interaction" in repr(sample_interaction)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: UUIDMixin y TimestampMixin
# ─────────────────────────────────────────────────────────────────────────────


class TestMixins:
    """Tests de los mixins base."""

    def test_uuidmixin_ids_son_uuid(self, sample_event, sample_venue, sample_user):
        """Los IDs generados son instancias de uuid.UUID."""
        assert isinstance(sample_event.id, uuid.UUID)
        assert isinstance(sample_venue.id, uuid.UUID)
        assert isinstance(sample_user.id, uuid.UUID)

    def test_uuidmixin_ids_son_unicos(self):
        """UUIDs generados en distintas instancias son únicos."""
        cat1 = Category()
        cat1.id = uuid.uuid4()
        cat2 = Category()
        cat2.id = uuid.uuid4()
        assert cat1.id != cat2.id

    def test_timestampmixin_created_at_soporta_datetime(self, sample_event):
        """Event (con TimestampMixin) soporta asignación de created_at."""
        ahora = datetime.now(timezone.utc)
        sample_event.created_at = ahora
        assert sample_event.created_at == ahora

    def test_timestampmixin_updated_at_soporta_datetime(self, sample_event):
        """Event soporta asignación de updated_at."""
        ahora = datetime.now(timezone.utc)
        sample_event.updated_at = ahora
        assert sample_event.updated_at == ahora
