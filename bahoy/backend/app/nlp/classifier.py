"""
Bahoy - Clasificador de Eventos Culturales

Sistema de clasificación en dos capas:
  - Capa 1: Reglas basadas en palabras clave (rápido y confiable).
  - Capa 2: Embeddings semánticos con sentence-transformers
    (fallback cuando las reglas no son suficientemente claras).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# CAPA 1 – Palabras clave por categoría
# ---------------------------------------------------------------------------

CATEGORIAS_KEYWORDS: dict[str, list[str]] = {
    "Teatro": [
        "obra", "función", "actor", "actriz", "elenco", "teatro", "escena",
        "dramaturgia", "puesta", "monólogo", "tragicomedia",
    ],
    "Música": [
        "recital", "concierto", "show", "banda", "cantante", "música",
        "orquesta", "jazz", "rock", "folklore", "tango", "ópera",
    ],
    "Exposiciones": [
        "muestra", "exposición", "galería", "museo", "arte",
        "fotografía", "pintura", "escultura", "instalación",
    ],
    "Gastronomía": [
        "restaurante", "bar", "café", "menú", "chef", "degustación",
        "maridaje", "brunch", "cocina", "gastronomía",
    ],
    "Cine": [
        "película", "film", "cine", "director", "proyección",
        "documental", "cortometraje", "cineforum", "cinematografía",
    ],
    "Danza": [
        "ballet", "tango", "danza", "coreografía", "bailarín",
        "bailarina", "bailarines", "bailarinas", "milonga", "flamenco",
    ],
    "Talleres": [
        "taller", "workshop", "curso", "clase", "aprender",
        "capacitación", "seminario", "formación",
    ],
    "Festivales": [
        "festival", "feria", "jornada", "fiesta popular",
        "encuentro", "muestra festival",
    ],
}

# ---------------------------------------------------------------------------
# CAPA 2 – Descripciones canónicas para comparación por embeddings
# ---------------------------------------------------------------------------

DESCRIPCIONES_TIPICAS: dict[str, str] = {
    "Teatro": (
        "obra teatral con actores en escena, función de teatro, elenco, "
        "dramaturgia, puesta en escena, representación teatral, drama, comedia, musical"
    ),
    "Música": (
        "concierto de música en vivo, recital, banda en vivo, cantante, "
        "festival musical, show musical, orquesta, jazz, rock, folklore, tango"
    ),
    "Exposiciones": (
        "exposición de arte en galería, muestra fotográfica, instalación artística, "
        "museo, obra plástica, pintura, escultura, arte contemporáneo"
    ),
    "Gastronomía": (
        "degustación gastronómica, menú especial, chef reconocido, maridaje de vinos, "
        "brunch, cocina de autor, restaurante, experiencia culinaria"
    ),
    "Cine": (
        "proyección de película, estreno cinematográfico, film, documental, cortometraje, "
        "director de cine, cineforum, ciclo de cine"
    ),
    "Danza": (
        "espectáculo de danza, ballet clásico, tango milonga, coreografía, bailarines, "
        "flamenco, danza contemporánea, folclore danza"
    ),
    "Talleres": (
        "taller participativo, workshop, curso de aprendizaje, clase práctica, "
        "capacitación, formación, seminario, aprender nuevas habilidades"
    ),
    "Festivales": (
        "festival multidisciplinario, feria cultural, jornada de actividades, "
        "encuentro artístico, fiesta popular, evento masivo al aire libre"
    ),
}

# ---------------------------------------------------------------------------
# Subcategorías por categoría
# ---------------------------------------------------------------------------

SUBCATEGORIAS_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "Teatro": {
        "Comedia":      ["comedia", "humor", "cómic", "gracioso", "risas"],
        "Drama":        ["drama", "dramático", "tragedia", "oscuro", "intenso"],
        "Musical":      ["musical", "canto", "voces", "canciones"],
        "Infantil":     ["infantil", "niños", "chicos", "kids", "familiar"],
        "Experimental": ["experimental", "vanguardia", "contemporáneo", "performático"],
    },
    "Música": {
        "Jazz":         ["jazz"],
        "Rock":         ["rock", "metal", "punk", "indie rock"],
        "Clásica":      ["clásica", "orquesta", "sinfónica", "ópera", "camerata"],
        "Folclórica":   ["folklore", "folclórica", "zamba", "chacarera", "cuarteto"],
        "Electrónica":  ["electrónica", "dj", "techno", "house", "beats"],
        "Pop":          ["pop", "indie pop"],
        "Tango":        ["tango", "milonga", "bandoneón"],
    },
    "Exposiciones": {
        "Fotografía":          ["fotografía", "foto", "imagen", "fotógrafo"],
        "Pintura":             ["pintura", "cuadros", "óleo", "acuarela"],
        "Escultura":           ["escultura", "instalación"],
        "Arte Contemporáneo":  ["contemporáneo", "moderno", "digital", "multimedia"],
    },
    "Gastronomía": {
        "Degustación":  ["degustación", "cata", "maridaje"],
        "Brunch":       ["brunch", "desayuno"],
        "Cocina":       ["clase de cocina", "taller gastronómico", "recetas"],
    },
    "Cine": {
        "Documental":  ["documental"],
        "Drama":       ["drama", "dramático"],
        "Comedia":     ["comedia"],
        "Animación":   ["animación", "animada", "cartoon"],
        "Terror":      ["terror", "horror", "suspenso"],
    },
    "Danza": {
        "Ballet":       ["ballet", "clásico"],
        "Tango":        ["tango", "milonga"],
        "Contemporánea": ["contemporánea", "moderna"],
        "Folclórica":   ["folclore", "folklore", "malambo"],
        "Flamenco":     ["flamenco"],
    },
    "Talleres": {
        "Arte":         ["pintura", "dibujo", "escultura", "cerámica"],
        "Cocina":       ["cocina", "gastronomía", "repostería"],
        "Tecnología":   ["programación", "diseño digital", "fotografía"],
        "Escritura":    ["escritura", "poesía", "literatura"],
    },
    "Festivales": {
        "Arte":         ["arte", "artístico"],
        "Música":       ["música", "musical"],
        "Gastronomía":  ["gastronomía", "comida", "food"],
        "Cine":         ["cine", "film", "película"],
    },
}

# ---------------------------------------------------------------------------
# Singleton del modelo de embeddings (carga perezosa)
# ---------------------------------------------------------------------------

_modelo_embeddings = None


def _get_modelo():
    """Carga el modelo de sentence-transformers una única vez (lazy singleton)."""
    global _modelo_embeddings
    if _modelo_embeddings is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        _modelo_embeddings = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )
    return _modelo_embeddings


# ---------------------------------------------------------------------------
# Capa 1: Clasificación por reglas
# ---------------------------------------------------------------------------

def _normalizar_texto(texto: str) -> str:
    """Convierte a minúsculas, elimina puntuación y normaliza espacios."""
    texto = texto.lower()
    texto = re.sub(r"[^\w\sáéíóúüñ]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _clasificar_por_reglas(titulo: str, descripcion: str) -> Optional[dict]:
    """
    Capa 1 – Clasifica usando palabras clave.

    Retorna un dict con categoría, confianza y método, o None si la señal
    es demasiado débil o ambigua para confiar en las reglas.
    """
    texto = _normalizar_texto(titulo + " " + descripcion)

    scores: dict[str, int] = {}
    for categoria, keywords in CATEGORIAS_KEYWORDS.items():
        count = sum(
            1 for kw in keywords
            if re.search(r"\b" + re.escape(kw) + r"\b", texto)
        )
        if count > 0:
            scores[categoria] = count

    if not scores:
        return None

    # Ordenar por puntaje descendente
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    mejor_cat, mejor_score = ranking[0]

    # Considerar ambigüedad: si hay empate en el primer puesto → embeddings
    if len(ranking) >= 2 and ranking[1][1] == mejor_score:
        return None

    # Confianza basada en número de palabras clave encontradas
    # mínimo 0.35 con 1 match, sube ~0.15 por cada match adicional
    confianza = min(0.95, 0.35 + 0.15 * (mejor_score - 1))

    # Si la confianza es muy baja, preferimos embeddings
    if confianza < 0.35:
        return None

    return {
        "categoria": mejor_cat,
        "confianza": round(confianza, 2),
        "metodo": "reglas",
    }


# ---------------------------------------------------------------------------
# Capa 2: Clasificación por embeddings
# ---------------------------------------------------------------------------

def _similitud_coseno(vec_a, vec_b) -> float:
    """Similitud coseno entre dos vectores numpy."""
    import numpy as np  # noqa: PLC0415

    norma_a = np.linalg.norm(vec_a)
    norma_b = np.linalg.norm(vec_b)
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norma_a * norma_b))


def _clasificar_por_embeddings(titulo: str, descripcion: str) -> dict:
    """
    Capa 2 – Clasifica usando similitud semántica con sentence-transformers.

    Siempre devuelve un resultado (fallback definitivo).
    """
    modelo = _get_modelo()
    texto_evento = titulo + " " + descripcion

    embedding_evento = modelo.encode(texto_evento)

    mejor_cat = "Festivales"  # fallback por defecto
    mejor_similitud = -1.0

    for categoria, descripcion_tipica in DESCRIPCIONES_TIPICAS.items():
        embedding_cat = modelo.encode(descripcion_tipica)
        sim = _similitud_coseno(embedding_evento, embedding_cat)
        if sim > mejor_similitud:
            mejor_similitud = sim
            mejor_cat = categoria

    return {
        "categoria": mejor_cat,
        "confianza": round(max(0.0, min(1.0, mejor_similitud)), 2),
        "metodo": "embeddings",
    }


# ---------------------------------------------------------------------------
# Detección de subcategoría
# ---------------------------------------------------------------------------

def _detectar_subcategoria(titulo: str, descripcion: str, categoria: str) -> Optional[str]:
    """
    Detecta la subcategoría más específica dentro de la categoría dada.
    Retorna None si no puede determinarse con certeza.
    """
    if categoria not in SUBCATEGORIAS_KEYWORDS:
        return None

    texto = _normalizar_texto(titulo + " " + descripcion)
    subcats = SUBCATEGORIAS_KEYWORDS[categoria]

    for subcat, keywords in subcats.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", texto) for kw in keywords):
            return subcat

    return None


# ---------------------------------------------------------------------------
# Generación automática de tags
# ---------------------------------------------------------------------------

def _generar_tags(
    titulo: str,
    descripcion: str,
    precio: Optional[float] = None,
    fecha: Optional[datetime] = None,
) -> list[str]:
    """
    Genera tags automáticos basados en el contenido del evento y sus metadatos.

    Tags detectados:
      - "gratuito"       → precio == 0 o texto menciona "gratis", "entrada libre"
      - "familiar"       → menciona "niños", "familia", "todas las edades"
      - "al aire libre"  → menciona "plaza", "parque", "aire libre"
      - "nocturno"       → fecha con horario >= 20:00
      - "fin de semana"  → sábado (5) o domingo (6)
    """
    texto = _normalizar_texto(titulo + " " + descripcion)
    tags: list[str] = []

    def _en_texto(kw: str) -> bool:
        return bool(re.search(r"\b" + re.escape(kw) + r"\b", texto))

    # Gratuito
    es_gratis_por_precio = precio is not None and precio == 0
    es_gratis_por_texto = any(
        _en_texto(kw)
        for kw in ["gratis", "gratuito", "entrada libre", "entrada gratis", "sin costo", "free"]
    )
    if es_gratis_por_precio or es_gratis_por_texto:
        tags.append("gratuito")

    # Familiar
    if any(
        _en_texto(kw)
        for kw in ["niños", "niñas", "familia", "familiar", "todas las edades", "para chicos", "infantil"]
    ):
        tags.append("familiar")

    # Al aire libre
    if any(
        _en_texto(kw)
        for kw in ["plaza", "parque", "aire libre", "al aire", "exterior", "outdoor", "espacio abierto"]
    ):
        tags.append("al aire libre")

    # Nocturno (horario >= 20:00)
    if fecha is not None and fecha.hour >= 20:
        tags.append("nocturno")

    # Fin de semana (sábado=5, domingo=6)
    if fecha is not None and fecha.weekday() in (5, 6):
        tags.append("fin de semana")

    return tags


# ---------------------------------------------------------------------------
# Función principal pública
# ---------------------------------------------------------------------------

def clasificar_evento(
    titulo: str,
    descripcion: str,
    precio: Optional[float] = None,
    fecha: Optional[datetime] = None,
) -> dict:
    """
    Clasifica un evento cultural en dos capas y genera sus tags automáticos.

    Parámetros
    ----------
    titulo       : Título del evento.
    descripcion  : Descripción completa del evento.
    precio       : Precio mínimo de entrada (None si desconocido, 0 si gratuito).
    fecha        : Fecha y hora de inicio del evento (para tags de horario/día).

    Retorna
    -------
    dict con:
        - "categoria"    : str  – categoría principal (ej. "Teatro")
        - "subcategoria" : str | None – subcategoría específica (ej. "Comedia")
        - "confianza"    : float – score entre 0 y 1
        - "metodo"       : str  – "reglas" o "embeddings"
        - "tags"         : list[str] – etiquetas automáticas generadas
    """
    if not titulo and not descripcion:
        return {
            "categoria": None,
            "subcategoria": None,
            "confianza": 0.0,
            "metodo": "reglas",
            "tags": [],
        }

    descripcion = descripcion or ""

    # Capa 1: reglas
    resultado = _clasificar_por_reglas(titulo, descripcion)

    # Capa 2: embeddings como fallback
    if resultado is None:
        resultado = _clasificar_por_embeddings(titulo, descripcion)

    categoria = resultado["categoria"]

    # Subcategoría
    subcategoria = _detectar_subcategoria(titulo, descripcion, categoria)

    # Tags automáticos
    tags = _generar_tags(titulo, descripcion, precio, fecha)

    return {
        "categoria": categoria,
        "subcategoria": subcategoria,
        "confianza": resultado["confianza"],
        "metodo": resultado["metodo"],
        "tags": tags,
    }
