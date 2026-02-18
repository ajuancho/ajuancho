"""
Bahoy - Rutas de estadísticas
Endpoint con estadísticas generales de la plataforma.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.category import Category
from app.models.event import Event
from app.schemas.auxiliary import CategoriaStats, StatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Estadísticas generales de la plataforma:
    - Total de eventos activos (con fecha_inicio futura)
    - Eventos por categoría
    - Eventos próximos esta semana
    """
    now = datetime.now(timezone.utc)
    end_of_week = now + timedelta(days=7)

    # Total de eventos activos
    total_result = await db.execute(
        select(func.count(Event.id)).where(Event.fecha_inicio >= now)
    )
    total_activos = total_result.scalar() or 0

    # Eventos por categoría
    cat_result = await db.execute(
        select(
            Category.nombre,
            func.count(Event.id).label("cantidad"),
        )
        .join(Event, Event.categoria_id == Category.id)
        .where(Event.fecha_inicio >= now)
        .group_by(Category.nombre)
        .order_by(func.count(Event.id).desc())
    )
    eventos_por_categoria = [
        CategoriaStats(nombre=row.nombre, cantidad=row.cantidad)
        for row in cat_result.all()
    ]

    # Eventos esta semana
    week_result = await db.execute(
        select(func.count(Event.id)).where(
            Event.fecha_inicio >= now,
            Event.fecha_inicio <= end_of_week,
        )
    )
    eventos_semana = week_result.scalar() or 0

    return StatsResponse(
        total_eventos_activos=total_activos,
        eventos_por_categoria=eventos_por_categoria,
        eventos_esta_semana=eventos_semana,
    )
