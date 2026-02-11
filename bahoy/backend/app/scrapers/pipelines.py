"""
Bahoy - Scrapy Pipelines
Procesa y guarda los eventos scrapeados en PostgreSQL.
"""

import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import Optional
import json


class EventProcessingPipeline:
    """
    Pipeline para procesar y limpiar los datos de eventos.
    """

    def process_item(self, item, spider):
        """
        Procesa y valida un item antes de guardarlo.

        Args:
            item: EventItem a procesar
            spider: Spider que generó el item

        Returns:
            Item procesado
        """
        # Validar campos requeridos
        if not item.get('title'):
            spider.logger.warning(f"Evento sin título, descartado: {item.get('url')}")
            raise DropItem("Evento sin título")

        # Normalizar título
        item['title'] = item['title'].strip()

        # Validar y normalizar fechas
        if item.get('start_date') and not isinstance(item['start_date'], datetime):
            spider.logger.warning(f"Fecha inválida para evento: {item['title']}")
            item['start_date'] = None

        # Normalizar precio
        if item.get('is_free'):
            item['price'] = 0.0
        elif item.get('price') is None:
            item['price'] = 0.0
            item['is_free'] = True

        # Asegurar que tags sea una lista
        if not item.get('tags'):
            item['tags'] = []
        elif isinstance(item['tags'], str):
            item['tags'] = [item['tags']]

        # Normalizar categoría
        if not item.get('category'):
            item['category'] = 'other'

        spider.logger.debug(f"Item procesado: {item['title']}")
        return item


class PostgreSQLPipeline:
    """
    Pipeline para guardar eventos en PostgreSQL.
    Verifica duplicados por hash y actualiza o inserta según corresponda.
    """

    def __init__(self, db_config):
        """
        Inicializa el pipeline con la configuración de la base de datos.

        Args:
            db_config: Diccionario con la configuración de PostgreSQL
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        self.events_inserted = 0
        self.events_updated = 0
        self.events_skipped = 0

    @classmethod
    def from_crawler(cls, crawler):
        """
        Crea el pipeline desde el crawler, obteniendo la configuración.

        Args:
            crawler: Crawler de Scrapy

        Returns:
            Instancia del pipeline
        """
        # Obtener configuración de la base de datos desde settings
        db_config = {
            'host': crawler.settings.get('POSTGRES_HOST', 'localhost'),
            'port': crawler.settings.get('POSTGRES_PORT', 5432),
            'user': crawler.settings.get('POSTGRES_USER', 'bahoy_user'),
            'password': crawler.settings.get('POSTGRES_PASSWORD', 'bahoy_password'),
            'database': crawler.settings.get('POSTGRES_DB', 'bahoy_db')
        }
        return cls(db_config)

    def open_spider(self, spider):
        """
        Se ejecuta cuando el spider se abre.
        Establece la conexión a PostgreSQL y crea las tablas si no existen.

        Args:
            spider: Spider que se está abriendo
        """
        spider.logger.info("Conectando a PostgreSQL...")

        try:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            self.cursor = self.connection.cursor()

            # Crear tabla de eventos si no existe
            self.create_tables(spider)

            spider.logger.info("Conexión a PostgreSQL establecida exitosamente")

        except psycopg2.Error as e:
            spider.logger.error(f"Error conectando a PostgreSQL: {e}")
            raise

    def create_tables(self, spider):
        """
        Crea las tablas necesarias si no existen.

        Args:
            spider: Spider actual
        """
        create_events_table = """
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            event_hash VARCHAR(32) UNIQUE NOT NULL,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            short_description TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            date_text VARCHAR(200),
            venue_name VARCHAR(300),
            venue_address TEXT,
            neighborhood VARCHAR(100),
            latitude FLOAT,
            longitude FLOAT,
            category VARCHAR(50),
            tags TEXT[],
            image_url TEXT,
            price DECIMAL(10, 2),
            is_free BOOLEAN DEFAULT TRUE,
            url TEXT UNIQUE NOT NULL,
            source VARCHAR(50),
            contact_info TEXT,
            booking_url TEXT,
            accessibility TEXT,
            age_restriction VARCHAR(50),
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_events_hash ON events(event_hash);
        CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
        CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
        CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
        """

        try:
            self.cursor.execute(create_events_table)
            self.connection.commit()
            spider.logger.info("Tablas de base de datos verificadas/creadas")
        except psycopg2.Error as e:
            spider.logger.error(f"Error creando tablas: {e}")
            self.connection.rollback()

    def close_spider(self, spider):
        """
        Se ejecuta cuando el spider se cierra.
        Cierra la conexión a PostgreSQL.

        Args:
            spider: Spider que se está cerrando
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

        spider.logger.info("Conexión a PostgreSQL cerrada")
        spider.logger.info(f"Estadísticas de guardado:")
        spider.logger.info(f"  - Eventos insertados: {self.events_inserted}")
        spider.logger.info(f"  - Eventos actualizados: {self.events_updated}")
        spider.logger.info(f"  - Eventos omitidos: {self.events_skipped}")

    def process_item(self, item, spider):
        """
        Procesa un item y lo guarda en la base de datos.

        Args:
            item: EventItem a guardar
            spider: Spider que generó el item

        Returns:
            Item guardado
        """
        try:
            # Verificar si el evento ya existe por hash
            existing_event = self.check_existing_event(item['event_hash'])

            if existing_event:
                # El evento existe, verificar si necesita actualización
                if self.should_update_event(item, existing_event, spider):
                    self.update_event(item, spider)
                    self.events_updated += 1
                else:
                    spider.logger.debug(f"Evento sin cambios: {item['title']}")
                    self.events_skipped += 1
            else:
                # Evento nuevo, insertar
                self.insert_event(item, spider)
                self.events_inserted += 1

            return item

        except psycopg2.Error as e:
            spider.logger.error(f"Error guardando evento en DB: {e}")
            spider.logger.error(f"Evento problemático: {item.get('title', 'SIN TITULO')}")
            self.connection.rollback()
            raise

    def check_existing_event(self, event_hash: str) -> Optional[dict]:
        """
        Verifica si un evento ya existe en la base de datos.

        Args:
            event_hash: Hash del evento a verificar

        Returns:
            Diccionario con datos del evento si existe, None si no existe
        """
        query = """
        SELECT id, title, description, start_date, updated_at
        FROM events
        WHERE event_hash = %s
        """

        self.cursor.execute(query, (event_hash,))
        row = self.cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'start_date': row[3],
                'updated_at': row[4]
            }

        return None

    def should_update_event(self, new_item: dict, existing_event: dict, spider) -> bool:
        """
        Determina si un evento existente debe actualizarse.

        Args:
            new_item: Nuevo item scrapeado
            existing_event: Evento existente en la base de datos
            spider: Spider actual

        Returns:
            True si debe actualizarse, False en caso contrario
        """
        # Actualizar si ha pasado más de 7 días desde la última actualización
        if existing_event['updated_at']:
            days_since_update = (datetime.now() - existing_event['updated_at']).days
            if days_since_update > 7:
                return True

        # Actualizar si la descripción ha cambiado significativamente
        new_desc = new_item.get('description', '')
        old_desc = existing_event.get('description', '')
        if len(new_desc) > len(old_desc) * 1.1:  # 10% más largo
            return True

        return False

    def insert_event(self, item: dict, spider):
        """
        Inserta un nuevo evento en la base de datos.

        Args:
            item: EventItem a insertar
            spider: Spider actual
        """
        query = """
        INSERT INTO events (
            event_hash, title, description, short_description,
            start_date, end_date, date_text,
            venue_name, venue_address, neighborhood,
            latitude, longitude,
            category, tags,
            image_url, price, is_free,
            url, source,
            contact_info, booking_url,
            scraped_at
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s
        )
        """

        values = (
            item['event_hash'],
            item['title'],
            item.get('description'),
            item.get('short_description'),
            item.get('start_date'),
            item.get('end_date'),
            item.get('date_text'),
            item.get('venue_name'),
            item.get('venue_address'),
            item.get('neighborhood'),
            item.get('latitude'),
            item.get('longitude'),
            item.get('category'),
            item.get('tags', []),
            item.get('image_url'),
            item.get('price'),
            item.get('is_free', True),
            item['url'],
            item['source'],
            item.get('contact_info'),
            item.get('booking_url'),
            item['scraped_at']
        )

        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            spider.logger.info(f"Evento insertado: {item['title']}")
        except psycopg2.IntegrityError as e:
            # Posible duplicado por URL
            spider.logger.warning(f"Posible duplicado detectado: {item['title']}")
            self.connection.rollback()

    def update_event(self, item: dict, spider):
        """
        Actualiza un evento existente en la base de datos.

        Args:
            item: EventItem con nuevos datos
            spider: Spider actual
        """
        query = """
        UPDATE events SET
            title = %s,
            description = %s,
            short_description = %s,
            start_date = %s,
            end_date = %s,
            date_text = %s,
            venue_name = %s,
            venue_address = %s,
            neighborhood = %s,
            category = %s,
            tags = %s,
            image_url = %s,
            price = %s,
            is_free = %s,
            contact_info = %s,
            booking_url = %s,
            scraped_at = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE event_hash = %s
        """

        values = (
            item['title'],
            item.get('description'),
            item.get('short_description'),
            item.get('start_date'),
            item.get('end_date'),
            item.get('date_text'),
            item.get('venue_name'),
            item.get('venue_address'),
            item.get('neighborhood'),
            item.get('category'),
            item.get('tags', []),
            item.get('image_url'),
            item.get('price'),
            item.get('is_free', True),
            item.get('contact_info'),
            item.get('booking_url'),
            item['scraped_at'],
            item['event_hash']
        )

        self.cursor.execute(query, values)
        self.connection.commit()
        spider.logger.info(f"Evento actualizado: {item['title']}")


class DropItem(Exception):
    """Excepción para descartar items."""
    pass
