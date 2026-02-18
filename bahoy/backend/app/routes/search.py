"""
Bahoy - Rutas de búsqueda
Endpoint de autocompletado/sugerencias para el buscador.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.category import Category
from app.models.event import Event
from app.models.venue import Venue
from app.schemas.auxiliary import SearchSuggestionsResponse, SuggestionItem

router = APIRouter(prefix="/search", tags=["search"])

MAX_SUGGESTIONS_PER_TYPE = 5


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_suggestions(
    query: str = Query(..., min_length=2, description="Texto parcial para autocompletado"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Autocompletado para el buscador.
    Devuelve sugerencias de eventos, venues y categorías que coincidan
    con el texto parcial ingresado.
    """
    pattern = f"%{query}%"
    sugerencias: list[SuggestionItem] = []

    # Buscar eventos por título
    events_result = await db.execute(
        select(Event)
        .where(Event.titulo.ilike(pattern))
        .order_by(Event.fecha_inicio.desc().nulls_last())
        .limit(MAX_SUGGESTIONS_PER_TYPE)
    )
    for event in events_result.scalars().all():
        fecha_str = event.fecha_inicio.strftime("%d/%m/%Y") if event.fecha_inicio else None
        sugerencias.append(
            SuggestionItem(
                tipo="evento",
                id=event.id,
                texto=event.titulo,
                extra=fecha_str,
            )
        )

    # Buscar venues por nombre
    venues_result = await db.execute(
        select(Venue)
        .where(Venue.nombre.ilike(pattern))
        .order_by(Venue.nombre)
        .limit(MAX_SUGGESTIONS_PER_TYPE)
    )
    for venue in venues_result.scalars().all():
        sugerencias.append(
            SuggestionItem(
                tipo="venue",
                id=venue.id,
                texto=venue.nombre,
                extra=venue.barrio,
            )
        )

    # Buscar categorías por nombre
    categories_result = await db.execute(
        select(Category)
        .where(Category.nombre.ilike(pattern))
        .order_by(Category.nombre)
        .limit(MAX_SUGGESTIONS_PER_TYPE)
    )
    for cat in categories_result.scalars().all():
        sugerencias.append(
            SuggestionItem(
                tipo="categoria",
                id=cat.id,
                texto=cat.nombre,
            )
        )

    return {"sugerencias": sugerencias}
