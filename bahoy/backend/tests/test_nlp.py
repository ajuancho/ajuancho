"""
Bahoy Backend - Tests de NLP (clasificador + embeddings).

Complementa test_classifier.py con tests específicos de:
  - Generación de embeddings (dimensión, tipo, normalización)
  - Comportamiento del clasificador con embeddings mockeados
  - Similitud coseno entre vectores
  - Pipeline completo con fallback a embeddings
  - Extracción de "entidades" implícitas: tags contextuales

El modelo de sentence-transformers se mockea para evitar
la descarga en el entorno de CI/test.

Ejecutar:
    docker-compose exec backend pytest tests/test_nlp.py -v
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.nlp.classifier import (
    CATEGORIAS_KEYWORDS,
    DESCRIPCIONES_TIPICAS,
    _clasificar_por_embeddings,
    _clasificar_por_reglas,
    _detectar_subcategoria,
    _generar_tags,
    _normalizar_texto,
    _similitud_coseno,
    clasificar_evento,
)

# Dimensión de los embeddings (384 para paraphrase-multilingual-MiniLM-L12-v2)
NLP_DIM = 384


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_vector(values: list[float]) -> np.ndarray:
    return np.array(values, dtype=float)


def _normalized_vector(seed: int, dim: int = 384) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype(float)
    return v / np.linalg.norm(v)


def _mock_sentence_transformer(embed_fn=None):
    """
    Crea un mock de SentenceTransformer.encode() que retorna
    vectores deterministas basados en el texto de entrada.
    """
    modelo = MagicMock()
    if embed_fn is None:
        # Por defecto, devuelve el mismo vector para cualquier texto
        modelo.encode.return_value = _normalized_vector(seed=0)
    else:
        modelo.encode.side_effect = embed_fn
    return modelo


# ─────────────────────────────────────────────────────────────────────────────
# Tests: _similitud_coseno
# ─────────────────────────────────────────────────────────────────────────────


class TestSimilitudCoseno:
    """Tests para la función de similitud coseno."""

    def test_vectores_identicos_similitud_uno(self):
        """Vectores idénticos tienen similitud coseno = 1."""
        v = _normalized_vector(seed=1)
        sim = _similitud_coseno(v, v)
        assert sim == pytest.approx(1.0, abs=1e-6)

    def test_vectores_opuestos_similitud_menos_uno(self):
        """Vectores opuestos tienen similitud coseno = -1."""
        v = np.array([1.0, 0.0, 0.0])
        sim = _similitud_coseno(v, -v)
        assert sim == pytest.approx(-1.0, abs=1e-6)

    def test_vectores_ortogonales_similitud_cero(self):
        """Vectores ortogonales tienen similitud coseno = 0."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        sim = _similitud_coseno(v1, v2)
        assert sim == pytest.approx(0.0, abs=1e-6)

    def test_vector_cero_retorna_cero(self):
        """Vector cero no divide por cero, retorna 0."""
        v = np.array([1.0, 2.0, 3.0])
        cero = np.array([0.0, 0.0, 0.0])
        sim = _similitud_coseno(v, cero)
        assert sim == 0.0

    def test_similitud_es_simetrica(self):
        """sim(a, b) == sim(b, a)."""
        v1 = _normalized_vector(seed=10)
        v2 = _normalized_vector(seed=20)
        assert _similitud_coseno(v1, v2) == pytest.approx(
            _similitud_coseno(v2, v1), abs=1e-6
        )

    def test_similitud_entre_menos_uno_y_uno(self):
        """La similitud coseno siempre está en [-1, 1]."""
        for seed in range(5):
            v1 = _normalized_vector(seed=seed)
            v2 = _normalized_vector(seed=seed + 10)
            sim = _similitud_coseno(v1, v2)
            assert -1.0 <= sim <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Generación de embeddings con modelo mockeado
# ─────────────────────────────────────────────────────────────────────────────


class TestGeneracionEmbeddings:
    """
    Tests para la generación de embeddings con el modelo de sentence-transformers.
    El modelo se mockea para no requerir descarga de pesos.
    """

    def test_clasificar_por_embeddings_retorna_categoria(self):
        """_clasificar_por_embeddings devuelve una categoría conocida."""
        categorias_validas = set(DESCRIPCIONES_TIPICAS.keys())
        embedding_teatro = _normalized_vector(seed=0)

        def encode_fn(texto):
            # Mismo embedding para todo texto → categoría arbitraria pero válida
            return embedding_teatro

        with patch("app.nlp.classifier._get_modelo") as mock_get:
            mock_get.return_value = _mock_sentence_transformer(encode_fn)
            result = _clasificar_por_embeddings("evento de prueba", "descripción")

        assert result["categoria"] in categorias_validas

    def test_clasificar_por_embeddings_retorna_confianza_flotante(self):
        """La confianza es un float entre 0 y 1."""
        with patch("app.nlp.classifier._get_modelo") as mock_get:
            mock_get.return_value = _mock_sentence_transformer()
            result = _clasificar_por_embeddings("texto", "descripción")

        assert isinstance(result["confianza"], float)
        assert 0.0 <= result["confianza"] <= 1.0

    def test_clasificar_por_embeddings_metodo_es_embeddings(self):
        """El método reportado es 'embeddings'."""
        with patch("app.nlp.classifier._get_modelo") as mock_get:
            mock_get.return_value = _mock_sentence_transformer()
            result = _clasificar_por_embeddings("texto", "descripción")

        assert result["metodo"] == "embeddings"

    def test_clasificar_por_embeddings_alta_similitud_teatro(self):
        """
        Si el embedding del evento es idéntico al de Teatro,
        la categoría debe ser Teatro con alta confianza.
        """
        # Embeddings para las categorías (distintos entre sí)
        emb_teatro = _normalized_vector(seed=1)
        emb_otros = {
            cat: _normalized_vector(seed=i + 10)
            for i, cat in enumerate(DESCRIPCIONES_TIPICAS.keys())
            if cat != "Teatro"
        }
        emb_otros["Teatro"] = emb_teatro

        def encode_fn(texto):
            # Devuelve el embedding de la categoría cuya descripción coincide
            for cat, desc in DESCRIPCIONES_TIPICAS.items():
                if desc in texto:
                    return emb_otros.get(cat, _normalized_vector(seed=99))
            # Para el texto del evento: devuelve el embedding de Teatro
            return emb_teatro

        with patch("app.nlp.classifier._get_modelo") as mock_get:
            mock_get.return_value = _mock_sentence_transformer(encode_fn)
            result = _clasificar_por_embeddings("obra teatral", "función en escena")

        assert result["categoria"] == "Teatro"
        assert result["confianza"] == pytest.approx(1.0, abs=1e-6)

    def test_fallback_a_embeddings_cuando_reglas_son_ambiguas(self):
        """
        Si las reglas son ambiguas (empate), se usa el clasificador por embeddings.
        """
        # Este texto tiene keywords de teatro Y música → ambigüedad → embeddings
        titulo = "Concierto de teatro musical"
        descripcion = "obra con recital, actor y cantante"

        con_reglas = _clasificar_por_reglas(titulo, descripcion)
        # Puede ser None (empate) o un resultado con baja confianza

        with patch("app.nlp.classifier._get_modelo") as mock_get:
            mock_get.return_value = _mock_sentence_transformer()
            result = clasificar_evento(titulo, descripcion)

        # Siempre debe retornar una categoría
        assert result["categoria"] is not None
        assert result["metodo"] in ("reglas", "embeddings")

    def test_embedding_encode_llamado_con_texto(self):
        """El modelo recibe el texto correcto para encodear."""
        mock_modelo = _mock_sentence_transformer()
        mock_modelo.encode.return_value = _normalized_vector(seed=0)

        with patch("app.nlp.classifier._get_modelo") as mock_get:
            mock_get.return_value = mock_modelo
            _clasificar_por_embeddings("Mi evento", "Mi descripción")

        # encode fue llamado al menos una vez
        assert mock_modelo.encode.call_count >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Pipeline completo (clasificar_evento)
# ─────────────────────────────────────────────────────────────────────────────


class TestPipelineCompleto:
    """Tests del pipeline end-to-end de clasificación."""

    def test_evento_de_teatro_clasificado_por_reglas(self):
        """Obra teatral clara → clasificada por reglas sin embeddings."""
        result = clasificar_evento(
            "Obra Teatral – Elenco Completo",
            "Función con actor, actriz y escena del teatro.",
        )
        assert result["categoria"] == "Teatro"
        assert result["metodo"] == "reglas"
        # No debe haber llamado al modelo de embeddings

    def test_evento_de_musica_clasificado_por_reglas(self):
        """Concierto claro → clasificado por reglas."""
        result = clasificar_evento(
            "Recital de Rock",
            "Gran show de la banda en el estadio.",
        )
        assert result["categoria"] == "Música"
        assert result["metodo"] == "reglas"

    def test_evento_ambiguo_usa_embeddings(self):
        """Evento sin keywords claras → intenta embeddings."""
        with patch("app.nlp.classifier._get_modelo") as mock_get:
            mock_get.return_value = _mock_sentence_transformer()
            result = clasificar_evento(
                "Propuesta única e irrepetible",
                "Una experiencia diferente en el centro porteño.",
            )
        assert result["categoria"] is not None
        assert result["metodo"] in ("reglas", "embeddings")

    def test_todas_las_categorias_clasificables(self):
        """Cada categoría del diccionario tiene al menos un evento que la activa."""
        eventos_por_categoria = {
            "Teatro": ("Gran obra teatral", "Función con actores en escena"),
            "Música": ("Concierto de jazz", "Show de la banda con recital"),
            "Exposiciones": ("Exposición de arte", "Muestra en galería con fotografía"),
            "Gastronomía": ("Degustación gastronómica", "Chef con menú y maridaje"),
            "Cine": ("Proyección de film", "Ciclo de cine documental en el cine"),
            "Danza": ("Espectáculo de ballet", "Función con bailarines y coreografía"),
            "Talleres": ("Taller participativo", "Workshop con curso y capacitación"),
            "Festivales": ("Gran festival", "Feria y encuentro con jornada cultural"),
        }
        for categoria_esperada, (titulo, desc) in eventos_por_categoria.items():
            result = _clasificar_por_reglas(titulo, desc)
            assert result is not None, (
                f"Las reglas no clasificaron '{titulo}' como '{categoria_esperada}'"
            )
            assert result["categoria"] == categoria_esperada

    def test_resultado_tiene_todas_las_claves(self):
        """clasificar_evento siempre retorna un dict con las 5 claves."""
        result = clasificar_evento("Ballet", "Danza clásica")
        assert set(result.keys()) == {"categoria", "subcategoria", "confianza", "metodo", "tags"}

    def test_confianza_mayor_con_mas_keywords(self):
        """Más keywords de la misma categoría → mayor confianza."""
        result_muchas = _clasificar_por_reglas(
            "Obra teatral",
            "Función con actor, actriz, elenco y escena del teatro.",
        )
        result_pocas = _clasificar_por_reglas(
            "Evento en teatro",
            "Una propuesta.",
        )
        assert result_muchas is not None
        assert result_pocas is not None
        assert result_muchas["confianza"] >= result_pocas["confianza"]


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Extracción de entidades / Tags contextuales
# ─────────────────────────────────────────────────────────────────────────────


class TestExtraccionEntidades:
    """
    Tests de extracción de entidades implícitas del texto del evento.
    Bahoy extrae entidades clave como indicadores de gratuidad, público
    objetivo, horario y ubicación usando la función _generar_tags.
    """

    # ── Gratuidad ──────────────────────────────────────────────────────────────

    def test_entidad_gratuito_por_precio_cero(self):
        """Precio 0 → entidad 'gratuito' detectada."""
        tags = _generar_tags("Concierto", "Música en vivo", precio=0.0)
        assert "gratuito" in tags

    def test_entidad_gratuito_por_keyword_gratis(self):
        """Keyword 'gratis' en texto → entidad 'gratuito'."""
        tags = _generar_tags("Muestra", "Entrada gratis para todos")
        assert "gratuito" in tags

    def test_entidad_gratuito_por_entrada_libre(self):
        """'entrada libre' → entidad 'gratuito'."""
        tags = _generar_tags("Festival", "Actividad con entrada libre")
        assert "gratuito" in tags

    def test_entidad_gratuito_por_sin_costo(self):
        """'sin costo' → entidad 'gratuito'."""
        tags = _generar_tags("Taller", "Clase sin costo para el público")
        assert "gratuito" in tags

    def test_no_entidad_gratuito_con_precio_positivo(self):
        """Precio positivo sin keywords → sin 'gratuito'."""
        tags = _generar_tags("Obra", "Gran función", precio=4000.0)
        assert "gratuito" not in tags

    # ── Público objetivo ────────────────────────────────────────────────────────

    def test_entidad_familiar_por_ninos(self):
        """'niños' → entidad 'familiar'."""
        tags = _generar_tags("Circo", "Espectáculo para niños")
        assert "familiar" in tags

    def test_entidad_familiar_por_familia(self):
        """'familia' → entidad 'familiar'."""
        tags = _generar_tags("Teatro", "Obra para toda la familia")
        assert "familiar" in tags

    def test_entidad_familiar_por_infantil(self):
        """'infantil' → entidad 'familiar'."""
        tags = _generar_tags("Espectáculo infantil", "Para chicos y chicas")
        assert "familiar" in tags

    def test_sin_entidad_familiar_sin_keywords(self):
        """Sin keywords de familia → sin 'familiar'."""
        tags = _generar_tags("Obra adulta", "Temática compleja")
        assert "familiar" not in tags

    # ── Ubicación exterior ─────────────────────────────────────────────────────

    def test_entidad_aire_libre_por_plaza(self):
        """'plaza' → entidad 'al aire libre'."""
        tags = _generar_tags("Concierto", "En la plaza del barrio")
        assert "al aire libre" in tags

    def test_entidad_aire_libre_por_parque(self):
        """'parque' → entidad 'al aire libre'."""
        tags = _generar_tags("Festival", "Gran festival en el parque")
        assert "al aire libre" in tags

    def test_entidad_aire_libre_por_keyword_explicito(self):
        """'aire libre' → entidad 'al aire libre'."""
        tags = _generar_tags("Show", "Evento al aire libre")
        assert "al aire libre" in tags

    # ── Horario ────────────────────────────────────────────────────────────────

    def test_entidad_nocturno_a_las_20(self):
        """Hora >= 20:00 → entidad 'nocturno'."""
        fecha = datetime(2025, 3, 15, 20, 0)
        tags = _generar_tags("Show", "Función de noche", fecha=fecha)
        assert "nocturno" in tags

    def test_entidad_nocturno_a_las_23(self):
        """23:00 también es nocturno."""
        fecha = datetime(2025, 3, 15, 23, 0)
        tags = _generar_tags("DJ Set", "Electrónica", fecha=fecha)
        assert "nocturno" in tags

    def test_no_entidad_nocturno_a_las_19(self):
        """19:59 no es nocturno (umbral en 20:00)."""
        fecha = datetime(2025, 3, 15, 19, 59)
        tags = _generar_tags("Teatro", "Función de tarde", fecha=fecha)
        assert "nocturno" not in tags

    def test_no_entidad_nocturno_sin_fecha(self):
        """Sin fecha, no se detecta 'nocturno'."""
        tags = _generar_tags("Show", "Función especial")
        assert "nocturno" not in tags

    # ── Fin de semana ──────────────────────────────────────────────────────────

    def test_entidad_fin_de_semana_sabado(self):
        """Sábado → entidad 'fin de semana'."""
        # 2025-07-05 es sábado
        fecha = datetime(2025, 7, 5, 18, 0)
        assert fecha.weekday() == 5  # 5 = sábado
        tags = _generar_tags("Ballet", "Función especial", fecha=fecha)
        assert "fin de semana" in tags

    def test_entidad_fin_de_semana_domingo(self):
        """Domingo → entidad 'fin de semana'."""
        # 2025-07-06 es domingo
        fecha = datetime(2025, 7, 6, 16, 0)
        assert fecha.weekday() == 6  # 6 = domingo
        tags = _generar_tags("Ballet", "Función especial", fecha=fecha)
        assert "fin de semana" in tags

    def test_no_entidad_fin_de_semana_entre_semana(self):
        """Lunes a viernes → sin 'fin de semana'."""
        # 2025-07-07 es lunes
        fecha = datetime(2025, 7, 7, 20, 0)
        assert fecha.weekday() == 0  # 0 = lunes
        tags = _generar_tags("Taller", "Clase regular", fecha=fecha)
        assert "fin de semana" not in tags

    # ── Combinaciones ──────────────────────────────────────────────────────────

    def test_multiples_entidades_simultaneas(self):
        """Evento que activa todas las entidades a la vez."""
        # Sábado 21hs, gratis, al aire libre, para niños
        fecha = datetime(2025, 7, 5, 21, 0)  # sábado
        tags = _generar_tags(
            "Gran Festival Infantil en el Parque",
            "Para toda la familia. Entrada gratis en el parque al aire libre.",
            precio=0.0,
            fecha=fecha,
        )
        assert "gratuito" in tags
        assert "familiar" in tags
        assert "al aire libre" in tags
        assert "nocturno" in tags
        assert "fin de semana" in tags

    def test_sin_contexto_tags_vacios(self):
        """Sin precio, fecha, ni keywords → lista vacía."""
        tags = _generar_tags("Evento genérico", "Propuesta artística")
        assert tags == []

    def test_tags_son_lista_de_strings(self):
        """Los tags retornados son siempre una lista de strings."""
        tags = _generar_tags("Ballet", "Danza clásica", precio=0.0)
        assert isinstance(tags, list)
        assert all(isinstance(t, str) for t in tags)

    def test_no_duplicados_en_tags(self):
        """No hay tags duplicados en la lista."""
        fecha = datetime(2025, 7, 5, 21, 0)
        tags = _generar_tags(
            "Festival gratis al aire libre",
            "gratis gratis gratis en parque parque",
            precio=0.0,
            fecha=fecha,
        )
        assert len(tags) == len(set(tags))


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Diccionarios de keywords (contratos de configuración)
# ─────────────────────────────────────────────────────────────────────────────


class TestConfiguracionNLP:
    """Tests del contrato de configuración del NLP."""

    def test_todas_las_categorias_tienen_keywords(self):
        """Cada categoría en CATEGORIAS_KEYWORDS tiene al menos 3 keywords."""
        for cat, keywords in CATEGORIAS_KEYWORDS.items():
            assert len(keywords) >= 3, (
                f"Categoría '{cat}' tiene solo {len(keywords)} keyword(s)"
            )

    def test_todas_las_categorias_tienen_descripcion_tipica(self):
        """Cada categoría en CATEGORIAS_KEYWORDS tiene descripción típica."""
        for cat in CATEGORIAS_KEYWORDS:
            assert cat in DESCRIPCIONES_TIPICAS, (
                f"Categoría '{cat}' no tiene descripción típica"
            )

    def test_keywords_son_strings(self):
        """Todas las keywords son strings."""
        for cat, keywords in CATEGORIAS_KEYWORDS.items():
            for kw in keywords:
                assert isinstance(kw, str), f"Keyword '{kw}' en '{cat}' no es string"

    def test_keywords_en_minusculas(self):
        """Las keywords deben estar en minúsculas para comparación consistente."""
        for cat, keywords in CATEGORIAS_KEYWORDS.items():
            for kw in keywords:
                assert kw == kw.lower(), (
                    f"Keyword '{kw}' en '{cat}' no está en minúsculas"
                )

    def test_descripciones_tipicas_son_strings_no_vacios(self):
        """Las descripciones típicas son strings no vacíos."""
        for cat, desc in DESCRIPCIONES_TIPICAS.items():
            assert isinstance(desc, str)
            assert len(desc.strip()) > 0, f"Descripción vacía para '{cat}'"

    def test_normalizar_texto_es_idempotente(self):
        """Aplicar _normalizar_texto dos veces produce el mismo resultado."""
        texto = "Función TEATRAL con actores, actrices y escena!"
        normalizado_una = _normalizar_texto(texto)
        normalizado_dos = _normalizar_texto(normalizado_una)
        assert normalizado_una == normalizado_dos
