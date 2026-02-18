"""
Bahoy - Rutas de barrios
Endpoint para listar barrios de Buenos Aires con cantidad de eventos.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.models.venue import Venue
from app.schemas.auxiliary import BarrioResponse, BarriosListResponse

router = APIRouter(prefix="/barrios", tags=["barrios"])


@router.get("", response_model=BarriosListResponse)
async def get_barrios(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Lista de barrios de Buenos Aires con la cantidad de eventos próximos en cada uno.
    Solo incluye barrios que tienen al menos un venue registrado.
    """
    now = datetime.now(timezone.utc)

    # Subconsulta: contar eventos futuros por venue
    result = await db.execute(
        select(
            Venue.barrio,
            func.count(Event.id).label("cantidad_eventos"),
        )
        .join(Event, Event.venue_id == Venue.id, isouter=True)
        .where(
            Venue.barrio.isnot(None),
            (Event.fecha_inicio >= now) | (Event.id.is_(None)),
        )
        .group_by(Venue.barrio)
        .order_by(func.count(Event.id).desc())
    )
    rows = result.all()

    barrios = [
        BarrioResponse(nombre=row.barrio, cantidad_eventos=row.cantidad_eventos)
        for row in rows
        if row.barrio
    ]

    return {"barrios": barrios}
