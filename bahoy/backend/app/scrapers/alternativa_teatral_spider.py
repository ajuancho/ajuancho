"""
Bahoy - Spider para Alternativa Teatral
Scraper para https://www.alternativateatral.com/

Este spider navega por la cartelera de teatro de Alternativa Teatral,
extrae información detallada de cada obra y la guarda en la base de datos.
"""

import scrapy
from scrapy.http import Response
from datetime import datetime
import re
import logging
from typing import Generator, Optional, List
from .items import EventItem, generate_event_hash, clean_text


class AlternativaTeatralSpider(scrapy.Spider):
    """
    Spider para extraer obras de teatro de Alternativa Teatral.
    """

    name = 'alternativa_teatral'
    allowed_domains = ['alternativateatral.com']
    start_urls = ['https://www.alternativateatral.com/cartelera']

    # Configuración del spider
    custom_settings = {
        'DOWNLOAD_DELAY': 3,  # 3 segundos entre requests para evitar bloqueos
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,  # Una request a la vez
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        },
    }

    # Mapeo de géneros teatrales a subcategorías
    GENRE_MAPPING = {
        'comedia': 'comedy',
        'drama': 'drama',
        'musical': 'musical',
        'infantil': 'kids',
        'unipersonal': 'one_person_show',
        'stand-up': 'stand_up',
        'teatro musical': 'musical',
        'comedia musical': 'musical_comedy',
        'drama histórico': 'historical_drama',
        'tragedia': 'tragedy',
        'teatro experimental': 'experimental',
        'teatro físico': 'physical_theater',
        'clown': 'clown',
        'títeres': 'puppets',
        'danza teatro': 'dance_theater',
        'cabaret': 'cabaret',
        'mimo': 'mime',
        'teatro de sombras': 'shadow_theater',
    }

    def __init__(self, *args, **kwargs):
        super(AlternativaTeatralSpider, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        self.events_scraped = 0
        self.errors = 0

    def parse(self, response: Response) -> Generator:
        """
        Parsea la página principal de cartelera y extrae enlaces a obras.

        Args:
            response: Respuesta HTTP de la página de cartelera

        Yields:
            Requests a páginas de obras individuales
        """
        self.logger.info(f"Parseando página de cartelera: {response.url}")

        # Selectores para enlaces a obras - múltiples opciones
        # Alternativa Teatral generalmente usa una estructura de cards
        event_links = response.css('article.obra a.obra-link::attr(href)').getall()

        if not event_links:
            # Intentar selectores alternativos comunes
            event_links = response.css('.obra-card a::attr(href)').getall()

        if not event_links:
            event_links = response.css('.cartelera-item a::attr(href)').getall()

        if not event_links:
            event_links = response.css('a[href*="/obra/"]::attr(href)').getall()

        if not event_links:
            # Último intento: buscar todos los links que contengan patrones de obra
            all_links = response.css('a::attr(href)').getall()
            event_links = [link for link in all_links if '/obra' in link or '/obras' in link]

        if not event_links:
            self.logger.warning(f"No se encontraron obras en {response.url}")
            self.logger.debug(f"HTML de la página (primeros 500 caracteres): {response.text[:500]}")
        else:
            self.logger.info(f"Encontrados {len(event_links)} enlaces a obras")

        # Seguir cada enlace de obra
        seen_urls = set()
        for link in event_links:
            # Construir URL completa si es relativa
            full_url = response.urljoin(link)

            # Evitar duplicados en la misma página
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            self.logger.debug(f"Siguiendo enlace: {full_url}")

            yield scrapy.Request(
                url=full_url,
                callback=self.parse_obra,
                errback=self.handle_error
            )

        # Paginación: buscar enlace a siguiente página
        next_page = response.css('a.next::attr(href)').get()
        if not next_page:
            next_page = response.css('a[rel="next"]::attr(href)').get()
        if not next_page:
            next_page = response.css('.pagination a:contains("Siguiente")::attr(href)').get()
        if not next_page:
            next_page = response.css('a:contains("›")::attr(href)').get()

        if next_page:
            self.logger.info(f"Encontrada página siguiente: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_obra(self, response: Response) -> EventItem:
        """
        Parsea la página de una obra de teatro individual y extrae toda la información.

        Args:
            response: Respuesta HTTP de la página de la obra

        Returns:
            EventItem con la información de la obra
        """
        self.logger.info(f"Parseando obra: {response.url}")

        try:
            item = EventItem()

            # Información básica
            item['url'] = response.url
            item['source'] = 'alternativa_teatral'
            item['scraped_at'] = datetime.now()

            # Título de la obra
            title = self.extract_title(response)
            if not title:
                self.logger.warning(f"No se encontró título en {response.url}")
                return None
            item['title'] = clean_text(title)

            # Sinopsis (descripción)
            item['description'] = self.extract_description(response)
            item['short_description'] = self.extract_short_description(response)

            # Elenco (como tags)
            cast = self.extract_cast(response)
            tags = cast.copy()  # El elenco va como tags

            # Director
            director = self.extract_director(response)
            if director:
                tags.append(f"Director: {director}")

            # Género teatral (para tags y subcategoría)
            genre = self.extract_genre(response)
            if genre:
                tags.append(f"Género: {genre}")

            # Duración
            duration = self.extract_duration(response)
            if duration:
                tags.append(f"Duración: {duration}")

            item['tags'] = tags

            # Categoría: siempre "theater" (Teatro)
            item['category'] = 'theater'

            # Funciones (fechas y horarios)
            functions_info = self.extract_functions(response)
            item['start_date'] = functions_info['start_date']
            item['end_date'] = functions_info['end_date']
            item['date_text'] = functions_info['date_text']

            # Sala/Teatro (ubicación)
            location_info = self.extract_location(response)
            item['venue_name'] = location_info['venue_name']
            item['venue_address'] = location_info['venue_address']
            item['neighborhood'] = location_info['neighborhood']

            # Precio
            price_info = self.extract_price(response)
            item['price'] = price_info['price']
            item['is_free'] = price_info['is_free']

            # Imágenes
            item['image_url'] = self.extract_image(response)

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
            self.logger.info(f"Obra scrapeada exitosamente: {item['title']}")

            return item

        except Exception as e:
            self.logger.error(f"Error parseando obra {response.url}: {str(e)}", exc_info=True)
            self.errors += 1
            return None

    def extract_title(self, response: Response) -> Optional[str]:
        """Extrae el título de la obra."""
        title = response.css('h1.obra-title::text').get()
        if not title:
            title = response.css('h1.title::text').get()
        if not title:
            title = response.css('h1::text').get()
        if not title:
            title = response.css('.obra-header h1::text').get()
        if not title:
            # Alternativa Teatral a veces usa meta tags
            title = response.css('meta[property="og:title"]::attr(content)').get()
        return title

    def extract_description(self, response: Response) -> str:
        """Extrae la sinopsis completa de la obra."""
        # Intentar diferentes selectores
        desc = response.css('.obra-descripcion::text, .obra-descripcion p::text').getall()
        if not desc:
            desc = response.css('.sinopsis::text, .sinopsis p::text').getall()
        if not desc:
            desc = response.css('.descripcion::text, .descripcion p::text').getall()
        if not desc:
            desc = response.css('div[itemprop="description"]::text').getall()
        if not desc:
            desc = response.css('.obra-content p::text').getall()

        description = ' '.join(desc) if desc else ''
        return clean_text(description)

    def extract_short_description(self, response: Response) -> str:
        """Extrae la descripción corta de la obra."""
        short = response.css('.obra-resumen::text').get()
        if not short:
            short = response.css('.resumen::text').get()
        if not short:
            short = response.css('meta[name="description"]::attr(content)').get()
        return clean_text(short) if short else ''

    def extract_cast(self, response: Response) -> List[str]:
        """
        Extrae el elenco de la obra.

        Returns:
            Lista de nombres del elenco
        """
        cast = []

        # Intentar diferentes selectores para elenco
        cast_items = response.css('.elenco li::text, .cast li::text').getall()
        if not cast_items:
            cast_items = response.css('.elenco .persona::text, .cast .persona::text').getall()
        if not cast_items:
            # Buscar en ficha técnica
            cast_section = response.css('.ficha-tecnica:contains("Elenco"), .ficha:contains("Elenco")').get()
            if cast_section:
                cast_items = response.css('.ficha-tecnica li::text, .ficha li::text').getall()

        # Limpiar y agregar nombres
        for item in cast_items:
            cleaned = clean_text(item)
            if cleaned and len(cleaned) > 2:  # Evitar entradas vacías o muy cortas
                cast.append(cleaned)

        return cast

    def extract_director(self, response: Response) -> Optional[str]:
        """Extrae el director de la obra."""
        # Buscar en ficha técnica
        director = response.css('.director::text, .ficha-director::text').get()
        if not director:
            # Buscar en un formato "Dirección: Nombre"
            ficha_text = response.css('.ficha-tecnica::text, .ficha::text').getall()
            for text in ficha_text:
                if 'dirección' in text.lower() or 'director' in text.lower():
                    # Extraer el nombre después de los dos puntos
                    match = re.search(r'(?:dirección|director)[:\s]+(.+)', text, re.IGNORECASE)
                    if match:
                        director = match.group(1)
                        break

        return clean_text(director) if director else None

    def extract_genre(self, response: Response) -> Optional[str]:
        """Extrae el género teatral de la obra."""
        genre = response.css('.genero::text, .genre::text').get()
        if not genre:
            genre = response.css('.obra-genero::text').get()
        if not genre:
            # Buscar en tags o categorías
            tags = response.css('.tag::text, .categoria::text').getall()
            for tag in tags:
                tag_lower = tag.lower()
                if any(g in tag_lower for g in self.GENRE_MAPPING.keys()):
                    genre = tag
                    break

        return clean_text(genre) if genre else None

    def extract_duration(self, response: Response) -> Optional[str]:
        """Extrae la duración de la obra."""
        duration = response.css('.duracion::text, .duration::text').get()
        if not duration:
            # Buscar patrón "Duración: XX minutos" o "XX min"
            ficha_text = response.css('.ficha-tecnica::text, .ficha::text').getall()
            for text in ficha_text:
                match = re.search(r'duración[:\s]+(\d+\s*(?:min|minutos|hs|horas))', text, re.IGNORECASE)
                if match:
                    duration = match.group(1)
                    break

        return clean_text(duration) if duration else None

    def extract_functions(self, response: Response) -> dict:
        """
        Extrae información de funciones (fechas y horarios).

        Returns:
            dict con start_date, end_date, date_text
        """
        # Alternativa Teatral generalmente lista múltiples funciones
        functions = response.css('.funcion, .function, .horario').getall()

        date_texts = []
        dates = []

        # Intentar extraer fechas de las funciones
        function_dates = response.css('.funcion-fecha::text, .fecha::text, .date::text').getall()
        for date_text in function_dates:
            cleaned = clean_text(date_text)
            if cleaned:
                date_texts.append(cleaned)
                parsed_date = self.parse_date(cleaned)
                if parsed_date:
                    dates.append(parsed_date)

        # Si no hay funciones específicas, buscar texto general de fechas
        if not date_texts:
            general_date = response.css('.obra-fecha::text, .evento-fecha::text').get()
            if general_date:
                date_texts.append(clean_text(general_date))
                parsed_date = self.parse_date(general_date)
                if parsed_date:
                    dates.append(parsed_date)

        # Determinar start_date y end_date
        start_date = min(dates) if dates else None
        end_date = max(dates) if dates and len(dates) > 1 else None
        date_text = ' | '.join(date_texts) if date_texts else ''

        return {
            'start_date': start_date,
            'end_date': end_date,
            'date_text': date_text
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
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        # Mapeo de días de la semana en español
        weekdays = {
            'lunes': 0, 'martes': 1, 'miércoles': 2, 'jueves': 3,
            'viernes': 4, 'sábado': 5, 'domingo': 6,
            'lun': 0, 'mar': 1, 'mié': 2, 'jue': 3, 'vie': 4, 'sáb': 5, 'dom': 6
        }

        try:
            # Patrón: "15 de marzo de 2024" o "15 de marzo"
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

            # Patrón alternativo: "15/03/2024" o "15-03-2024"
            pattern2 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
            match2 = re.search(pattern2, date_text)

            if match2:
                day = int(match2.group(1))
                month = int(match2.group(2))
                year = int(match2.group(3))

                # Si el año es de 2 dígitos, asumimos 20XX
                if year < 100:
                    year += 2000

                return datetime(year, month, day)

        except Exception as e:
            self.logger.warning(f"Error parseando fecha '{date_text}': {str(e)}")

        return None

    def extract_location(self, response: Response) -> dict:
        """Extrae información de la sala/teatro donde se presenta la obra."""
        venue_name = response.css('.sala-nombre::text, .teatro-nombre::text, .venue-name::text').get()
        if not venue_name:
            venue_name = response.css('.lugar::text, .venue::text').get()
        if not venue_name:
            # Buscar en schema.org
            venue_name = response.css('[itemprop="location"] [itemprop="name"]::text').get()

        address = response.css('.sala-direccion::text, .venue-address::text').get()
        if not address:
            address = response.css('.direccion::text, .address::text').get()
        if not address:
            address = response.css('[itemprop="location"] [itemprop="address"]::text').get()

        neighborhood = response.css('.barrio::text, .neighborhood::text').get()
        if not neighborhood:
            # Intentar extraer del address
            if address:
                barrios = ['Palermo', 'Recoleta', 'San Telmo', 'Belgrano', 'Caballito',
                          'Villa Crespo', 'Almagro', 'Flores', 'Núñez', 'Colegiales']
                for barrio in barrios:
                    if barrio.lower() in address.lower():
                        neighborhood = barrio
                        break

        return {
            'venue_name': clean_text(venue_name) if venue_name else '',
            'venue_address': clean_text(address) if address else '',
            'neighborhood': clean_text(neighborhood) if neighborhood else ''
        }

    def extract_price(self, response: Response) -> dict:
        """Extrae información de precio de las entradas."""
        price_text = response.css('.precio::text, .price::text').get()
        if not price_text:
            price_text = response.css('.entrada-precio::text, .ticket-price::text').get()
        if not price_text:
            # Buscar en el texto general
            price_text = response.css('.ficha:contains("Precio")::text, .info:contains("Precio")::text').get()

        is_free = False
        price = None

        if price_text:
            price_text_lower = price_text.lower()
            if 'gratis' in price_text_lower or 'gratuito' in price_text_lower or 'libre' in price_text_lower:
                is_free = True
            else:
                # Intentar extraer precio numérico
                # Buscar patrones como "$1000", "$ 1000", "1000 pesos", etc.
                price_match = re.search(r'\$?\s*(\d+(?:[.,]\d+)?)', price_text)
                if price_match:
                    price_str = price_match.group(1).replace(',', '.')
                    try:
                        price = float(price_str)
                    except ValueError:
                        pass

        return {
            'price': price,
            'is_free': is_free
        }

    def extract_image(self, response: Response) -> Optional[str]:
        """Extrae la URL de la imagen principal de la obra."""
        image = response.css('.obra-imagen img::attr(src), .poster img::attr(src)').get()
        if not image:
            image = response.css('.obra-foto img::attr(src)').get()
        if not image:
            image = response.css('article img::attr(src)').get()
        if not image:
            image = response.css('img[itemprop="image"]::attr(src)').get()
        if not image:
            # Meta tag Open Graph
            image = response.css('meta[property="og:image"]::attr(content)').get()

        if image:
            return response.urljoin(image)

        return None

    def extract_contact(self, response: Response) -> str:
        """Extrae información de contacto."""
        contact = response.css('.contacto::text, .contact::text').get()
        if not contact:
            # Buscar email o teléfono
            email = response.css('a[href^="mailto:"]::attr(href)').get()
            phone = response.css('a[href^="tel:"]::text').get()

            contact_parts = []
            if email:
                contact_parts.append(email.replace('mailto:', ''))
            if phone:
                contact_parts.append(phone)

            contact = ' | '.join(contact_parts) if contact_parts else ''

        return clean_text(contact) if contact else ''

    def extract_booking_url(self, response: Response) -> Optional[str]:
        """Extrae URL de compra de entradas."""
        booking = response.css('a.comprar::attr(href), a.buy-ticket::attr(href)').get()
        if not booking:
            booking = response.css('a:contains("Comprar")::attr(href), a:contains("Entradas")::attr(href)').get()
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
        self.logger.info(f"Total obras scrapeadas: {self.events_scraped}")
        self.logger.info(f"Total errores: {self.errors}")
