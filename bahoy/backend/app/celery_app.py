"""
Bahoy - Configuración de Celery
Este archivo configura Celery para ejecutar tareas asíncronas y programadas.
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear instancia de Celery
celery_app = Celery(
    "bahoy",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]  # Importar módulo de tareas
)

# Configuración de Celery
celery_app.conf.update(
    # Configuración de zona horaria
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=True,

    # Configuración de resultados
    result_expires=3600,  # Los resultados expiran en 1 hora
    result_persistent=True,  # Persistir resultados en Redis

    # Configuración de tareas
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,  # Rastrear cuando una tarea comienza
    task_time_limit=3600,  # Límite de tiempo de 1 hora por tarea
    task_soft_time_limit=3300,  # Límite suave de 55 minutos

    # Configuración de reintentos
    task_acks_late=True,  # Confirmar tareas solo después de completarse
    task_reject_on_worker_lost=True,  # Rechazar tareas si el worker se pierde

    # Configuración de worker
    worker_prefetch_multiplier=1,  # Obtener una tarea a la vez
    worker_max_tasks_per_child=50,  # Reiniciar worker cada 50 tareas (prevenir memory leaks)

    # Configuración de logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",

    # Configuración de Beat (scheduler)
    beat_schedule={
        # Tarea diaria: Scraper de Agenda BA a las 6:00 AM
        "scrape-agenda-ba-daily": {
            "task": "app.tasks.task_scrape_agenda_ba",
            "schedule": crontab(hour=6, minute=0),  # 6:00 AM todos los días
            "options": {
                "expires": 3600,  # La tarea expira si no se ejecuta en 1 hora
            }
        },
        # Tarea diaria: Scraper de Alternativa Teatral a las 7:00 AM
        "scrape-alternativa-teatral-daily": {
            "task": "app.tasks.task_scrape_alternativa_teatral",
            "schedule": crontab(hour=7, minute=0),  # 7:00 AM todos los días
            "options": {
                "expires": 3600,
            }
        },
    },
    beat_schedule_filename="/tmp/celerybeat-schedule",  # Archivo de estado del scheduler
)

# Configurar logging para Celery
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Configuración adicional después de que Celery se configure.
    """
    logger.info("Celery configurado correctamente")
    logger.info(f"Broker URL: {settings.REDIS_URL}")
    logger.info("Tareas programadas:")
    logger.info("  - Agenda BA: Diaria a las 6:00 AM")
    logger.info("  - Alternativa Teatral: Diaria a las 7:00 AM")


# Event handlers para logging
@celery_app.task(bind=True)
def debug_task(self):
    """
    Tarea de prueba para verificar que Celery funciona.
    """
    logger.info(f"Request: {self.request!r}")
    return "Celery está funcionando correctamente"


if __name__ == "__main__":
    celery_app.start()
