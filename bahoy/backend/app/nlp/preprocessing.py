"""
Bahoy - Preprocesamiento de texto para eventos culturales en español.

Funciones para limpiar, normalizar, tokenizar, lematizar y extraer
entidades de textos provenientes de scrapers de eventos culturales.

Requiere:
    pip install spacy beautifulsoup4
    python -m spacy download es_core_news_lg
"""

import html
import re
import unicodedata
from typing import TypedDict

import spacy
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Carga lazy del modelo de spaCy
# ---------------------------------------------------------------------------
_nlp: spacy.language.Language | None = None


def _get_nlp() -> spacy.language.Language:
    """Carga el modelo de spaCy una sola vez (singleton)."""
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("es_core_news_lg")
    return _nlp


# ---------------------------------------------------------------------------
# Stopwords personalizadas para eventos culturales
# ---------------------------------------------------------------------------
# Palabras comunes sin valor semántico para el dominio de eventos.
# Se MANTIENEN: días de la semana, meses, horarios y palabras clave de eventos.
_STOPWORDS_CULTURALES: set[str] = {
    # Artículos
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    # Preposiciones
    "de", "del", "en", "a", "al", "con", "por", "para", "sin",
    "sobre", "entre", "desde", "hasta", "hacia", "ante",
    # Conjunciones
    "y", "o", "ni", "que", "pero", "sino", "como",
    # Pronombres
    "se", "su", "sus", "lo", "le", "les", "nos", "me", "te",
    # Verbos auxiliares / muy comunes
    "es", "son", "está", "ser", "estar", "hay", "fue", "ha", "sido",
    # Determinantes
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
    "más", "muy", "todo", "toda", "todos", "todas",
    # Otras
    "no", "ya", "así", "cada", "donde", "cuando", "también",
    "puede", "pueden", "otro", "otra", "otros", "otras",
}


# ---------------------------------------------------------------------------
# 1. Limpieza de HTML
# ---------------------------------------------------------------------------
def limpiar_html(texto: str) -> str:
    """
    Remueve tags HTML, decodifica entidades y normaliza espacios.

    Args:
        texto: Cadena con posible markup HTML.

    Returns:
        Texto plano limpio.

    Ejemplo:
        >>> limpiar_html("<p>Hola &amp; <b>mundo</b></p>")
        'Hola & mundo'
    """
    if not texto:
        return ""

    # Remover tags HTML con BeautifulSoup (maneja tags malformados)
    soup = BeautifulSoup(texto, "html.parser")
    texto_plano = soup.get_text(separator=" ")

    # Decodificar entidades HTML restantes (&amp; → &, &lt; → <, etc.)
    texto_plano = html.unescape(texto_plano)

    # Normalizar espacios: múltiples espacios/tabs/newlines → un solo espacio
    texto_plano = re.sub(r"\s+", " ", texto_plano).strip()

    return texto_plano


# ---------------------------------------------------------------------------
# 2. Normalización de texto
# ---------------------------------------------------------------------------
def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto en español: minúsculas, limpieza de caracteres especiales,
    manteniendo acentos y ñ.

    Args:
        texto: Texto a normalizar.

    Returns:
        Texto normalizado.

    Ejemplo:
        >>> normalizar_texto("¡¡Gran SHOW!! en el Teatro... @Colón  #2024")
        'gran show en el teatro colón 2024'
    """
    if not texto:
        return ""

    # Minúsculas
    texto = texto.lower()

    # Normalizar unicode a NFC (forma canónica compuesta) para que
    # los acentos se preserven como un solo codepoint.
    texto = unicodedata.normalize("NFC", texto)

    # Remover caracteres especiales innecesarios, MANTENIENDO:
    #   - letras (incluye acentos, ñ, ü gracias a \w con Unicode)
    #   - números
    #   - espacios
    #   - signos de moneda ($) para precios
    texto = re.sub(r"[^\w\s$]", " ", texto)

    # Normalizar espacios múltiples
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


# ---------------------------------------------------------------------------
# 3. Tokenización
# ---------------------------------------------------------------------------
def tokenizar(texto: str) -> list[str]:
    """
    Tokeniza texto en español usando spaCy (es_core_news_lg).
    Excluye signos de puntuación y espacios.

    Args:
        texto: Texto a tokenizar.

    Returns:
        Lista de tokens como strings.

    Ejemplo:
        >>> tokenizar("Gran show de Fito Páez en el Luna Park")
        ['Gran', 'show', 'de', 'Fito', 'Páez', 'en', 'el', 'Luna', 'Park']
    """
    if not texto:
        return []

    nlp = _get_nlp()
    doc = nlp(texto)

    return [
        token.text
        for token in doc
        if not token.is_punct and not token.is_space
    ]


# ---------------------------------------------------------------------------
# 4. Lematización
# ---------------------------------------------------------------------------
def lematizar(tokens: list[str]) -> list[str]:
    """
    Reduce palabras a su forma base (lema) usando spaCy.

    Args:
        tokens: Lista de tokens a lematizar.

    Returns:
        Lista de lemas.

    Ejemplo:
        >>> lematizar(["actuaciones", "musicales", "increíbles"])
        ['actuación', 'musical', 'increíble']
    """
    if not tokens:
        return []

    nlp = _get_nlp()
    # Unir tokens y procesar como texto para que spaCy aplique contexto
    doc = nlp(" ".join(tokens))

    return [
        token.lemma_
        for token in doc
        if not token.is_punct and not token.is_space
    ]


# ---------------------------------------------------------------------------
# 5. Remoción de stopwords
# ---------------------------------------------------------------------------
def remover_stopwords(tokens: list[str]) -> list[str]:
    """
    Remueve palabras vacías usando lista personalizada para eventos culturales.
    Mantiene días, meses, horarios y palabras clave del dominio.

    Args:
        tokens: Lista de tokens.

    Returns:
        Lista filtrada sin stopwords.

    Ejemplo:
        >>> remover_stopwords(["gran", "show", "de", "rock", "en", "el", "teatro"])
        ['gran', 'show', 'rock', 'teatro']
    """
    if not tokens:
        return []

    return [t for t in tokens if t.lower() not in _STOPWORDS_CULTURALES]


# ---------------------------------------------------------------------------
# 6. Extracción de entidades (NER)
# ---------------------------------------------------------------------------

class Entidades(TypedDict):
    personas: list[str]
    lugares: list[str]
    organizaciones: list[str]
    fechas: list[str]
    precios: list[str]


def extraer_entidades(texto: str) -> Entidades:
    """
    Extrae entidades nombradas del texto usando el NER de spaCy.
    Identifica personas, lugares, organizaciones, fechas y precios.

    Args:
        texto: Texto del cual extraer entidades.

    Returns:
        Diccionario con listas de entidades por tipo.

    Ejemplo:
        >>> extraer_entidades("Show de Fito Páez en Luna Park el 15 de marzo, $5000")
        {
            'personas': ['Fito Páez'],
            'lugares': ['Luna Park'],
            'organizaciones': [],
            'fechas': ['15 de marzo'],
            'precios': ['$5000']
        }
    """
    if not texto:
        return Entidades(
            personas=[], lugares=[], organizaciones=[], fechas=[], precios=[]
        )

    nlp = _get_nlp()
    doc = nlp(texto)

    # Mapeo de etiquetas spaCy → nuestras categorías
    label_map: dict[str, str] = {
        "PER": "personas",
        "LOC": "lugares",
        "ORG": "organizaciones",
        "DATE": "fechas",
        "MONEY": "precios",
    }

    entidades: Entidades = {
        "personas": [],
        "lugares": [],
        "organizaciones": [],
        "fechas": [],
        "precios": [],
    }

    seen: set[str] = set()
    for ent in doc.ents:
        key = label_map.get(ent.label_)
        if key and ent.text not in seen:
            seen.add(ent.text)
            entidades[key].append(ent.text)

    # Extraer precios con regex como fallback (spaCy puede no detectar $5000)
    precios_regex = re.findall(r"\$\s?[\d.,]+", texto)
    for precio in precios_regex:
        precio_limpio = precio.replace(" ", "")
        if precio_limpio not in seen:
            seen.add(precio_limpio)
            entidades["precios"].append(precio_limpio)

    return entidades


# ---------------------------------------------------------------------------
# Pipeline completo: procesar_evento
# ---------------------------------------------------------------------------

class ResultadoProcesamiento(TypedDict):
    texto_limpio: str
    tokens: list[str]
    lemas: list[str]
    entidades: Entidades


def procesar_evento(texto: str) -> ResultadoProcesamiento:
    """
    Pipeline completo de procesamiento de texto para un evento cultural.

    Ejecuta en orden:
        1. Limpiar HTML
        2. Extraer entidades (sobre texto limpio, antes de normalizar)
        3. Normalizar texto
        4. Tokenizar
        5. Remover stopwords
        6. Lematizar

    Args:
        texto: Texto crudo (puede contener HTML) del evento.

    Returns:
        Diccionario con texto limpio, tokens filtrados, lemas y entidades.

    Ejemplo:
        >>> procesar_evento("<p>Gran show de <b>Fito Páez</b> en el Luna Park, $5000</p>")
        {
            'texto_limpio': 'gran show de fito páez en el luna park $5000',
            'tokens': ['gran', 'show', 'fito', 'páez', 'luna', 'park', '$5000'],
            'lemas': ['gran', 'show', 'fito', 'páez', 'luna', 'park', '$5000'],
            'entidades': {
                'personas': ['Fito Páez'],
                'lugares': ['Luna Park'],
                'organizaciones': [],
                'fechas': [],
                'precios': ['$5000']
            }
        }
    """
    # 1. Limpiar HTML
    texto_sin_html = limpiar_html(texto)

    # 2. Extraer entidades ANTES de normalizar (para preservar mayúsculas)
    entidades = extraer_entidades(texto_sin_html)

    # 3. Normalizar
    texto_normalizado = normalizar_texto(texto_sin_html)

    # 4. Tokenizar
    tokens_raw = tokenizar(texto_normalizado)

    # 5. Remover stopwords
    tokens_filtrados = remover_stopwords(tokens_raw)

    # 6. Lematizar
    lemas = lematizar(tokens_filtrados)

    return ResultadoProcesamiento(
        texto_limpio=texto_normalizado,
        tokens=tokens_filtrados,
        lemas=lemas,
        entidades=entidades,
    )
