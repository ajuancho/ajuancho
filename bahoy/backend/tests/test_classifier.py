"""
Tests unitarios para el clasificador de eventos culturales de Bahoy.

Los ejemplos están basados en eventos reales de Buenos Aires
(Teatro San Martín, Centro Cultural Recoleta, La Trastienda, etc.).

Ejecutar con:
    cd bahoy/backend
    pytest tests/test_classifier.py -v
"""

from datetime import datetime

import pytest

from app.nlp.classifier import (
    _clasificar_por_reglas,
    _detectar_subcategoria,
    _generar_tags,
    _normalizar_texto,
    clasificar_evento,
)


# ---------------------------------------------------------------------------
# Fixtures compartidas
# ---------------------------------------------------------------------------

@pytest.fixture
def evento_teatro_comedia():
    return {
        "titulo": "La Noche de los Asesinos",
        "descripcion": (
            "Una obra teatral con un elenco de primer nivel. La función cuenta "
            "con tres actores y una actriz que despliegan una comedia oscura "
            "en la escena del Teatro San Martín."
        ),
    }


@pytest.fixture
def evento_musica_concierto():
    return {
        "titulo": "Concierto de Cierre de Temporada – Orquesta Sinfónica Nacional",
        "descripcion": (
            "Gran recital de la orquesta sinfónica con cantante invitada. "
            "La banda interpreta obras del repertorio clásico y folklore argentino."
        ),
    }


@pytest.fixture
def evento_exposicion():
    return {
        "titulo": "Muestra Fotográfica: Buenos Aires en Blanco y Negro",
        "descripcion": (
            "Exposición de fotografía documental en la galería del Centro Cultural "
            "Recoleta. Se exhiben obras de arte de artistas emergentes."
        ),
    }


@pytest.fixture
def evento_gastronomia():
    return {
        "titulo": "Noche de Maridaje – Chef Donato De Santis",
        "descripcion": (
            "Degustación exclusiva con el chef. El menú de cinco pasos incluye "
            "maridaje de vinos. Bar privado con capacidad limitada."
        ),
    }


@pytest.fixture
def evento_cine():
    return {
        "titulo": "Ciclo de Cine Documental – Retrospectiva Pino Solanas",
        "descripcion": (
            "Proyección del film 'La Hora de los Hornos'. El ciclo rinde homenaje "
            "al director y a la cinematografía nacional. Cine Gaumont, sala 2."
        ),
    }


@pytest.fixture
def evento_danza():
    return {
        "titulo": "Ballet Folklórico Nacional – Función Especial",
        "descripcion": (
            "Espectáculo de danza folclórica con coreografía de Norma Viola. "
            "El conjunto de bailarines presenta malambo, zamba y chacarera."
        ),
    }


@pytest.fixture
def evento_taller():
    return {
        "titulo": "Workshop de Escritura Creativa",
        "descripcion": (
            "Taller intensivo para aprender técnicas narrativas. El curso incluye "
            "clases teóricas y práctica de escritura. Capacidad: 20 personas."
        ),
    }


@pytest.fixture
def evento_festival():
    return {
        "titulo": "Festival Internacional de Buenos Aires (FIBA)",
        "descripcion": (
            "Gran festival multidisciplinario con jornada de actividades artísticas. "
            "Feria de editores, encuentros y propuestas al aire libre en el parque."
        ),
    }


# ---------------------------------------------------------------------------
# Tests: _normalizar_texto
# ---------------------------------------------------------------------------

class TestNormalizarTexto:
    def test_convierte_a_minusculas(self):
        assert _normalizar_texto("TEATRO") == "teatro"

    def test_elimina_puntuacion(self):
        resultado = _normalizar_texto("obra, función!")
        assert "," not in resultado
        assert "!" not in resultado

    def test_normaliza_espacios(self):
        resultado = _normalizar_texto("obra   teatral")
        assert "  " not in resultado

    def test_preserva_acentos(self):
        resultado = _normalizar_texto("música, exposición")
        assert "música" in resultado
        assert "exposición" in resultado


# ---------------------------------------------------------------------------
# Tests: Capa 1 – _clasificar_por_reglas
# ---------------------------------------------------------------------------

class TestClasificarPorReglas:

    def test_clasifica_teatro(self, evento_teatro_comedia):
        resultado = _clasificar_por_reglas(
            evento_teatro_comedia["titulo"],
            evento_teatro_comedia["descripcion"],
        )
        assert resultado is not None
        assert resultado["categoria"] == "Teatro"
        assert resultado["metodo"] == "reglas"
        assert resultado["confianza"] >= 0.35

    def test_clasifica_musica(self, evento_musica_concierto):
        resultado = _clasificar_por_reglas(
            evento_musica_concierto["titulo"],
            evento_musica_concierto["descripcion"],
        )
        assert resultado is not None
        assert resultado["categoria"] == "Música"
        assert resultado["metodo"] == "reglas"

    def test_clasifica_exposicion(self, evento_exposicion):
        resultado = _clasificar_por_reglas(
            evento_exposicion["titulo"],
            evento_exposicion["descripcion"],
        )
        assert resultado is not None
        assert resultado["categoria"] == "Exposiciones"

    def test_clasifica_gastronomia(self, evento_gastronomia):
        resultado = _clasificar_por_reglas(
            evento_gastronomia["titulo"],
            evento_gastronomia["descripcion"],
        )
        assert resultado is not None
        assert resultado["categoria"] == "Gastronomía"

    def test_clasifica_cine(self, evento_cine):
        resultado = _clasificar_por_reglas(
            evento_cine["titulo"],
            evento_cine["descripcion"],
        )
        assert resultado is not None
        assert resultado["categoria"] == "Cine"

    def test_clasifica_danza(self, evento_danza):
        resultado = _clasificar_por_reglas(
            evento_danza["titulo"],
            evento_danza["descripcion"],
        )
        assert resultado is not None
        assert resultado["categoria"] == "Danza"

    def test_clasifica_taller(self, evento_taller):
        resultado = _clasificar_por_reglas(
            evento_taller["titulo"],
            evento_taller["descripcion"],
        )
        assert resultado is not None
        assert resultado["categoria"] == "Talleres"

    def test_clasifica_festival(self, evento_festival):
        resultado = _clasificar_por_reglas(
            evento_festival["titulo"],
            evento_festival["descripcion"],
        )
        assert resultado is not None
        assert resultado["categoria"] == "Festivales"

    def test_retorna_none_sin_keywords(self):
        resultado = _clasificar_por_reglas(
            "Evento especial de verano",
            "Una propuesta única e irrepetible para toda la ciudad.",
        )
        assert resultado is None

    def test_confianza_aumenta_con_mas_matches(self):
        # Un evento con muchas palabras clave de teatro
        resultado_mucho = _clasificar_por_reglas(
            "Gran obra teatral – Elenco completo",
            "Función especial con actor, actriz, y toda la escena del teatro.",
        )
        resultado_poco = _clasificar_por_reglas(
            "Evento en el teatro",
            "Una propuesta cultural.",
        )
        assert resultado_mucho is not None
        assert resultado_poco is not None
        assert resultado_mucho["confianza"] >= resultado_poco["confianza"]

    def test_confianza_entre_0_y_1(self, evento_teatro_comedia):
        resultado = _clasificar_por_reglas(
            evento_teatro_comedia["titulo"],
            evento_teatro_comedia["descripcion"],
        )
        assert resultado is not None
        assert 0.0 <= resultado["confianza"] <= 1.0


# ---------------------------------------------------------------------------
# Tests: _detectar_subcategoria
# ---------------------------------------------------------------------------

class TestDetectarSubcategoria:

    def test_teatro_comedia(self):
        subcat = _detectar_subcategoria(
            "La Gran Comedia", "Una comedia de humor absurdo con muchas risas.", "Teatro"
        )
        assert subcat == "Comedia"

    def test_teatro_musical(self):
        subcat = _detectar_subcategoria(
            "Mamma Mia – El Musical",
            "Musical con canciones y canto en vivo.",
            "Teatro",
        )
        assert subcat == "Musical"

    def test_musica_jazz(self):
        subcat = _detectar_subcategoria(
            "Noche de Jazz en el ND Ateneo",
            "Improvisación y standards de jazz.",
            "Música",
        )
        assert subcat == "Jazz"

    def test_musica_clasica(self):
        subcat = _detectar_subcategoria(
            "Concierto de la Orquesta Sinfónica",
            "Música clásica con la orquesta y la sinfónica.",
            "Música",
        )
        assert subcat == "Clásica"

    def test_cine_documental(self):
        subcat = _detectar_subcategoria(
            "Documental sobre la dictadura",
            "Proyección de un documental histórico.",
            "Cine",
        )
        assert subcat == "Documental"

    def test_danza_tango(self):
        subcat = _detectar_subcategoria(
            "Noche de Tango en La Catedral",
            "Milonga con orquesta de tango en vivo.",
            "Danza",
        )
        assert subcat == "Tango"

    def test_sin_subcategoria_conocida(self):
        subcat = _detectar_subcategoria(
            "Evento de teatro sin pistas adicionales",
            "Una propuesta única.",
            "Teatro",
        )
        assert subcat is None

    def test_categoria_sin_subcategorias(self):
        subcat = _detectar_subcategoria("Algo", "Descripción", "CategoriaInexistente")
        assert subcat is None


# ---------------------------------------------------------------------------
# Tests: _generar_tags
# ---------------------------------------------------------------------------

class TestGenerarTags:

    def test_tag_gratuito_por_precio_cero(self):
        tags = _generar_tags("Concierto", "Música en vivo", precio=0.0)
        assert "gratuito" in tags

    def test_tag_gratuito_por_texto_gratis(self):
        tags = _generar_tags("Festival", "Entrada libre y gratuita para todos")
        assert "gratuito" in tags

    def test_tag_gratuito_por_texto_entrada_libre(self):
        tags = _generar_tags("Muestra", "Visita con entrada libre, sin costo")
        assert "gratuito" in tags

    def test_no_tag_gratuito_con_precio_positivo(self):
        tags = _generar_tags("Obra", "Gran elenco", precio=1500.0)
        assert "gratuito" not in tags

    def test_tag_familiar_por_ninos(self):
        tags = _generar_tags("Circo", "Espectáculo para niños y niñas de todas las edades")
        assert "familiar" in tags

    def test_tag_familiar_por_familia(self):
        tags = _generar_tags("Teatro", "Una obra familiar para toda la familia")
        assert "familiar" in tags

    def test_tag_al_aire_libre_plaza(self):
        tags = _generar_tags("Concierto", "Evento en la plaza central al aire libre")
        assert "al aire libre" in tags

    def test_tag_al_aire_libre_parque(self):
        tags = _generar_tags("Festival", "Gran festival en el parque Centenario")
        assert "al aire libre" in tags

    def test_tag_nocturno_a_las_21(self):
        fecha = datetime(2024, 7, 15, 21, 0)
        tags = _generar_tags("Show", "Noche especial", fecha=fecha)
        assert "nocturno" in tags

    def test_no_tag_nocturno_a_las_18(self):
        fecha = datetime(2024, 7, 15, 18, 0)
        tags = _generar_tags("Show", "Tarde cultural", fecha=fecha)
        assert "nocturno" not in tags

    def test_tag_fin_de_semana_sabado(self):
        # 2024-07-13 es sábado
        fecha = datetime(2024, 7, 13, 18, 0)
        tags = _generar_tags("Muestra", "Arte contemporáneo", fecha=fecha)
        assert "fin de semana" in tags

    def test_tag_fin_de_semana_domingo(self):
        # 2024-07-14 es domingo
        fecha = datetime(2024, 7, 14, 16, 0)
        tags = _generar_tags("Ballet", "Danza clásica", fecha=fecha)
        assert "fin de semana" in tags

    def test_no_tag_fin_de_semana_lunes(self):
        # 2024-07-15 es lunes
        fecha = datetime(2024, 7, 15, 20, 0)
        tags = _generar_tags("Taller", "Curso semanal", fecha=fecha)
        assert "fin de semana" not in tags

    def test_multiples_tags_simultaneos(self):
        # Sábado a las 21h, gratis, al aire libre, para niños
        fecha = datetime(2024, 7, 13, 21, 0)
        tags = _generar_tags(
            "Festival Infantil",
            "Evento para niños y familias en el parque, entrada gratis",
            precio=0,
            fecha=fecha,
        )
        assert "gratuito" in tags
        assert "familiar" in tags
        assert "al aire libre" in tags
        assert "nocturno" in tags
        assert "fin de semana" in tags

    def test_tags_vacios_sin_contexto(self):
        tags = _generar_tags("Evento", "Propuesta cultural")
        assert tags == []


# ---------------------------------------------------------------------------
# Tests: clasificar_evento (función principal)
# ---------------------------------------------------------------------------

class TestClasificarEvento:

    def test_retorna_dict_completo(self, evento_teatro_comedia):
        resultado = clasificar_evento(
            evento_teatro_comedia["titulo"],
            evento_teatro_comedia["descripcion"],
        )
        assert "categoria" in resultado
        assert "subcategoria" in resultado
        assert "confianza" in resultado
        assert "metodo" in resultado
        assert "tags" in resultado

    def test_teatro_comedia_real(self, evento_teatro_comedia):
        resultado = clasificar_evento(
            evento_teatro_comedia["titulo"],
            evento_teatro_comedia["descripcion"],
        )
        assert resultado["categoria"] == "Teatro"
        assert resultado["metodo"] in ("reglas", "embeddings")
        assert 0.0 <= resultado["confianza"] <= 1.0

    def test_concierto_gratuito_fin_de_semana(self):
        """Evento real: concierto gratuito en el parque los domingos."""
        fecha = datetime(2024, 8, 11, 17, 0)  # domingo
        resultado = clasificar_evento(
            titulo="Concierto de Bandas Independientes – Parque Centenario",
            descripcion=(
                "Show de tres bandas de rock indie en el parque. "
                "Entrada libre y gratuita. Ideal para toda la familia."
            ),
            precio=0,
            fecha=fecha,
        )
        assert resultado["categoria"] == "Música"
        assert "gratuito" in resultado["tags"]
        assert "fin de semana" in resultado["tags"]
        assert "al aire libre" in resultado["tags"]
        assert "familiar" in resultado["tags"]

    def test_obra_nocturna_de_pago(self):
        """Obra teatral de noche, con precio."""
        fecha = datetime(2024, 9, 20, 21, 30)  # viernes, 21:30h
        resultado = clasificar_evento(
            titulo="Hamlet – Teatro Cervantes",
            descripcion=(
                "Obra teatral con elenco de renombre. "
                "El actor principal es reconocido internacionalmente."
            ),
            precio=4500.0,
            fecha=fecha,
        )
        assert resultado["categoria"] == "Teatro"
        assert "nocturno" in resultado["tags"]
        assert "gratuito" not in resultado["tags"]
        assert "fin de semana" not in resultado["tags"]

    def test_exposicion_museo_gratis(self):
        """Muestra gratuita en museo."""
        resultado = clasificar_evento(
            titulo="Exposición Permanente – MALBA",
            descripcion=(
                "Muestra de arte contemporáneo latinoamericano. "
                "Galería con instalaciones y obra plástica. Entrada libre los miércoles."
            ),
            precio=0,
        )
        assert resultado["categoria"] == "Exposiciones"
        assert "gratuito" in resultado["tags"]

    def test_taller_con_subcategoria(self):
        resultado = clasificar_evento(
            titulo="Taller de Escritura Creativa – Casa de la Cultura",
            descripcion=(
                "Curso de escritura narrativa y poesía para adultos. "
                "Clase teórico-práctica, capacidad limitada."
            ),
        )
        assert resultado["categoria"] == "Talleres"
        assert resultado["subcategoria"] == "Escritura"

    def test_festival_aire_libre(self):
        fecha = datetime(2024, 11, 9, 12, 0)  # sábado, mediodía
        resultado = clasificar_evento(
            titulo="Feria de Diseño y Arte en Palermo",
            descripcion=(
                "Gran festival y feria con stands de artistas y diseñadores. "
                "Jornada a cielo abierto en la plaza Serrano."
            ),
            precio=0,
            fecha=fecha,
        )
        assert resultado["categoria"] == "Festivales"
        assert "al aire libre" in resultado["tags"]
        assert "fin de semana" in resultado["tags"]

    def test_titulo_y_descripcion_vacios(self):
        resultado = clasificar_evento("", "")
        assert resultado["categoria"] is None
        assert resultado["confianza"] == 0.0
        assert resultado["tags"] == []

    def test_solo_titulo_sin_descripcion(self):
        resultado = clasificar_evento("Concierto de Rock", "")
        assert resultado["categoria"] == "Música"

    def test_metodo_es_reglas_o_embeddings(self):
        resultado = clasificar_evento(
            "Función de teatro experimental",
            "Obra vanguardista con actores del elenco.",
        )
        assert resultado["metodo"] in ("reglas", "embeddings")

    def test_confianza_es_flotante_entre_0_y_1(self):
        resultado = clasificar_evento(
            "Recital de piano clásico",
            "Concierto con el pianista al frente de la orquesta.",
        )
        assert isinstance(resultado["confianza"], float)
        assert 0.0 <= resultado["confianza"] <= 1.0

    def test_tags_es_lista(self):
        resultado = clasificar_evento("Ballet Nacional", "Espectáculo de danza.")
        assert isinstance(resultado["tags"], list)

    def test_danza_tango_nocturno(self):
        """Milonga nocturna típica de Buenos Aires."""
        fecha = datetime(2024, 10, 5, 22, 0)  # sábado, 22h
        resultado = clasificar_evento(
            titulo="Gran Milonga en Salón Canning",
            descripcion=(
                "Noche de tango con orquesta en vivo. "
                "Bailarines y bailarinas de todas las edades. "
                "El mejor tango de Buenos Aires."
            ),
            fecha=fecha,
        )
        assert resultado["categoria"] == "Danza"
        assert resultado["subcategoria"] == "Tango"
        assert "nocturno" in resultado["tags"]
        assert "fin de semana" in resultado["tags"]

    def test_gastronomia_con_chef(self):
        resultado = clasificar_evento(
            titulo="Cena Maridaje con el Chef Germán Martitegui",
            descripcion=(
                "Menú de degustación en restaurante Tegui. "
                "El chef presenta platos con ingredientes de estación. "
                "Bar de vinos seleccionados."
            ),
            precio=12000.0,
        )
        assert resultado["categoria"] == "Gastronomía"
