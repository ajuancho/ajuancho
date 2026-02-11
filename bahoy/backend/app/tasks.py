"""
Bahoy - Tareas de Celery
Este archivo define todas las tareas asíncronas para scrapers y otras operaciones.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

from celery import Task
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from crochet import setup, wait_for

# Configurar crochet para usar Scrapy con Celery
setup()

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.celery_app import celery_app
from app.scrapers.agenda_ba_spider import AgendaBaSpider
from app.scrapers.alternativa_teatral_spider import AlternativaTeatralSpider
from app.scrapers import settings as scrapy_settings

# Configurar logging
logger = logging.getLogger(__name__)

# Configurar Scrapy logging
configure_logging(install_root_handler=False)


class ScraperTask(Task):
    """
    Clase base para tareas de scraping con manejo de errores y reintentos.
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 300}  # Reintentar hasta 3 veces, esperar 5 min
    retry_backoff = True
    retry_backoff_max = 600  # Máximo 10 minutos entre reintentos
    retry_jitter = True  # Añadir jitter aleatorio a los reintentos


def get_scrapy_settings() -> Dict[str, Any]:
    """
    Obtiene la configuración de Scrapy para los crawlers.

    Returns:
        Diccionario con la configuración de Scrapy
    """
    return {
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
        'LOG_LEVEL': scrapy_settings.LOG_LEVEL,
        'AUTOTHROTTLE_ENABLED': scrapy_settings.AUTOTHROTTLE_ENABLED,
        'AUTOTHROTTLE_START_DELAY': scrapy_settings.AUTOTHROTTLE_START_DELAY,
        'AUTOTHROTTLE_MAX_DELAY': scrapy_settings.AUTOTHROTTLE_MAX_DELAY,
        'MEMUSAGE_ENABLED': scrapy_settings.MEMUSAGE_ENABLED,
        'MEMUSAGE_LIMIT_MB': scrapy_settings.MEMUSAGE_LIMIT_MB,
    }


@wait_for(timeout=3600)  # Timeout de 1 hora
def run_spider(spider_class):
    """
    Ejecuta un spider de Scrapy usando CrawlerRunner.

    Args:
        spider_class: Clase del spider a ejecutar

    Returns:
        Deferred que se resuelve cuando el spider termina
    """
    runner = CrawlerRunner(get_scrapy_settings())
    return runner.crawl(spider_class)


@celery_app.task(
    bind=True,
    base=ScraperTask,
    name="app.tasks.task_scrape_agenda_ba"
)
def task_scrape_agenda_ba(self) -> Dict[str, Any]:
    """
    Tarea para ejecutar el scraper de Agenda Buenos Aires.
    Programado para ejecutarse diariamente a las 6:00 AM.

    Returns:
        Diccionario con información sobre la ejecución
    """
    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info("INICIANDO SCRAPER: Agenda Buenos Aires")
    logger.info(f"Tarea ID: {self.request.id}")
    logger.info(f"Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    try:
        # Ejecutar el spider
        run_spider(AgendaBaSpider)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("-" * 70)
        logger.info("SCRAPER COMPLETADO: Agenda Buenos Aires")
        logger.info(f"Duración: {duration:.2f} segundos")
        logger.info(f"Hora de finalización: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)

        return {
            "status": "success",
            "spider": "agenda_ba",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "task_id": self.request.id
        }

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.error("-" * 70)
        logger.error(f"ERROR EN SCRAPER: Agenda Buenos Aires")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Duración antes del error: {duration:.2f} segundos")
        logger.error("=" * 70)

        # Re-lanzar la excepción para que Celery maneje el reintento
        raise


@celery_app.task(
    bind=True,
    base=ScraperTask,
    name="app.tasks.task_scrape_alternativa_teatral"
)
def task_scrape_alternativa_teatral(self) -> Dict[str, Any]:
    """
    Tarea para ejecutar el scraper de Alternativa Teatral.
    Programado para ejecutarse diariamente a las 7:00 AM.

    Returns:
        Diccionario con información sobre la ejecución
    """
    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info("INICIANDO SCRAPER: Alternativa Teatral")
    logger.info(f"Tarea ID: {self.request.id}")
    logger.info(f"Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    try:
        # Ejecutar el spider
        run_spider(AlternativaTeatralSpider)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("-" * 70)
        logger.info("SCRAPER COMPLETADO: Alternativa Teatral")
        logger.info(f"Duración: {duration:.2f} segundos")
        logger.info(f"Hora de finalización: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)

        return {
            "status": "success",
            "spider": "alternativa_teatral",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "task_id": self.request.id
        }

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.error("-" * 70)
        logger.error(f"ERROR EN SCRAPER: Alternativa Teatral")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Duración antes del error: {duration:.2f} segundos")
        logger.error("=" * 70)

        # Re-lanzar la excepción para que Celery maneje el reintento
        raise


@celery_app.task(
    bind=True,
    base=ScraperTask,
    name="app.tasks.task_full_scrape"
)
def task_full_scrape(self) -> Dict[str, Any]:
    """
    Tarea para ejecutar todos los scrapers en secuencia.
    Para ejecución manual o bajo demanda.

    Returns:
        Diccionario con información sobre la ejecución de todos los scrapers
    """
    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info("INICIANDO SCRAPING COMPLETO: Todos los scrapers")
    logger.info(f"Tarea ID: {self.request.id}")
    logger.info(f"Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    results = {}
    spiders = {
        "agenda_ba": AgendaBaSpider,
        "alternativa_teatral": AlternativaTeatralSpider
    }

    for spider_name, spider_class in spiders.items():
        spider_start = datetime.now()
        logger.info(f"\n--- Ejecutando spider: {spider_name} ---")

        try:
            run_spider(spider_class)

            spider_end = datetime.now()
            spider_duration = (spider_end - spider_start).total_seconds()

            results[spider_name] = {
                "status": "success",
                "start_time": spider_start.isoformat(),
                "end_time": spider_end.isoformat(),
                "duration_seconds": spider_duration
            }

            logger.info(f"Spider {spider_name} completado en {spider_duration:.2f} segundos")

        except Exception as e:
            spider_end = datetime.now()
            spider_duration = (spider_end - spider_start).total_seconds()

            results[spider_name] = {
                "status": "error",
                "error": str(e),
                "start_time": spider_start.isoformat(),
                "end_time": spider_end.isoformat(),
                "duration_seconds": spider_duration
            }

            logger.error(f"Error en spider {spider_name}: {str(e)}")
            # Continuar con el siguiente spider en lugar de fallar completamente

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    logger.info("-" * 70)
    logger.info("SCRAPING COMPLETO FINALIZADO")
    logger.info(f"Duración total: {total_duration:.2f} segundos")
    logger.info(f"Hora de finalización: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    return {
        "status": "completed",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_duration_seconds": total_duration,
        "task_id": self.request.id,
        "spiders": results
    }


# Tarea de prueba para verificar que Celery funciona
@celery_app.task(name="app.tasks.test_task")
def test_task(message: str = "Hola desde Celery!") -> Dict[str, str]:
    """
    Tarea de prueba para verificar que Celery está configurado correctamente.

    Args:
        message: Mensaje de prueba

    Returns:
        Diccionario con el mensaje y timestamp
    """
    logger.info(f"Ejecutando tarea de prueba: {message}")
    return {
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }
