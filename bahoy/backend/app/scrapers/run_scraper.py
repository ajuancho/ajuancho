#!/usr/bin/env python3
"""
Bahoy - Runner para Scrapy
Script para ejecutar el scraper de Agenda Buenos Aires fácilmente.

Uso:
    python run_scraper.py
    python run_scraper.py --output events.json
    python run_scraper.py --debug
"""

import sys
import os
import argparse
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.scrapers.agenda_ba_spider import AgendaBaSpider
from app.scrapers import settings as scrapy_settings


def setup_logging(debug: bool = False):
    """
    Configura el logging para el scraper.

    Args:
        debug: Si True, muestra logs de nivel DEBUG
    """
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_scraper(output_file: str = None, debug: bool = False):
    """
    Ejecuta el scraper de Agenda Buenos Aires.

    Args:
        output_file: Archivo de salida opcional (JSON/CSV)
        debug: Modo debug para logs detallados
    """
    setup_logging(debug)

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("BAHOY - Scraper de Agenda Buenos Aires")
    logger.info("=" * 60)

    # Crear configuración del proceso
    settings_dict = {
        'BOT_NAME': scrapy_settings.BOT_NAME,
        'USER_AGENT': scrapy_settings.USER_AGENT,
        'ROBOTSTXT_OBEY': scrapy_settings.ROBOTSTXT_OBEY,
        'DOWNLOAD_DELAY': scrapy_settings.DOWNLOAD_DELAY,
        'RANDOMIZE_DOWNLOAD_DELAY': scrapy_settings.RANDOMIZE_DOWNLOAD_DELAY,
        'CONCURRENT_REQUESTS': scrapy_settings.CONCURRENT_REQUESTS,
        'CONCURRENT_REQUESTS_PER_DOMAIN': scrapy_settings.CONCURRENT_REQUESTS_PER_DOMAIN,
        'DOWNLOAD_TIMEOUT': scrapy_settings.DOWNLOAD_TIMEOUT,
        'RETRY_ENABLED': scrapy_settings.RETRY_ENABLED,
        'RETRY_TIMES': scrapy_settings.RETRY_TIMES,
        'RETRY_HTTP_CODES': scrapy_settings.RETRY_HTTP_CODES,
        'DOWNLOADER_MIDDLEWARES': scrapy_settings.DOWNLOADER_MIDDLEWARES,
        'SPIDER_MIDDLEWARES': scrapy_settings.SPIDER_MIDDLEWARES,
        'ITEM_PIPELINES': scrapy_settings.ITEM_PIPELINES,
        'POSTGRES_HOST': scrapy_settings.POSTGRES_HOST,
        'POSTGRES_PORT': scrapy_settings.POSTGRES_PORT,
        'POSTGRES_USER': scrapy_settings.POSTGRES_USER,
        'POSTGRES_PASSWORD': scrapy_settings.POSTGRES_PASSWORD,
        'POSTGRES_DB': scrapy_settings.POSTGRES_DB,
        'LOG_LEVEL': 'DEBUG' if debug else scrapy_settings.LOG_LEVEL,
        'AUTOTHROTTLE_ENABLED': scrapy_settings.AUTOTHROTTLE_ENABLED,
        'AUTOTHROTTLE_START_DELAY': scrapy_settings.AUTOTHROTTLE_START_DELAY,
        'AUTOTHROTTLE_MAX_DELAY': scrapy_settings.AUTOTHROTTLE_MAX_DELAY,
        'MEMUSAGE_ENABLED': scrapy_settings.MEMUSAGE_ENABLED,
        'MEMUSAGE_LIMIT_MB': scrapy_settings.MEMUSAGE_LIMIT_MB,
    }

    # Configurar salida a archivo si se especificó
    if output_file:
        file_ext = os.path.splitext(output_file)[1].lower()

        if file_ext == '.json':
            settings_dict['FEEDS'] = {
                output_file: {
                    'format': 'json',
                    'encoding': 'utf8',
                    'store_empty': False,
                    'indent': 2,
                }
            }
            logger.info(f"Salida JSON habilitada: {output_file}")

        elif file_ext == '.csv':
            settings_dict['FEEDS'] = {
                output_file: {
                    'format': 'csv',
                    'encoding': 'utf8',
                    'store_empty': False,
                }
            }
            logger.info(f"Salida CSV habilitada: {output_file}")

        else:
            logger.warning(f"Formato de archivo no soportado: {file_ext}")
            logger.warning("Formatos soportados: .json, .csv")

    # Crear y configurar el proceso de crawling
    process = CrawlerProcess(settings_dict)

    # Añadir el spider al proceso
    process.crawl(AgendaBaSpider)

    # Iniciar el scraping
    logger.info("Iniciando scraper...")
    logger.info(f"URL objetivo: {AgendaBaSpider.start_urls[0]}")
    logger.info("-" * 60)

    try:
        process.start()  # Bloqueante hasta que termine
        logger.info("-" * 60)
        logger.info("Scraper finalizado exitosamente")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("\nScraper interrumpido por el usuario")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error durante el scraping: {e}", exc_info=True)
        sys.exit(1)


def main():
    """
    Punto de entrada principal del script.
    """
    parser = argparse.ArgumentParser(
        description='Ejecuta el scraper de Agenda Buenos Aires',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Ejecutar scraper y guardar en PostgreSQL
  python run_scraper.py

  # Ejecutar con salida a archivo JSON
  python run_scraper.py --output events.json

  # Ejecutar con salida a archivo CSV
  python run_scraper.py --output events.csv

  # Ejecutar en modo debug (logs detallados)
  python run_scraper.py --debug

  # Combinar opciones
  python run_scraper.py --output events.json --debug
        """
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Archivo de salida (JSON o CSV). Los datos también se guardan en PostgreSQL.',
        metavar='FILE'
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Activar modo debug (logs detallados)'
    )

    args = parser.parse_args()

    # Ejecutar el scraper
    run_scraper(output_file=args.output, debug=args.debug)


if __name__ == '__main__':
    main()
