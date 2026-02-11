"""
Bahoy - Rutas de administración
Este archivo contiene endpoints para tareas administrativas como scrapers.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from celery.result import AsyncResult

from app.tasks import (
    task_scrape_agenda_ba,
    task_scrape_alternativa_teatral,
    task_full_scrape,
    test_task
)

# Crear el router con el prefijo /admin
router = APIRouter(prefix="/admin", tags=["admin"])


class ScrapeResponse(BaseModel):
    """Modelo de respuesta para operaciones de scraping."""
    message: str
    task_id: str
    source: Optional[str] = None
    status: str


class TaskStatusResponse(BaseModel):
    """Modelo de respuesta para el estado de una tarea."""
    task_id: str
    state: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ========== Endpoints de Scraping ==========

@router.post("/scrape/{source_name}", response_model=ScrapeResponse)
async def trigger_scraper(source_name: str) -> ScrapeResponse:
    """
    Dispara un scraper de forma manual.

    Args:
        source_name: Nombre del scraper a ejecutar
            - 'agenda_ba': Scraper de Agenda Buenos Aires
            - 'alternativa_teatral': Scraper de Alternativa Teatral
            - 'all': Ejecuta todos los scrapers en secuencia

    Returns:
        ScrapeResponse con el ID de la tarea y el estado

    Raises:
        HTTPException: Si el nombre del scraper no es válido
    """
    # Mapeo de nombres a tareas de Celery
    scraper_tasks = {
        "agenda_ba": task_scrape_agenda_ba,
        "alternativa_teatral": task_scrape_alternativa_teatral,
        "all": task_full_scrape
    }

    # Validar que el scraper existe
    if source_name not in scraper_tasks:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Scraper '{source_name}' no encontrado",
                "available_scrapers": list(scraper_tasks.keys())
            }
        )

    # Disparar la tarea de Celery
    task = scraper_tasks[source_name].delay()

    return ScrapeResponse(
        message=f"Scraper '{source_name}' iniciado exitosamente",
        task_id=task.id,
        source=source_name if source_name != "all" else None,
        status="pending"
    )


@router.get("/scrape/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Obtiene el estado de una tarea de scraping.

    Args:
        task_id: ID de la tarea de Celery

    Returns:
        TaskStatusResponse con el estado y resultado (si está disponible)
    """
    # Obtener el resultado de la tarea de Celery
    task_result = AsyncResult(task_id)

    response = TaskStatusResponse(
        task_id=task_id,
        state=task_result.state
    )

    # Si la tarea está completa, incluir el resultado
    if task_result.state == "SUCCESS":
        response.result = task_result.result
    elif task_result.state == "FAILURE":
        response.error = str(task_result.info)

    return response


@router.get("/scrape/list")
async def list_available_scrapers() -> Dict[str, Any]:
    """
    Lista todos los scrapers disponibles con su información.

    Returns:
        Diccionario con la lista de scrapers y sus detalles
    """
    return {
        "scrapers": [
            {
                "name": "agenda_ba",
                "description": "Scraper de Agenda Buenos Aires",
                "source": "https://turismo.buenosaires.gob.ar/es/agenda",
                "schedule": "Diario a las 6:00 AM",
                "endpoint": "/api/v1/admin/scrape/agenda_ba"
            },
            {
                "name": "alternativa_teatral",
                "description": "Scraper de Alternativa Teatral",
                "source": "https://www.alternativateatral.com/cartelera",
                "schedule": "Diario a las 7:00 AM",
                "endpoint": "/api/v1/admin/scrape/alternativa_teatral"
            },
            {
                "name": "all",
                "description": "Ejecuta todos los scrapers en secuencia",
                "schedule": "Manual",
                "endpoint": "/api/v1/admin/scrape/all"
            }
        ],
        "total": 3
    }


# ========== Endpoint de Prueba ==========

@router.post("/test/celery")
async def test_celery_task(message: str = "Hola desde la API!") -> Dict[str, Any]:
    """
    Ejecuta una tarea de prueba en Celery para verificar que está funcionando.

    Args:
        message: Mensaje de prueba (opcional)

    Returns:
        Diccionario con el ID de la tarea y el mensaje
    """
    task = test_task.delay(message)

    return {
        "message": "Tarea de prueba enviada a Celery",
        "task_id": task.id,
        "input_message": message,
        "status": "pending"
    }
