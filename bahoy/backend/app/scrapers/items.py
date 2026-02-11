"""
Bahoy - Scrapy Items
Define la estructura de datos para los eventos scrapeados.
"""

import scrapy
from scrapy.item import Item, Field
from datetime import datetime
import hashlib


class EventItem(scrapy.Item):
    """
    Item de Scrapy que representa un evento.
    Define todos los campos que se extraerán de cada evento.
    """

    # Campos principales del evento
    title = Field()                    # Título del evento
    description = Field()              # Descripción completa del evento
    short_description = Field()        # Descripción corta (si existe)

    # Fechas y horarios
    start_date = Field()               # Fecha y hora de inicio (datetime)
    end_date = Field()                 # Fecha y hora de fin (datetime, opcional)
    date_text = Field()                # Texto original de la fecha

    # Ubicación
    venue_name = Field()               # Nombre del lugar
    venue_address = Field()            # Dirección completa
    neighborhood = Field()             # Barrio
    latitude = Field()                 # Latitud (opcional)
    longitude = Field()                # Longitud (opcional)

    # Categorización
    category = Field()                 # Categoría del evento
    tags = Field()                     # Lista de etiquetas/tags

    # Imagen y multimedia
    image_url = Field()                # URL de la imagen principal
    image_urls = Field()               # Lista de todas las imágenes
    images = Field()                   # Campo usado por ImagesPipeline de Scrapy

    # Precio
    price = Field()                    # Precio del evento
    is_free = Field()                  # Boolean: es gratuito o no

    # Metadata
    url = Field()                      # URL original del evento
    source = Field()                   # Fuente: "agenda_ba"
    event_hash = Field()               # Hash único para detectar duplicados
    scraped_at = Field()               # Timestamp del scraping

    # Campos adicionales
    contact_info = Field()             # Información de contacto
    booking_url = Field()              # URL para reservas/compras
    accessibility = Field()            # Información de accesibilidad
    age_restriction = Field()          # Restricción de edad


def generate_event_hash(title: str, start_date: str, venue_name: str) -> str:
    """
    Genera un hash único para un evento basado en título, fecha y lugar.

    Args:
        title: Título del evento
        start_date: Fecha de inicio (como string)
        venue_name: Nombre del lugar

    Returns:
        Hash MD5 del evento
    """
    # Normalizar los valores para el hash
    normalized_title = title.lower().strip()
    normalized_venue = venue_name.lower().strip() if venue_name else ""
    normalized_date = str(start_date)

    # Crear string único
    unique_string = f"{normalized_title}|{normalized_date}|{normalized_venue}"

    # Generar hash MD5
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()


def clean_text(text: str) -> str:
    """
    Limpia texto HTML y espacios en blanco.

    Args:
        text: Texto a limpiar

    Returns:
        Texto limpio
    """
    if not text:
        return ""

    # Eliminar tags HTML si existen
    import re
    text = re.sub(r'<[^>]+>', '', text)

    # Normalizar espacios en blanco
    text = ' '.join(text.split())

    return text.strip()
