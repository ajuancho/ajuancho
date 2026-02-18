"""
Bahoy - Rutas de recomendaciones
Endpoints para obtener recomendaciones personalizadas de eventos culturales.
"""

import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.recommender import RecommenderService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{user_id}", response_model=list[dict[str, Any]])
async def get_recommendations(
    user_id: uuid.UUID,
    tipo: Literal["personalizadas", "populares", "similares"] = Query(
        default="personalizadas",
        description="Tipo de recomendación",
    ),
    event_id: uuid.UUID | None = Query(
        default=None,
        description="ID del evento base (requerido si tipo=similares)",
    ),
    limite: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Número de resultados a devolver",
    ),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Obtiene recomendaciones de eventos para el usuario.

    Tipos disponibles:
    - **personalizadas**: basadas en las preferencias declaradas del usuario
      (categorías favoritas, barrios, rango de precio, tags de interés)
    - **populares**: eventos más populares por interacciones (fallback para
      usuarios sin historial o sin preferencias)
    - **similares**: eventos similares a uno dado; requiere `event_id`

    Cada resultado incluye el evento y la razón por la que se recomienda:
    ```json
    {
      "event": { ... },
      "razon": "Porque te gustan: eventos de Teatro · en Palermo"
    }
    ```
    """
    service = RecommenderService(db)

    if tipo == "similares":
        if not event_id:
            raise HTTPException(
                status_code=422,
                detail="Se requiere 'event_id' cuando tipo=similares",
            )
        return await service.recomendar_similares(str(event_id), limite)

    if tipo == "populares":
        return await service.recomendar_populares(limite)

    # tipo == "personalizadas"
    return await service.recomendar_para_usuario(str(user_id), limite)


@router.get("/contexto/buscar", response_model=list[dict[str, Any]])
async def get_recommendations_by_context(
    query: str | None = Query(
        default=None,
        description=(
            "Texto libre: 'esta noche', 'gratis', 'con niños', 'fin de semana', 'hoy'"
        ),
    ),
    barrio: str | None = Query(
        default=None,
        description="Filtrar por barrio (ej: Palermo, San Telmo)",
    ),
    gratis: bool | None = Query(
        default=None,
        description="Solo eventos gratuitos",
    ),
    limite: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Número de resultados a devolver",
    ),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Recomendaciones contextuales sin necesidad de autenticación.

    Acepta lenguaje natural para filtrar eventos:
    - **"esta noche"** → eventos de hoy a partir de las 19 hs
    - **"hoy"** → eventos del día de hoy
    - **"fin de semana"** → eventos del próximo sábado y domingo
    - **"gratis"** → solo eventos gratuitos
    - **"con niños"** → eventos con tags familiar/infantil
    - Combinaciones: `?query=gratis esta noche&barrio=Palermo`
    """
    service = RecommenderService(db)
    contexto = {
        "query": query or "",
        "barrio": barrio,
        "gratis": gratis,
    }
    resultados = await service.recomendar_por_contexto(contexto)
    return resultados[:limite]
