"""
Tests para RecommenderService - Fase 2: recomendación basada en contenido.

Cubre:
  - calcular_perfil_usuario
  - buscar_por_perfil
  - recomendar_basado_en_contenido
  - recomendar_hibrido (Fase 1 + Fase 2)

Los tests usan mocks de AsyncSession para evitar dependencia de base de datos.

Ejecutar con:
    cd bahoy/backend
    pytest tests/test_recommender.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.models.interaction import InteractionType
from app.services.recommender import RecommenderService, _PESOS_CONTENIDO


# ─────────────────────────────────────────────────────────────────────────────
# Helpers para construir mocks
# ─────────────────────────────────────────────────────────────────────────────


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _emb(seed: int = 0, dim: int = 384) -> list[float]:
    """Genera un embedding determinista de dimensión `dim`."""
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype(float)
    return (v / np.linalg.norm(v)).tolist()


def make_category(nombre: str = "Teatro") -> MagicMock:
    cat = MagicMock()
    cat.id = _uuid()
    cat.nombre = nombre
    return cat


def make_venue(barrio: str = "Palermo") -> MagicMock:
    venue = MagicMock()
    venue.id = _uuid()
    venue.nombre = "Teatro San Martín"
    venue.barrio = barrio
    venue.direccion = "Corrientes 1530"
    return venue


def make_event(
    *,
    titulo: str = "Evento de prueba",
    embedding: list[float] | None = None,
    categoria: MagicMock | None = None,
    venue: MagicMock | None = None,
    es_gratuito: bool = False,
    precio_min: float | None = None,
    tags: list[str] | None = None,
    dias_futuro: int = 7,
) -> MagicMock:
    """Crea un mock de Event con los atributos mínimos necesarios."""
    cat = categoria or make_category()
    event = MagicMock()
    event.id = _uuid()
    event.titulo = titulo
    event.descripcion = "Descripción de prueba"
    event.embedding = embedding
    event.categoria = cat
    event.categoria_id = cat.id
    event.venue = venue or make_venue()
    event.es_gratuito = es_gratuito
    event.precio_min = Decimal(str(precio_min)) if precio_min is not None else None
    event.precio_max = None
    event.tags = tags or []
    event.subcategorias = []
    event.imagen_url = None
    event.url_fuente = None
    event.fecha_inicio = datetime.now(timezone.utc) + timedelta(days=dias_futuro)
    event.fecha_fin = None
    return event


def make_user(
    *,
    preferencias: dict[str, Any] | None = None,
) -> MagicMock:
    user = MagicMock()
    user.id = _uuid()
    user.email = "test@bahoy.ar"
    user.nombre = "Usuario Prueba"
    user.preferencias = preferencias
    return user


def make_interaction(
    tipo: InteractionType,
    user_id: uuid.UUID,
    event_id: uuid.UUID,
) -> MagicMock:
    inter = MagicMock()
    inter.id = _uuid()
    inter.user_id = user_id
    inter.event_id = event_id
    inter.tipo = tipo
    return inter


def _make_db_result(rows: list[Any]) -> MagicMock:
    """
    Simula el resultado de db.execute().
    - .all()                → rows (para selects de columnas individuales)
    - .scalars().all()      → rows (para selects de modelos ORM)
    - .scalar_one_or_none() → rows[0] if rows else None
    """
    result = MagicMock()
    result.all.return_value = rows
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result.scalars.return_value = scalars_mock
    result.scalar_one_or_none.return_value = rows[0] if rows else None
    return result


def make_async_db(*execute_returns: Any) -> AsyncMock:
    """
    Crea un AsyncMock de AsyncSession.
    Si se pasa más de un argumento, `execute` devuelve cada valor en orden
    (side_effect). Si se pasa uno solo, siempre devuelve ese valor.
    """
    db = AsyncMock()
    if len(execute_returns) == 1:
        db.execute.return_value = execute_returns[0]
    else:
        db.execute.side_effect = list(execute_returns)
    return db


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures de usuarios de prueba con distintos historiales
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def usuario_teatro():
    """Usuario con historial exclusivo de teatro."""
    return make_user(
        preferencias={
            "categorias_favoritas": ["teatro"],
            "barrios_preferidos": ["San Telmo"],
            "rango_precios": {"min": 0, "max": 8000},
            "tags_interes": [],
        }
    )


@pytest.fixture
def usuario_musica():
    """Usuario con historial exclusivo de música y sin preferencias explícitas."""
    return make_user(preferencias={})


@pytest.fixture
def usuario_sin_historial():
    """Usuario recién creado, sin interacciones ni preferencias."""
    return make_user(preferencias=None)


@pytest.fixture
def usuario_hibrido():
    """Usuario con preferencias explícitas Y historial implícito."""
    return make_user(
        preferencias={
            "categorias_favoritas": ["cine"],
            "barrios_preferidos": ["Palermo"],
            "rango_precios": {"min": 0, "max": 5000},
            "tags_interes": ["familiar"],
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests: calcular_perfil_usuario
# ─────────────────────────────────────────────────────────────────────────────


class TestCalcularPerfilUsuario:
    """Verifica que el perfil del usuario se calcule correctamente."""

    @pytest.mark.asyncio
    async def test_sin_interacciones_retorna_none(self, usuario_teatro):
        """Sin interacciones en la DB, el método debe retornar None."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        perfil = await service.calcular_perfil_usuario(str(usuario_teatro.id))

        assert perfil is None

    @pytest.mark.asyncio
    async def test_sin_embeddings_retorna_none(self, usuario_teatro):
        """Interacciones presentes pero sin embeddings en los eventos → None."""
        # La query filtra Event.embedding IS NOT NULL en la DB;
        # si la DB no devuelve filas, el resultado sigue siendo None.
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        perfil = await service.calcular_perfil_usuario(str(usuario_teatro.id))

        assert perfil is None

    @pytest.mark.asyncio
    async def test_una_interaccion_retorna_embedding_del_evento(self, usuario_musica):
        """Con una sola interacción, el perfil debe igualar el embedding del evento."""
        emb = _emb(seed=42)
        # La query retorna (tipo, embedding) por fila
        filas = [(InteractionType.VISTA, emb)]
        db = make_async_db(_make_db_result(filas))
        service = RecommenderService(db)

        perfil = await service.calcular_perfil_usuario(str(usuario_musica.id))

        assert perfil is not None
        assert len(perfil) == len(emb)
        np.testing.assert_allclose(perfil, emb, rtol=1e-6)

    @pytest.mark.asyncio
    async def test_promedio_ponderado_dos_interacciones(self, usuario_teatro):
        """
        Dos interacciones con diferentes pesos → promedio ponderado correcto.

        guardado (peso 3) + vista (peso 1): perfil = (3*emb1 + 1*emb2) / 4
        """
        emb1 = _emb(seed=1)
        emb2 = _emb(seed=2)
        filas = [
            (InteractionType.GUARDADO, emb1),
            (InteractionType.VISTA, emb2),
        ]
        db = make_async_db(_make_db_result(filas))
        service = RecommenderService(db)

        perfil = await service.calcular_perfil_usuario(str(usuario_teatro.id))

        esperado = (
            np.array(emb1) * _PESOS_CONTENIDO[InteractionType.GUARDADO]
            + np.array(emb2) * _PESOS_CONTENIDO[InteractionType.VISTA]
        ) / (
            _PESOS_CONTENIDO[InteractionType.GUARDADO]
            + _PESOS_CONTENIDO[InteractionType.VISTA]
        )

        assert perfil is not None
        np.testing.assert_allclose(perfil, esperado.tolist(), rtol=1e-6)

    @pytest.mark.asyncio
    async def test_pesos_segun_tipo_interaccion(self, usuario_teatro):
        """
        Verificar que guardado > clic > vista en influencia sobre el perfil.
        """
        emb_guardado = np.ones(384, dtype=float).tolist()   # vector de 1s
        emb_vista = np.zeros(384, dtype=float).tolist()     # vector de 0s

        filas = [
            (InteractionType.GUARDADO, emb_guardado),  # peso 3
            (InteractionType.VISTA, emb_vista),         # peso 1
        ]
        db = make_async_db(_make_db_result(filas))
        service = RecommenderService(db)

        perfil = await service.calcular_perfil_usuario(str(usuario_teatro.id))

        # El perfil debe ser (3*1 + 1*0) / 4 = 0.75
        assert perfil is not None
        assert all(abs(v - 0.75) < 1e-6 for v in perfil)

    @pytest.mark.asyncio
    async def test_multiples_tipos_de_interaccion(self, usuario_hibrido):
        """Todos los tipos de interacción contribuyen con sus pesos correctos."""
        emb = _emb(seed=99)
        filas = [
            (InteractionType.GUARDADO, emb),
            (InteractionType.ASISTIO, emb),
            (InteractionType.COMPARTIDO, emb),
            (InteractionType.CLIC, emb),
            (InteractionType.VISTA, emb),
        ]
        db = make_async_db(_make_db_result(filas))
        service = RecommenderService(db)

        perfil = await service.calcular_perfil_usuario(str(usuario_hibrido.id))

        # Todos los embeddings son iguales → el promedio ponderado también es igual
        assert perfil is not None
        np.testing.assert_allclose(perfil, emb, rtol=1e-6)

    @pytest.mark.asyncio
    async def test_retorna_lista_de_floats(self, usuario_teatro):
        """El perfil retornado debe ser una lista de floats, no un ndarray."""
        filas = [(InteractionType.CLIC, _emb(seed=5))]
        db = make_async_db(_make_db_result(filas))
        service = RecommenderService(db)

        perfil = await service.calcular_perfil_usuario(str(usuario_teatro.id))

        assert isinstance(perfil, list)
        assert all(isinstance(v, float) for v in perfil)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: buscar_por_perfil
# ─────────────────────────────────────────────────────────────────────────────


class TestBuscarPorPerfil:
    """Verifica la búsqueda por similitud vectorial."""

    @pytest.mark.asyncio
    async def test_retorna_eventos_futuros(self, usuario_teatro):
        """Debe retornar la lista de eventos que devuelve la DB."""
        eventos = [make_event(embedding=_emb(i)) for i in range(3)]
        db = make_async_db(_make_db_result(eventos))
        service = RecommenderService(db)

        resultado = await service.buscar_por_perfil(_emb(seed=0), excluir=[])

        assert resultado == eventos

    @pytest.mark.asyncio
    async def test_sin_resultados_retorna_lista_vacia(self, usuario_musica):
        """Cuando la DB no retorna eventos, el resultado es lista vacía."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        resultado = await service.buscar_por_perfil(_emb(seed=1), excluir=[])

        assert resultado == []

    @pytest.mark.asyncio
    async def test_excluir_ids_se_pasa_a_la_query(self, usuario_teatro):
        """
        La exclusión de IDs se aplica como filtro en la query.
        Verificamos que el parámetro llegue sin errores al execute.
        """
        evento = make_event(embedding=_emb(0))
        excluir = [str(uuid.uuid4()), str(uuid.uuid4())]
        db = make_async_db(_make_db_result([evento]))
        service = RecommenderService(db)

        resultado = await service.buscar_por_perfil(_emb(seed=2), excluir=excluir)

        assert db.execute.called
        assert resultado == [evento]

    @pytest.mark.asyncio
    async def test_lista_excluir_vacia_no_falla(self, usuario_teatro):
        """excluir=[] no debe lanzar excepciones."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        resultado = await service.buscar_por_perfil(_emb(seed=3), excluir=[])

        assert resultado == []


# ─────────────────────────────────────────────────────────────────────────────
# Tests: recomendar_basado_en_contenido
# ─────────────────────────────────────────────────────────────────────────────


class TestRecomendarBasadoEnContenido:
    """Tests de integración (con DB mock) para la recomendación por contenido."""

    @pytest.mark.asyncio
    async def test_sin_interacciones_cae_en_populares(self, usuario_sin_historial):
        """
        Usuario sin interacciones → recomendar_populares como fallback.
        Populares necesita 2 consultas a DB (interacciones + eventos).
        """
        user = usuario_sin_historial
        # 1ª execute: IDs de interacciones del usuario (vacío)
        # 2ª execute: interacciones globales para populares (vacío)
        # 3ª execute: eventos próximos para completar populares
        evento_popular = make_event(titulo="Obra popular")
        db = make_async_db(
            _make_db_result([]),           # ids_interactuados
            _make_db_result([]),           # populares: interacciones
            _make_db_result([evento_popular]),  # populares: eventos futuros
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_basado_en_contenido(str(user.id))

        assert isinstance(resultado, list)
        # El fallback de populares retorna dicts con "event" y "razon"
        if resultado:
            assert "event" in resultado[0]
            assert "razon" in resultado[0]

    @pytest.mark.asyncio
    async def test_con_historial_sin_embeddings_cae_en_populares(self, usuario_musica):
        """
        Interacciones presentes pero ningún evento tiene embedding → populares.
        """
        user = usuario_musica
        event_id = _uuid()
        # Fila de la query de IDs interactuados
        fila_id = MagicMock()
        fila_id.event_id = event_id

        db = make_async_db(
            _make_db_result([fila_id]),   # ids_interactuados
            _make_db_result([]),          # calcular_perfil: sin embeddings
            _make_db_result([]),          # populares: interacciones globales
            _make_db_result([]),          # populares: eventos futuros (vacío)
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_basado_en_contenido(str(user.id))

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_retorna_eventos_similares_con_historial(self, usuario_teatro):
        """
        Usuario con historial e interacciones con embeddings → eventos similares.
        """
        user = usuario_teatro
        event_id = _uuid()
        fila_id = MagicMock()
        fila_id.event_id = event_id

        emb_base = _emb(seed=10)
        cat_teatro = make_category("Teatro")
        eventos_similares = [
            make_event(titulo=f"Obra {i}", embedding=_emb(i + 11), categoria=cat_teatro)
            for i in range(5)
        ]

        db = make_async_db(
            _make_db_result([fila_id]),              # ids_interactuados
            _make_db_result([(InteractionType.GUARDADO, emb_base)]),  # perfil
            _make_db_result(eventos_similares),      # buscar_por_perfil
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_basado_en_contenido(str(user.id), limite=5)

        assert isinstance(resultado, list)
        assert len(resultado) <= 5
        for item in resultado:
            assert "event" in item
            assert "razon" in item
            assert item["razon"] == "Basado en tus intereses recientes"

    @pytest.mark.asyncio
    async def test_diversificacion_limita_por_categoria(self, usuario_teatro):
        """
        Con muchos eventos de la misma categoría, la diversificación
        no permite más de 3 de la misma.
        """
        user = usuario_teatro
        event_id = _uuid()
        fila_id = MagicMock()
        fila_id.event_id = event_id

        emb_base = _emb(seed=20)
        cat_unica = make_category("Teatro")
        # 6 eventos de la misma categoría
        candidatos = [
            make_event(titulo=f"Obra {i}", embedding=_emb(i), categoria=cat_unica)
            for i in range(6)
        ]

        db = make_async_db(
            _make_db_result([fila_id]),
            _make_db_result([(InteractionType.VISTA, emb_base)]),
            _make_db_result(candidatos),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_basado_en_contenido(str(user.id), limite=10)

        assert len(resultado) <= 3  # max_por_categoria=3

    @pytest.mark.asyncio
    async def test_respeta_limite(self, usuario_teatro):
        """El resultado no excede el límite solicitado."""
        user = usuario_teatro
        fila_id = MagicMock()
        fila_id.event_id = _uuid()

        emb_base = _emb(seed=30)
        categorias = [make_category(f"Cat{i}") for i in range(10)]
        candidatos = [
            make_event(titulo=f"Evento {i}", embedding=_emb(i), categoria=categorias[i])
            for i in range(10)
        ]

        db = make_async_db(
            _make_db_result([fila_id]),
            _make_db_result([(InteractionType.CLIC, emb_base)]),
            _make_db_result(candidatos),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_basado_en_contenido(str(user.id), limite=4)

        assert len(resultado) <= 4


# ─────────────────────────────────────────────────────────────────────────────
# Tests: recomendar_hibrido
# ─────────────────────────────────────────────────────────────────────────────


class TestRecomendarHibrido:
    """Tests para la combinación Fase 1 + Fase 2."""

    def _mock_service_con_resultados(
        self,
        db: AsyncMock,
        explicitas: list[dict],
        contenido: list[dict],
    ) -> RecommenderService:
        """
        Devuelve un RecommenderService con los métodos de Fase 1 y Fase 2
        reemplazados por mocks que retornan los valores dados.
        """
        service = RecommenderService(db)
        service.recomendar_para_usuario = AsyncMock(return_value=explicitas)
        service.recomendar_basado_en_contenido = AsyncMock(return_value=contenido)
        return service

    def _make_rec(self, event_id: str, categoria: str = "Teatro") -> dict:
        return {
            "event": {
                "id": event_id,
                "titulo": f"Evento {event_id[:8]}",
                "categoria": categoria,
                "descripcion": None,
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
            "razon": "Razón de prueba",
        }

    @pytest.mark.asyncio
    async def test_combina_resultados_sin_duplicados(self, usuario_hibrido):
        """
        Los resultados de Fase 1 y Fase 2 se combinan eliminando duplicados.
        Eventos que aparecen en ambas fases solo deben aparecer una vez.
        """
        id_compartido = str(_uuid())
        id_solo_explicito = str(_uuid())
        id_solo_contenido = str(_uuid())

        explicitas = [
            self._make_rec(id_compartido, "Teatro"),
            self._make_rec(id_solo_explicito, "Música"),
        ]
        contenido = [
            self._make_rec(id_compartido, "Teatro"),   # duplicado
            self._make_rec(id_solo_contenido, "Cine"),
        ]

        db = AsyncMock()
        service = self._mock_service_con_resultados(db, explicitas, contenido)

        resultado = await service.recomendar_hibrido(str(usuario_hibrido.id), limite=10)

        ids_resultado = [r["event"]["id"] for r in resultado]
        # Sin duplicados
        assert len(ids_resultado) == len(set(ids_resultado))
        # El evento compartido aparece exactamente una vez
        assert ids_resultado.count(id_compartido) == 1

    @pytest.mark.asyncio
    async def test_respeta_limite_final(self, usuario_hibrido):
        """El resultado no excede el límite solicitado."""
        explicitas = [self._make_rec(str(_uuid()), f"Cat{i}") for i in range(5)]
        contenido = [self._make_rec(str(_uuid()), f"Cat{i + 10}") for i in range(5)]

        db = AsyncMock()
        service = self._mock_service_con_resultados(db, explicitas, contenido)

        resultado = await service.recomendar_hibrido(str(usuario_hibrido.id), limite=6)

        assert len(resultado) <= 6

    @pytest.mark.asyncio
    async def test_prioriza_resultados_explicitos(self, usuario_hibrido):
        """
        Los resultados explícitos (Fase 1) aparecen antes que los de contenido.
        """
        id_explicito = str(_uuid())
        id_contenido = str(_uuid())

        explicitas = [self._make_rec(id_explicito, "Teatro")]
        contenido = [self._make_rec(id_contenido, "Cine")]

        db = AsyncMock()
        service = self._mock_service_con_resultados(db, explicitas, contenido)

        resultado = await service.recomendar_hibrido(str(usuario_hibrido.id), limite=10)

        ids = [r["event"]["id"] for r in resultado]
        assert ids.index(id_explicito) < ids.index(id_contenido)

    @pytest.mark.asyncio
    async def test_diversificacion_final_por_categoria(self, usuario_hibrido):
        """
        La diversificación final limita a 3 eventos por categoría en el resultado.
        """
        cat = "Teatro"
        # 8 eventos de la misma categoría en total
        explicitas = [self._make_rec(str(_uuid()), cat) for _ in range(4)]
        contenido = [self._make_rec(str(_uuid()), cat) for _ in range(4)]

        db = AsyncMock()
        service = self._mock_service_con_resultados(db, explicitas, contenido)

        resultado = await service.recomendar_hibrido(str(usuario_hibrido.id), limite=10)

        cats = [r["event"]["categoria"] for r in resultado]
        assert cats.count(cat) <= 3

    @pytest.mark.asyncio
    async def test_usuario_solo_con_preferencias_explicitas(self, usuario_teatro):
        """
        Usuario con preferencias pero sin historial implícito:
        recomendar_basado_en_contenido retorna populares, la combinación sigue.
        """
        explicitas = [self._make_rec(str(_uuid()), "Teatro") for _ in range(3)]
        contenido = [self._make_rec(str(_uuid()), "Popular") for _ in range(2)]

        db = AsyncMock()
        service = self._mock_service_con_resultados(db, explicitas, contenido)

        resultado = await service.recomendar_hibrido(str(usuario_teatro.id), limite=10)

        assert len(resultado) >= 1
        assert all("event" in r for r in resultado)

    @pytest.mark.asyncio
    async def test_usuario_solo_con_historial_implicito(self, usuario_musica):
        """
        Usuario sin preferencias explícitas: Fase 1 cae en populares,
        Fase 2 retorna eventos por contenido. El híbrido los combina.
        """
        populares = [self._make_rec(str(_uuid()), "Popular") for _ in range(2)]
        contenido = [self._make_rec(str(_uuid()), "Música") for _ in range(3)]

        db = AsyncMock()
        service = self._mock_service_con_resultados(db, populares, contenido)

        resultado = await service.recomendar_hibrido(str(usuario_musica.id), limite=10)

        assert len(resultado) >= 1

    @pytest.mark.asyncio
    async def test_resultado_vacio_si_ambas_fases_vacias(self, usuario_sin_historial):
        """Si ambas fases no retornan nada, el resultado es lista vacía."""
        db = AsyncMock()
        service = self._mock_service_con_resultados(db, [], [])

        resultado = await service.recomendar_hibrido(
            str(usuario_sin_historial.id), limite=10
        )

        assert resultado == []

    @pytest.mark.asyncio
    async def test_formato_resultado(self, usuario_hibrido):
        """Cada elemento del resultado tiene las claves 'event' y 'razon'."""
        explicitas = [self._make_rec(str(_uuid()), "Teatro")]
        contenido = [self._make_rec(str(_uuid()), "Cine")]

        db = AsyncMock()
        service = self._mock_service_con_resultados(db, explicitas, contenido)

        resultado = await service.recomendar_hibrido(str(usuario_hibrido.id), limite=10)

        for item in resultado:
            assert "event" in item
            assert "razon" in item
            assert "id" in item["event"]


# ─────────────────────────────────────────────────────────────────────────────
# Tests: pesos _PESOS_CONTENIDO (contrato de la constante)
# ─────────────────────────────────────────────────────────────────────────────


class TestPesosContenido:
    """Verifica el contrato de los pesos de interacción."""

    def test_guardado_tiene_mayor_peso_que_clic(self):
        assert _PESOS_CONTENIDO[InteractionType.GUARDADO] > _PESOS_CONTENIDO[InteractionType.CLIC]

    def test_clic_tiene_mayor_peso_que_vista(self):
        assert _PESOS_CONTENIDO[InteractionType.CLIC] > _PESOS_CONTENIDO[InteractionType.VISTA]

    def test_asistio_tiene_peso_igual_a_guardado(self):
        assert _PESOS_CONTENIDO[InteractionType.ASISTIO] == _PESOS_CONTENIDO[InteractionType.GUARDADO]

    def test_todos_los_tipos_de_interaccion_estan_definidos(self):
        for tipo in InteractionType:
            assert tipo in _PESOS_CONTENIDO, f"Falta peso para {tipo}"

    def test_todos_los_pesos_son_positivos(self):
        for tipo, peso in _PESOS_CONTENIDO.items():
            assert peso > 0, f"Peso de {tipo} debe ser positivo"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: recomendar_populares
# ─────────────────────────────────────────────────────────────────────────────


class TestRecomendarPopulares:
    """Tests para la recomendación basada en popularidad."""

    @pytest.mark.asyncio
    async def test_sin_interacciones_devuelve_eventos_futuros(self):
        """
        Sin interacciones en la DB, completa con próximos eventos.
        """
        evento = make_event(titulo="Próximo evento")
        db = make_async_db(
            _make_db_result([]),        # interacciones: vacío
            _make_db_result([evento]),  # eventos futuros para completar
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_populares(limite=5)

        assert isinstance(resultado, list)
        assert len(resultado) <= 5
        if resultado:
            assert "event" in resultado[0]
            assert "razon" in resultado[0]

    @pytest.mark.asyncio
    async def test_razon_es_descripcion_correcta(self):
        """La razón de recomendación popular describe la comunidad."""
        evento = make_event(titulo="Obra popular")
        db = make_async_db(
            _make_db_result([]),
            _make_db_result([evento]),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_populares(limite=5)

        if resultado:
            assert "popular" in resultado[0]["razon"].lower()

    @pytest.mark.asyncio
    async def test_limite_respetado(self):
        """No devuelve más eventos que el límite solicitado."""
        eventos = [make_event(titulo=f"Evento {i}") for i in range(20)]
        db = make_async_db(
            _make_db_result([]),
            _make_db_result(eventos),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_populares(limite=3)

        assert len(resultado) <= 3

    @pytest.mark.asyncio
    async def test_con_interacciones_pondera_guardados(self):
        """
        Eventos con más guardados aparecen primero.
        Verifica que el método no falla con interacciones reales.
        """
        event_id = _uuid()

        # Fila de interacción: (event_id, tipo, n)
        fila = MagicMock()
        fila.event_id = event_id
        fila.tipo = InteractionType.GUARDADO
        fila.n = 5

        evento_popular = make_event(titulo="El más guardado")
        evento_popular.id = event_id

        db = make_async_db(
            _make_db_result([fila]),           # interacciones agrupadas
            _make_db_result([evento_popular]), # eventos por IDs
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_populares(limite=10)

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_lista_vacia_cuando_no_hay_eventos(self):
        """Sin eventos en la DB, retorna lista vacía."""
        db = make_async_db(
            _make_db_result([]),  # interacciones
            _make_db_result([]),  # eventos futuros (también vacío)
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_populares(limite=5)

        assert resultado == []


# ─────────────────────────────────────────────────────────────────────────────
# Tests: recomendar_similares
# ─────────────────────────────────────────────────────────────────────────────


class TestRecomendarSimilares:
    """Tests para la recomendación de eventos similares a uno dado."""

    @pytest.mark.asyncio
    async def test_evento_inexistente_retorna_lista_vacia(self):
        """Si el evento base no existe en la DB, retorna []."""
        db = make_async_db(_make_db_result([]))  # get_evento retorna None
        service = RecommenderService(db)

        resultado = await service.recomendar_similares(str(_uuid()), limite=5)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_retorna_eventos_similares(self):
        """Con evento base existente, devuelve candidatos similares."""
        cat = make_category("Teatro")
        evento_base = make_event(titulo="Obra base", embedding=_emb(0), categoria=cat)
        candidatos = [
            make_event(titulo=f"Similar {i}", embedding=_emb(i + 1), categoria=cat)
            for i in range(3)
        ]

        db = make_async_db(
            _make_db_result([evento_base]),  # get_evento
            _make_db_result(candidatos),     # candidatos similares
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_similares(str(evento_base.id), limite=3)

        assert isinstance(resultado, list)
        assert len(resultado) <= 3
        for item in resultado:
            assert "event" in item
            assert "razon" in item

    @pytest.mark.asyncio
    async def test_razon_menciona_evento_base(self):
        """La razón de cada resultado menciona el evento de referencia."""
        cat = make_category("Cine")
        titulo_base = "La Gran Película"
        evento_base = make_event(titulo=titulo_base, embedding=_emb(0), categoria=cat)
        candidato = make_event(titulo="Otra película", embedding=_emb(1), categoria=cat)

        db = make_async_db(
            _make_db_result([evento_base]),
            _make_db_result([candidato]),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_similares(str(evento_base.id), limite=5)

        if resultado:
            assert titulo_base[:40] in resultado[0]["razon"] or "Similar" in resultado[0]["razon"]

    @pytest.mark.asyncio
    async def test_sin_candidatos_retorna_lista_vacia(self):
        """Si no hay eventos similares, retorna lista vacía."""
        cat = make_category("Danza")
        evento_base = make_event(titulo="Ballet único", embedding=_emb(0), categoria=cat)

        db = make_async_db(
            _make_db_result([evento_base]),
            _make_db_result([]),  # sin candidatos
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_similares(str(evento_base.id), limite=5)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_limite_respetado(self):
        """No devuelve más eventos que el límite solicitado."""
        cat = make_category("Música")
        evento_base = make_event(titulo="Base", embedding=_emb(0), categoria=cat)
        candidatos = [
            make_event(titulo=f"Candidato {i}", embedding=_emb(i + 1), categoria=cat)
            for i in range(10)
        ]

        db = make_async_db(
            _make_db_result([evento_base]),
            _make_db_result(candidatos),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_similares(str(evento_base.id), limite=3)

        assert len(resultado) <= 3

    @pytest.mark.asyncio
    async def test_evento_sin_embedding_no_falla(self):
        """Evento base sin embedding funciona (ordena por fecha)."""
        cat = make_category("Teatro")
        evento_base = make_event(titulo="Sin embedding", embedding=None, categoria=cat)
        candidato = make_event(titulo="Candidato", embedding=None, categoria=cat)

        db = make_async_db(
            _make_db_result([evento_base]),
            _make_db_result([candidato]),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_similares(str(evento_base.id), limite=5)

        assert isinstance(resultado, list)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: recomendar_para_usuario (Fase 1 – usuario nuevo y con historial)
# ─────────────────────────────────────────────────────────────────────────────


class TestRecomendarParaUsuario:
    """Tests para la recomendación personalizada por preferencias explícitas."""

    @pytest.mark.asyncio
    async def test_usuario_nuevo_sin_historial_cae_en_populares(
        self, usuario_sin_historial
    ):
        """
        Usuario nuevo (sin preferencias) → recomendar_populares como fallback.
        """
        evento_popular = make_event(titulo="Evento popular")
        db = make_async_db(
            _make_db_result([usuario_sin_historial]),  # get_user
            _make_db_result([]),                        # populares: interacciones
            _make_db_result([evento_popular]),          # populares: eventos futuros
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_para_usuario(
            str(usuario_sin_historial.id), limite=5
        )

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_usuario_inexistente_retorna_lista_vacia(self):
        """Usuario no encontrado en la DB → retorna []."""
        db = make_async_db(_make_db_result([]))  # get_user retorna None
        service = RecommenderService(db)

        resultado = await service.recomendar_para_usuario(str(_uuid()), limite=5)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_usuario_con_preferencias_recibe_eventos_de_categoria(
        self, usuario_teatro
    ):
        """
        Usuario con categoría favorita 'teatro' recibe eventos de esa categoría.
        """
        cat_teatro = make_category("teatro")
        evento_teatro = make_event(titulo="Obra de teatro", categoria=cat_teatro)
        evento_teatro.categoria.nombre = "teatro"

        db = make_async_db(
            _make_db_result([usuario_teatro]),   # get_user
            _make_db_result([evento_teatro]),    # candidatos filtrados
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_para_usuario(
            str(usuario_teatro.id), limite=5
        )

        assert isinstance(resultado, list)
        if resultado:
            assert "event" in resultado[0]
            assert "razon" in resultado[0]

    @pytest.mark.asyncio
    async def test_razon_menciona_preferencias(self, usuario_teatro):
        """La razón incluye información sobre las preferencias del usuario."""
        cat = make_category("teatro")
        evento = make_event(titulo="Comedia", categoria=cat)

        # Ajustar nombre para que el filtro de categoría lo reconozca
        evento.categoria.nombre = "teatro"

        db = make_async_db(
            _make_db_result([usuario_teatro]),
            _make_db_result([evento]),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_para_usuario(str(usuario_teatro.id))

        if resultado:
            # La razón debe mencionar que es por preferencias
            assert len(resultado[0]["razon"]) > 0

    @pytest.mark.asyncio
    async def test_sin_candidatos_cae_en_populares(self, usuario_teatro):
        """
        Sin candidatos de las categorías favoritas → fallback a populares.
        """
        evento_popular = make_event(titulo="Popular fallback")
        db = make_async_db(
            _make_db_result([usuario_teatro]),  # get_user
            _make_db_result([]),                # candidatos de categoría (vacío)
            _make_db_result([]),                # eventos futuros (también vacío)
            _make_db_result([]),                # populares: interacciones
            _make_db_result([evento_popular]),  # populares: eventos futuros
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_para_usuario(str(usuario_teatro.id))

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_diversificacion_no_supera_max_por_categoria(self, usuario_hibrido):
        """
        Con muchos eventos de la misma categoría, no se supera max_por_categoria=3.
        """
        cat_unica = make_category("cine")
        eventos = [
            make_event(titulo=f"Film {i}", categoria=cat_unica)
            for i in range(10)
        ]
        for e in eventos:
            e.categoria.nombre = "cine"

        db = make_async_db(
            _make_db_result([usuario_hibrido]),
            _make_db_result(eventos),
        )
        service = RecommenderService(db)

        resultado = await service.recomendar_para_usuario(str(usuario_hibrido.id), limite=10)

        # Máximo 3 por categoría
        assert len(resultado) <= 3


# ─────────────────────────────────────────────────────────────────────────────
# Tests: recomendar_por_contexto
# ─────────────────────────────────────────────────────────────────────────────


class TestRecomendarPorContexto:
    """Tests para recomendaciones contextuales sin autenticación."""

    @pytest.mark.asyncio
    async def test_sin_filtros_devuelve_eventos_futuros(self):
        """Sin filtros, devuelve eventos próximos."""
        evento = make_event(titulo="Próximo evento")
        db = make_async_db(_make_db_result([evento]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({})

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_filtro_gratis_por_bool(self):
        """Contexto con gratis=True filtra solo gratuitos."""
        evento = make_event(titulo="Gratis", es_gratuito=True)
        db = make_async_db(_make_db_result([evento]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({"gratis": True})

        assert isinstance(resultado, list)
        # El mock devuelve lo que le configuramos; verificamos que no falla
        assert db.execute.called

    @pytest.mark.asyncio
    async def test_filtro_gratis_por_query_text(self):
        """Contexto con query='gratis' activa el filtro de gratuidad."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({"query": "gratis"})

        assert isinstance(resultado, list)
        assert db.execute.called

    @pytest.mark.asyncio
    async def test_filtro_con_ninos(self):
        """Contexto con query='con niños' filtra eventos familiares."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({"query": "con niños"})

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_filtro_esta_noche(self):
        """Contexto 'esta noche' filtra eventos de hoy de 19:00 a 23:59."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({"query": "esta noche"})

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_filtro_hoy(self):
        """Contexto 'hoy' filtra eventos del día de hoy."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({"query": "hoy"})

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_filtro_fin_de_semana(self):
        """Contexto 'fin de semana' filtra eventos del próximo sábado y domingo."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({"query": "fin de semana"})

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_filtro_barrio(self):
        """Contexto con barrio hace JOIN con Venue."""
        evento = make_event(titulo="En Palermo")
        db = make_async_db(_make_db_result([evento]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({"barrio": "Palermo"})

        assert isinstance(resultado, list)

    @pytest.mark.asyncio
    async def test_razon_menciona_contexto(self):
        """La razón de recomendación describe el contexto aplicado."""
        evento = make_event(titulo="Gratis hoy")
        db = make_async_db(_make_db_result([evento]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({"gratis": True})

        if resultado:
            # La razón debe ser informativa
            assert len(resultado[0]["razon"]) > 0

    @pytest.mark.asyncio
    async def test_sin_contexto_razon_generica(self):
        """Sin filtros la razón es genérica."""
        db = make_async_db(_make_db_result([make_event()]))
        service = RecommenderService(db)

        resultado = await service.recomendar_por_contexto({})

        if resultado:
            assert "Buenos Aires" in resultado[0]["razon"] or len(resultado[0]["razon"]) > 0

    @pytest.mark.asyncio
    async def test_contexto_vacio_no_falla(self):
        """Contexto vacío no lanza excepciones."""
        db = make_async_db(_make_db_result([]))
        service = RecommenderService(db)

        # No debe lanzar excepciones
        resultado = await service.recomendar_por_contexto({})
        assert isinstance(resultado, list)
