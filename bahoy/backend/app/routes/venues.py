"""
Bahoy - Rutas de venues
Endpoints para listar venues con filtros y obtener detalle con próximos eventos.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.models.venue import Venue, VenueType
from app.schemas.auxiliary import (
    EventoEnVenue,
    VenueDetailResponse,
    VenueListItem,
    VenuesListResponse,
)

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("", response_model=VenuesListResponse)
async def get_venues(
    barrio: str | None = Query(None, description="Filtrar por barrio"),
    tipo: str | None = Query(None, description="Filtrar por tipo de venue"),
    con_eventos: bool = Query(False, description="Solo venues con eventos próximos"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Lista de venues con filtros opcionales.
    Permite filtrar por barrio, tipo y si tienen eventos próximos.
    """
    query = select(Venue).order_by(Venue.nombre)

    if barrio:
        query = query.where(Venue.barrio.ilike(f"%{barrio}%"))

    if tipo:
        try:
            venue_type = VenueType(tipo)
            query = query.where(Venue.tipo == venue_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de venue inválido. Válidos: {[t.value for t in VenueType]}",
            )

    if con_eventos:
        now = datetime.now(timezone.utc)
        subquery = (
            select(Event.venue_id)
            .where(Event.fecha_inicio >= now)
            .distinct()
            .scalar_subquery()
        )
        query = query.where(Venue.id.in_(subquery))

    result = await db.execute(query)
    venues = result.scalars().all()

    # Contar eventos futuros por venue
    now = datetime.now(timezone.utc)
    venue_items = []
    for v in venues:
        count_result = await db.execute(
            select(func.count(Event.id)).where(
                Event.venue_id == v.id,
                Event.fecha_inicio >= now,
            )
        )
        cantidad = count_result.scalar() or 0

        venue_items.append(
            VenueListItem(
                id=v.id,
                nombre=v.nombre,
                direccion=v.direccion,
                barrio=v.barrio,
                tipo=v.tipo.value if v.tipo else None,
                latitud=v.latitud,
                longitud=v.longitud,
                capacidad=v.capacidad,
                cantidad_eventos=cantidad,
            )
        )

    return {"venues": venue_items, "total": len(venue_items)}


@router.get("/{venue_id}", response_model=VenueDetailResponse)
async def get_venue_detail(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Detalle de un venue con sus próximos eventos.
    """
    result = await db.execute(select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue no encontrado")

    # Obtener próximos eventos del venue
    now = datetime.now(timezone.utc)
    events_result = await db.execute(
        select(Event)
        .where(Event.venue_id == venue_id, Event.fecha_inicio >= now)
        .order_by(Event.fecha_inicio)
    )
    eventos = events_result.scalars().all()

    return VenueDetailResponse(
        id=venue.id,
        nombre=venue.nombre,
        direccion=venue.direccion,
        barrio=venue.barrio,
        tipo=venue.tipo.value if venue.tipo else None,
        latitud=venue.latitud,
        longitud=venue.longitud,
        capacidad=venue.capacidad,
        proximos_eventos=[
            EventoEnVenue(
                id=e.id,
                titulo=e.titulo,
                fecha_inicio=e.fecha_inicio,
                fecha_fin=e.fecha_fin,
                precio_min=float(e.precio_min) if e.precio_min is not None else None,
                precio_max=float(e.precio_max) if e.precio_max is not None else None,
                es_gratuito=e.es_gratuito,
                imagen_url=e.imagen_url,
            )
            for e in eventos
        ],
    )
