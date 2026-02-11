"""
Bahoy - Spider para Agenda Buenos Aires
Scraper para https://turismo.buenosaires.gob.ar/es/agenda

Este spider navega por la agenda de eventos de Buenos Aires,
extrae información de cada evento y la guarda en la base de datos.
"""

import scrapy
from scrapy.http import Response
from datetime import datetime
import re
import logging
from typing import Generator, Optional
from .items import EventItem, generate_event_hash, clean_text


class AgendaBaSpider(scrapy.Spider):
    """
    Spider para extraer eventos de la Agenda de Buenos Aires.
    """

    name = 'agenda_ba'
    allowed_domains = ['turismo.buenosaires.gob.ar']
    start_urls = ['https://turismo.buenosaires.gob.ar/es/agenda']

    # Configuración del spider
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # 2 segundos entre requests
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,  # Una request a la vez
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'BahoyBot/1.0 (+https://bahoy.com.ar; info@bahoy.com.ar)',
    }

    # Mapeo de categorías del sitio a nuestras categorías
    CATEGORY_MAPPING = {
        'musica': 'music',
        'teatro': 'theater',
        'arte': 'art',
        'danza': 'dance',
        'cine': 'cinema',
        'feria': 'fair',
        'gastronomia': 'food',
        'deporte': 'sports',
        'infantil': 'kids',
        'tango': 'tango',
        'festival': 'festival',
        'exposicion': 'exhibition',
        'curso': 'workshop',
        'recital': 'music',
        'concierto': 'music',
    }

    def __init__(self, *args, **kwargs):
        super(AgendaBaSpider, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        self.events_scraped = 0
        self.errors = 0

    def parse(self, response: Response) -> Generator:
        """
        Parsea la página principal de la agenda y extrae enlaces a eventos.

        Args:
            response: Respuesta HTTP de la página de agenda

        Yields:
            Requests a páginas de eventos individuales
        """
        self.logger.info(f"Parseando página de agenda: {response.url}")

        # Seleccionar todos los eventos de la página
        # Ajustar selectores según la estructura real del sitio
        event_links = response.css('article.event a::attr(href)').getall()

        if not event_links:
            # Intentar selectores alternativos
            event_links = response.css('.event-item a::attr(href)').getall()

        if not event_links:
            event_links = response.css('.agenda-item a::attr(href)').getall()

        if not event_links:
            self.logger.warning(f"No se encontraron eventos en {response.url}")
            self.logger.debug(f"HTML de la página: {response.text[:500]}")
        else:
            self.logger.info(f"Encontrados {len(event_links)} enlaces a eventos")

        # Seguir cada enlace de evento
        for link in event_links:
            # Construir URL completa si es relativa
            full_url = response.urljoin(link)
            self.logger.debug(f"Siguiendo enlace: {full_url}")

            yield scrapy.Request(
                url=full_url,
                callback=self.parse_event,
                errback=self.handle_error
            )

        # Paginación: buscar enlace a siguiente página
        next_page = response.css('a.next::attr(href)').get()
        if not next_page:
            next_page = response.css('a[rel="next"]::attr(href)').get()
        if not next_page:
            next_page = response.css('.pagination a:contains("Siguiente")::attr(href)').get()

        if next_page:
            self.logger.info(f"Encontrada página siguiente: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_event(self, response: Response) -> EventItem:
        """
        Parsea la página de un evento individual y extrae toda la información.

        Args:
            response: Respuesta HTTP de la página del evento

        Returns:
            EventItem con la información del evento
        """
        self.logger.info(f"Parseando evento: {response.url}")

        try:
            item = EventItem()

            # Información básica
            item['url'] = response.url
            item['source'] = 'agenda_ba'
            item['scraped_at'] = datetime.now()

            # Título - intentar diferentes selectores
            title = self.extract_title(response)
            if not title:
                self.logger.warning(f"No se encontró título en {response.url}")
                return None
            item['title'] = clean_text(title)

            # Descripción
            item['description'] = self.extract_description(response)
            item['short_description'] = self.extract_short_description(response)

            # Fechas
            date_info = self.extract_dates(response)
            item['start_date'] = date_info['start_date']
            item['end_date'] = date_info['end_date']
            item['date_text'] = date_info['date_text']

            # Ubicación
            location_info = self.extract_location(response)
            item['venue_name'] = location_info['venue_name']
            item['venue_address'] = location_info['venue_address']
            item['neighborhood'] = location_info['neighborhood']

            # Categoría
            item['category'] = self.extract_category(response)
            item['tags'] = self.extract_tags(response)

            # Imagen
            item['image_url'] = self.extract_image(response)

            # Precio
            price_info = self.extract_price(response)
            item['price'] = price_info['price']
            item['is_free'] = price_info['is_free']

            # Información adicional
            item['contact_info'] = self.extract_contact(response)
            item['booking_url'] = self.extract_booking_url(response)

            # Generar hash único
            item['event_hash'] = generate_event_hash(
                item['title'],
                str(item['start_date']),
                item['venue_name'] or ''
            )

            self.events_scraped += 1
            self.logger.info(f"Evento scrapeado exitosamente: {item['title']}")

            return item

        except Exception as e:
            self.logger.error(f"Error parseando evento {response.url}: {str(e)}", exc_info=True)
            self.errors += 1
            return None

    def extract_title(self, response: Response) -> Optional[str]:
        """Extrae el título del evento."""
        title = response.css('h1.event-title::text').get()
        if not title:
            title = response.css('h1::text').get()
        if not title:
            title = response.css('.event-header h1::text').get()
        return title

    def extract_description(self, response: Response) -> str:
        """Extrae la descripción completa del evento."""
        # Intentar diferentes selectores
        desc = response.css('.event-description::text').getall()
        if not desc:
            desc = response.css('.descripcion::text').getall()
        if not desc:
            desc = response.css('article p::text').getall()

        description = ' '.join(desc) if desc else ''
        return clean_text(description)

    def extract_short_description(self, response: Response) -> str:
        """Extrae la descripción corta del evento."""
        short = response.css('.event-summary::text').get()
        if not short:
            short = response.css('.resumen::text').get()
        return clean_text(short) if short else ''

    def extract_dates(self, response: Response) -> dict:
        """
        Extrae y parsea las fechas del evento.

        Returns:
            dict con start_date, end_date, date_text
        """
        date_text = response.css('.event-date::text').get()
        if not date_text:
            date_text = response.css('.fecha::text').get()
        if not date_text:
            date_text = response.css('time::text').get()

        # Intentar parsear la fecha
        start_date = None
        end_date = None

        if date_text:
            start_date = self.parse_date(date_text)

        return {
            'start_date': start_date,
            'end_date': end_date,
            'date_text': date_text or ''
        }

    def parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parsea un string de fecha en español a objeto datetime.

        Args:
            date_text: Texto con la fecha en español

        Returns:
            Objeto datetime o None si no se puede parsear
        """
        if not date_text:
            return None

        # Limpiar el texto
        date_text = date_text.lower().strip()

        # Mapeo de meses en español
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        try:
            # Patrón: "15 de marzo de 2024" o "15 de marzo, 20:00"
            pattern = r'(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?'
            match = re.search(pattern, date_text)

            if match:
                day = int(match.group(1))
                month_name = match.group(2)
                year = int(match.group(3)) if match.group(3) else datetime.now().year

                month = months.get(month_name)
                if month:
                    # Buscar hora si existe
                    time_pattern = r'(\d{1,2}):(\d{2})'
                    time_match = re.search(time_pattern, date_text)

                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2))
                        return datetime(year, month, day, hour, minute)
                    else:
                        return datetime(year, month, day)

        except Exception as e:
            self.logger.warning(f"Error parseando fecha '{date_text}': {str(e)}")

        return None

    def extract_location(self, response: Response) -> dict:
        """Extrae información de ubicación del evento."""
        venue_name = response.css('.event-venue::text').get()
        if not venue_name:
            venue_name = response.css('.lugar::text').get()

        address = response.css('.event-address::text').get()
        if not address:
            address = response.css('.direccion::text').get()

        neighborhood = response.css('.event-neighborhood::text').get()
        if not neighborhood:
            neighborhood = response.css('.barrio::text').get()

        return {
            'venue_name': clean_text(venue_name) if venue_name else '',
            'venue_address': clean_text(address) if address else '',
            'neighborhood': clean_text(neighborhood) if neighborhood else ''
        }

    def extract_category(self, response: Response) -> str:
        """Extrae y mapea la categoría del evento."""
        category = response.css('.event-category::text').get()
        if not category:
            category = response.css('.categoria::text').get()
        if not category:
            # Intentar extraer de la URL o breadcrumbs
            breadcrumbs = response.css('.breadcrumb a::text').getall()
            if breadcrumbs:
                category = breadcrumbs[-1]

        if category:
            category_clean = category.lower().strip()
            # Mapear a nuestras categorías
            for key, value in self.CATEGORY_MAPPING.items():
                if key in category_clean:
                    return value

        return 'other'

    def extract_tags(self, response: Response) -> list:
        """Extrae tags/etiquetas del evento."""
        tags = response.css('.event-tag::text').getall()
        if not tags:
            tags = response.css('.tag::text').getall()

        return [clean_text(tag) for tag in tags if tag]

    def extract_image(self, response: Response) -> Optional[str]:
        """Extrae la URL de la imagen principal del evento."""
        image = response.css('.event-image img::attr(src)').get()
        if not image:
            image = response.css('article img::attr(src)').get()
        if not image:
            image = response.css('img[itemprop="image"]::attr(src)').get()

        if image:
            return response.urljoin(image)

        return None

    def extract_price(self, response: Response) -> dict:
        """Extrae información de precio del evento."""
        price_text = response.css('.event-price::text').get()
        if not price_text:
            price_text = response.css('.precio::text').get()

        is_free = False
        price = None

        if price_text:
            price_text_lower = price_text.lower()
            if 'gratis' in price_text_lower or 'gratuito' in price_text_lower:
                is_free = True
            else:
                # Intentar extraer precio numérico
                price_match = re.search(r'\$?\s*(\d+(?:[.,]\d+)?)', price_text)
                if price_match:
                    price = float(price_match.group(1).replace(',', '.'))

        return {
            'price': price,
            'is_free': is_free
        }

    def extract_contact(self, response: Response) -> str:
        """Extrae información de contacto."""
        contact = response.css('.event-contact::text').get()
        if not contact:
            contact = response.css('.contacto::text').get()

        return clean_text(contact) if contact else ''

    def extract_booking_url(self, response: Response) -> Optional[str]:
        """Extrae URL de reserva/compra."""
        booking = response.css('a.event-booking::attr(href)').get()
        if not booking:
            booking = response.css('a:contains("Comprar")::attr(href)').get()
        if not booking:
            booking = response.css('a:contains("Reservar")::attr(href)').get()

        if booking:
            return response.urljoin(booking)

        return None

    def handle_error(self, failure):
        """Maneja errores durante el scraping."""
        self.logger.error(f"Error en request: {failure.request.url}")
        self.logger.error(f"Tipo de error: {failure.type}")
        self.logger.error(f"Detalle: {failure.value}")
        self.errors += 1

    def closed(self, reason):
        """Se ejecuta cuando el spider termina."""
        self.logger.info(f"Spider cerrado. Razón: {reason}")
        self.logger.info(f"Total eventos scrapeados: {self.events_scraped}")
        self.logger.info(f"Total errores: {self.errors}")
