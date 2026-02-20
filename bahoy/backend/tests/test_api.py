"""
Bahoy Backend - Tests de la API REST.

Cubre los endpoints principales usando FastAPI TestClient con la
dependencia `get_db` reemplazada por un AsyncMock, evitando cualquier
conexión real a PostgreSQL.

Endpoints testeados:
  GET  /api/events              → lista de eventos
  GET  /api/events?categoria=… → lista filtrada
  GET  /api/events/{id}         → detalle de evento
  POST /api/users/register      → crear usuario
  POST /api/users/preferences   → guardar preferencias
  GET  /api/recommendations/{user_id} → recomendaciones

Ejecutar:
    docker-compose exec backend pytest tests/test_api.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_db_result(rows: list[Any]) -> MagicMock:
    result = MagicMock()
    result.all.return_value = rows
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result.scalars.return_value = scalars_mock
    result.scalar_one_or_none.return_value = rows[0] if rows else None
    return result


def _make_orm_event(
    titulo: str = "Obra de teatro",
    es_gratuito: bool = False,
    precio_min: float | None = 2000.0,
    categoria_nombre: str = "Teatro",
    barrio: str = "San Nicolás",
    dias_futuro: int = 7,
) -> MagicMock:
    """Crea un mock de Event ORM que el TestClient puede serializar."""
    cat = MagicMock()
    cat.id = uuid.uuid4()
    cat.nombre = categoria_nombre

    venue = MagicMock()
    venue.id = uuid.uuid4()
    venue.nombre = "Teatro San Martín"
    venue.barrio = barrio
    venue.direccion = "Corrientes 1530"

    event = MagicMock()
    event.id = uuid.uuid4()
    event.titulo = titulo
    event.descripcion = "Descripción de prueba"
    event.categoria = cat
    event.categoria_id = cat.id
    event.subcategorias = []
    event.venue = venue
    event.venue_id = venue.id
    event.fecha_inicio = datetime.now(timezone.utc) + timedelta(days=dias_futuro)
    event.fecha_fin = None
    event.precio_min = Decimal(str(precio_min)) if precio_min is not None else None
    event.precio_max = None
    event.es_gratuito = es_gratuito
    event.imagen_url = None
    event.url_fuente = None
    event.tags = ["teatro"]
    return event


def _make_orm_user(
    email: str = "test@bahoy.ar",
    nombre: str = "Test",
    preferencias: dict | None = None,
) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.nombre = nombre
    user.preferencias = preferencias
    user.ubicacion_habitual = None
    return user


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: cliente con DB mockeada
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    """
    Retorna (TestClient, mock_db).

    Sobreescribe la dependencia `get_db` con un AsyncMock para que
    los tests no necesiten una base de datos real.
    Limpia los overrides al finalizar.
    """
    mock_db = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client, mock_db
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Tests: GET /api/events
# ─────────────────────────────────────────────────────────────────────────────


class TestGetEvents:
    """Tests para el endpoint de listado de eventos."""

    def test_lista_eventos_vacia(self, api_client):
        """Cuando no hay eventos en la DB, devuelve lista vacía."""
        client, mock_db = api_client
        mock_db.execute.return_value = _make_db_result([])

        resp = client.get("/api/events")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_lista_eventos_con_resultados(self, api_client):
        """Devuelve la lista de eventos en el formato esperado."""
        client, mock_db = api_client
        event = _make_orm_event("Hamlet")
        mock_db.execute.return_value = _make_db_result([event])

        resp = client.get("/api/events")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["titulo"] == "Hamlet"
        assert "id" in data[0]
        assert "es_gratuito" in data[0]
        assert "venue" in data[0]
        assert "categoria" in data[0]

    def test_lista_multiples_eventos(self, api_client):
        """Devuelve todos los eventos cuando hay varios."""
        client, mock_db = api_client
        eventos = [_make_orm_event(f"Evento {i}") for i in range(5)]
        mock_db.execute.return_value = _make_db_result(eventos)

        resp = client.get("/api/events")

        assert resp.status_code == 200
        assert len(resp.json()) == 5

    def test_filtro_gratis_true(self, api_client):
        """Filtro gratis=true devuelve solo eventos gratuitos."""
        client, mock_db = api_client
        evento_gratis = _make_orm_event("Festival Gratis", es_gratuito=True)
        mock_db.execute.return_value = _make_db_result([evento_gratis])

        resp = client.get("/api/events?gratis=true")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["es_gratuito"] is True

    def test_filtro_gratis_false(self, api_client):
        """Filtro gratis=false devuelve solo eventos de pago."""
        client, mock_db = api_client
        evento_pago = _make_orm_event("Obra de pago", es_gratuito=False, precio_min=3000)
        mock_db.execute.return_value = _make_db_result([evento_pago])

        resp = client.get("/api/events?gratis=false")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["es_gratuito"] is False

    def test_filtro_categoria(self, api_client):
        """Filtro por categoría pasa correctamente a la query."""
        client, mock_db = api_client
        mock_db.execute.return_value = _make_db_result([])

        resp = client.get("/api/events?categoria=teatro")

        assert resp.status_code == 200
        assert mock_db.execute.called

    def test_filtro_barrio(self, api_client):
        """Filtro por barrio pasa correctamente a la query."""
        client, mock_db = api_client
        evento = _make_orm_event(barrio="Palermo")
        mock_db.execute.return_value = _make_db_result([evento])

        resp = client.get("/api/events?barrio=Palermo")

        assert resp.status_code == 200

    def test_paginacion_page_y_per_page(self, api_client):
        """Los parámetros page y per_page son aceptados."""
        client, mock_db = api_client
        mock_db.execute.return_value = _make_db_result([])

        resp = client.get("/api/events?page=2&per_page=10")

        assert resp.status_code == 200

    def test_per_page_invalido_rechazado(self, api_client):
        """per_page > 100 es rechazado (ge=1, le=100)."""
        client, mock_db = api_client

        resp = client.get("/api/events?per_page=200")

        assert resp.status_code == 422

    def test_page_invalida_rechazada(self, api_client):
        """page=0 es rechazado (ge=1)."""
        client, mock_db = api_client

        resp = client.get("/api/events?page=0")

        assert resp.status_code == 422

    def test_estructura_evento_en_respuesta(self, api_client):
        """Cada evento en la respuesta tiene los campos requeridos."""
        client, mock_db = api_client
        event = _make_orm_event()
        mock_db.execute.return_value = _make_db_result([event])

        resp = client.get("/api/events")
        data = resp.json()[0]

        campos_requeridos = {
            "id", "titulo", "descripcion", "categoria", "subcategorias",
            "fecha_inicio", "fecha_fin", "venue", "precio_min", "precio_max",
            "es_gratuito", "imagen_url", "url_fuente", "tags",
        }
        for campo in campos_requeridos:
            assert campo in data, f"Campo '{campo}' ausente en la respuesta"

    def test_venue_anidado_en_respuesta(self, api_client):
        """El venue en la respuesta tiene id, nombre, barrio, direccion."""
        client, mock_db = api_client
        event = _make_orm_event()
        mock_db.execute.return_value = _make_db_result([event])

        resp = client.get("/api/events")
        venue = resp.json()[0]["venue"]

        assert "id" in venue
        assert "nombre" in venue
        assert "barrio" in venue
        assert "direccion" in venue

    def test_evento_sin_venue_retorna_null(self, api_client):
        """Un evento sin venue devuelve venue=null en la respuesta."""
        client, mock_db = api_client
        event = _make_orm_event()
        event.venue = None
        mock_db.execute.return_value = _make_db_result([event])

        resp = client.get("/api/events")

        assert resp.json()[0]["venue"] is None


# ─────────────────────────────────────────────────────────────────────────────
# Tests: GET /api/events/{id}
# ─────────────────────────────────────────────────────────────────────────────


class TestGetEventById:
    """Tests para el endpoint de detalle de evento."""

    def test_obtener_evento_existente(self, api_client):
        """Devuelve el evento con status 200."""
        client, mock_db = api_client
        event = _make_orm_event("Hamlet")
        mock_db.execute.return_value = _make_db_result([event])

        resp = client.get(f"/api/events/{event.id}")

        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Hamlet"

    def test_evento_inexistente_retorna_404(self, api_client):
        """Evento no encontrado devuelve 404."""
        client, mock_db = api_client
        mock_db.execute.return_value = _make_db_result([])

        resp = client.get(f"/api/events/{uuid.uuid4()}")

        assert resp.status_code == 404
        assert "no encontrado" in resp.json()["detail"].lower()

    def test_id_invalido_retorna_422(self, api_client):
        """Un ID que no es UUID válido devuelve 422."""
        client, mock_db = api_client

        resp = client.get("/api/events/no-es-un-uuid-valido")

        assert resp.status_code == 422

    def test_estructura_detalle_evento(self, api_client):
        """La respuesta de detalle tiene todos los campos."""
        client, mock_db = api_client
        event = _make_orm_event("Obra completa", precio_min=2500.0)
        mock_db.execute.return_value = _make_db_result([event])

        resp = client.get(f"/api/events/{event.id}")
        data = resp.json()

        assert data["titulo"] == "Obra completa"
        assert data["precio_min"] == pytest.approx(2500.0)
        assert "venue" in data
        assert "categoria" in data


# ─────────────────────────────────────────────────────────────────────────────
# Tests: POST /api/users/register
# ─────────────────────────────────────────────────────────────────────────────


class TestPostUsersRegister:
    """Tests para el endpoint de registro de usuarios."""

    def test_registro_exitoso(self, api_client):
        """Registro con email y nombre válidos devuelve 201."""
        client, mock_db = api_client
        user = _make_orm_user(email="nuevo@bahoy.ar", nombre="Juan")
        # Primera query: verificar duplicado (no existe) → None
        # Segunda query: refresh del usuario creado → user
        mock_db.execute.side_effect = [
            _make_db_result([]),   # no existe usuario con ese email
        ]
        mock_db.refresh.return_value = None
        mock_db.refresh.side_effect = _set_user_on_refresh(user)

        resp = client.post(
            "/api/users/register",
            json={"email": "nuevo@bahoy.ar", "nombre": "Juan"},
        )

        assert resp.status_code == 201

    def test_registro_email_duplicado_retorna_409(self, api_client):
        """Email ya registrado devuelve 409 Conflict."""
        client, mock_db = api_client
        usuario_existente = _make_orm_user()
        mock_db.execute.return_value = _make_db_result([usuario_existente])

        resp = client.post(
            "/api/users/register",
            json={"email": "test@bahoy.ar", "nombre": "Otro"},
        )

        assert resp.status_code == 409

    def test_registro_email_invalido_retorna_422(self, api_client):
        """Email con formato inválido devuelve 422."""
        client, mock_db = api_client

        resp = client.post(
            "/api/users/register",
            json={"email": "no-es-un-email", "nombre": "Test"},
        )

        assert resp.status_code == 422

    def test_registro_sin_nombre_retorna_422(self, api_client):
        """Falta el campo nombre → 422."""
        client, mock_db = api_client

        resp = client.post(
            "/api/users/register",
            json={"email": "test@bahoy.ar"},
        )

        assert resp.status_code == 422

    def test_registro_con_preferencias_opcionales(self, api_client):
        """El campo preferencias es opcional en el registro."""
        client, mock_db = api_client
        user = _make_orm_user(
            email="prefs@bahoy.ar",
            preferencias={"categorias_favoritas": ["teatro"]},
        )
        mock_db.execute.return_value = _make_db_result([])
        mock_db.refresh.side_effect = _set_user_on_refresh(user)

        resp = client.post(
            "/api/users/register",
            json={
                "email": "prefs@bahoy.ar",
                "nombre": "Con Prefs",
                "preferencias": {"categorias_favoritas": ["teatro"]},
            },
        )

        assert resp.status_code == 201


def _set_user_on_refresh(user: MagicMock):
    """
    Side-effect que simula db.refresh() poblando los atributos del
    objeto pasado con los del mock de usuario.
    """
    import asyncio

    async def _refresh(obj):
        obj.id = user.id
        obj.email = user.email
        obj.nombre = user.nombre
        obj.preferencias = user.preferencias
        obj.ubicacion_habitual = user.ubicacion_habitual

    return _refresh


# ─────────────────────────────────────────────────────────────────────────────
# Tests: POST /api/users/preferences
# ─────────────────────────────────────────────────────────────────────────────


class TestPostUsersPreferences:
    """Tests para el endpoint de preferencias."""

    def test_guardar_preferencias_exitoso(self, api_client):
        """Usuario existente puede actualizar preferencias."""
        client, mock_db = api_client
        user_id = uuid.uuid4()
        user = _make_orm_user()
        user.id = user_id
        user.preferencias = {}
        mock_db.execute.return_value = _make_db_result([user])
        mock_db.refresh.side_effect = _noop_refresh

        resp = client.post(
            "/api/users/preferences",
            json={
                "user_id": str(user_id),
                "categorias_favoritas": ["música", "cine"],
                "barrios_preferidos": ["Palermo"],
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert "preferencias" in data

    def test_preferencias_usuario_inexistente_404(self, api_client):
        """Usuario no encontrado devuelve 404."""
        client, mock_db = api_client
        mock_db.execute.return_value = _make_db_result([])

        resp = client.post(
            "/api/users/preferences",
            json={"user_id": str(uuid.uuid4())},
        )

        assert resp.status_code == 404

    def test_preferencias_user_id_invalido_422(self, api_client):
        """user_id inválido devuelve 422."""
        client, mock_db = api_client

        resp = client.post(
            "/api/users/preferences",
            json={"user_id": "no-es-uuid"},
        )

        assert resp.status_code == 422


async def _noop_refresh(obj):
    """Side-effect de refresh que no hace nada."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Tests: GET /api/recommendations/{user_id}
# ─────────────────────────────────────────────────────────────────────────────


class TestGetRecommendations:
    """Tests para el endpoint de recomendaciones."""

    def _make_recommendation(self, titulo: str = "Evento recomendado") -> dict:
        return {
            "event": {
                "id": str(uuid.uuid4()),
                "titulo": titulo,
                "descripcion": None,
                "categoria": "Teatro",
                "subcategorias": [],
                "fecha_inicio": None,
                "fecha_fin": None,
                "venue": None,
                "precio_min": None,
                "precio_max": None,
                "es_gratuito": False,
                "imagen_url": None,
                "url_fuente": None,
                "tags": [],
            },
            "razon": "Porque te gustan: eventos de Teatro",
        }

    def test_recomendaciones_tipo_populares(self, api_client):
        """tipo=populares devuelve lista de recomendaciones."""
        client, mock_db = api_client
        # recomendar_populares hace 2 queries: interacciones + eventos
        mock_db.execute.side_effect = [
            _make_db_result([]),   # interacciones (vacío → completa con futuros)
            _make_db_result([_make_orm_event("Popular")]),  # eventos futuros
        ]

        resp = client.get(
            f"/api/recommendations/{uuid.uuid4()}?tipo=populares"
        )

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_recomendaciones_user_id_invalido_422(self, api_client):
        """user_id no UUID devuelve 422."""
        client, mock_db = api_client

        resp = client.get("/api/recommendations/no-es-uuid?tipo=populares")

        assert resp.status_code == 422

    def test_recomendaciones_tipo_invalido_422(self, api_client):
        """tipo no válido devuelve 422."""
        client, mock_db = api_client

        resp = client.get(
            f"/api/recommendations/{uuid.uuid4()}?tipo=invalido"
        )

        assert resp.status_code == 422

    def test_recomendaciones_similares_sin_event_id_retorna_422(self, api_client):
        """tipo=similares sin event_id devuelve 422."""
        client, mock_db = api_client

        resp = client.get(
            f"/api/recommendations/{uuid.uuid4()}?tipo=similares"
        )

        assert resp.status_code == 422

    def test_recomendaciones_contexto_buscar(self, api_client):
        """Endpoint de contexto sin parámetros devuelve lista."""
        client, mock_db = api_client
        mock_db.execute.return_value = _make_db_result([])

        resp = client.get("/api/recommendations/contexto/buscar")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_recomendaciones_contexto_con_query_gratis(self, api_client):
        """Contexto con query='gratis' filtra eventos gratuitos."""
        client, mock_db = api_client
        evento = _make_orm_event("Concierto Gratis", es_gratuito=True)
        mock_db.execute.return_value = _make_db_result([evento])

        resp = client.get("/api/recommendations/contexto/buscar?query=gratis")

        assert resp.status_code == 200

    def test_recomendaciones_limite_valido(self, api_client):
        """El parámetro limite acepta valores entre 1 y 50."""
        client, mock_db = api_client
        mock_db.execute.side_effect = [
            _make_db_result([]),
            _make_db_result([]),
        ]

        resp = client.get(
            f"/api/recommendations/{uuid.uuid4()}?tipo=populares&limite=5"
        )

        assert resp.status_code == 200

    def test_recomendaciones_limite_invalido_422(self, api_client):
        """limite=0 es rechazado."""
        client, mock_db = api_client

        resp = client.get(
            f"/api/recommendations/{uuid.uuid4()}?tipo=populares&limite=0"
        )

        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Endpoint raíz y health
# ─────────────────────────────────────────────────────────────────────────────


class TestRootEndpoints:
    """Tests básicos del endpoint raíz."""

    def test_root_devuelve_bienvenida(self, api_client):
        """GET / devuelve mensaje de bienvenida y status online."""
        client, _ = api_client

        resp = client.get("/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "Bahoy" in data["message"]
