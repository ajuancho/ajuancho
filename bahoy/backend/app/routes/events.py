"""
Bahoy - Rutas de eventos
Endpoints para listar y obtener eventos culturales de Buenos Aires.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.category import Category
from app.models.event import Event
from app.models.venue import Venue

router = APIRouter(prefix="/events", tags=["events"])


def _serializar_evento(event: Event) -> dict[str, Any]:
    """Convierte un objeto Event ORM a dict JSON-serializable."""
    return {
        "id": str(event.id),
        "titulo": event.titulo,
        "descripcion": event.descripcion,
        "categoria": event.categoria.nombre if event.categoria else None,
        "subcategorias": event.subcategorias,
        "fecha_inicio": (
            event.fecha_inicio.isoformat() if event.fecha_inicio else None
        ),
        "fecha_fin": event.fecha_fin.isoformat() if event.fecha_fin else None,
        "venue": (
            {
                "id": str(event.venue.id),
                "nombre": event.venue.nombre,
                "barrio": event.venue.barrio,
                "direccion": event.venue.direccion,
            }
            if event.venue
            else None
        ),
        "precio_min": (
            float(event.precio_min) if event.precio_min is not None else None
        ),
        "precio_max": (
            float(event.precio_max) if event.precio_max is not None else None
        ),
        "es_gratuito": event.es_gratuito,
        "imagen_url": event.imagen_url,
        "url_fuente": event.url_fuente,
        "tags": event.tags,
    }


@router.get("", response_model=list[dict[str, Any]])
async def list_events(
    categoria: str | None = Query(
        default=None, description="Filtrar por nombre de categoría"
    ),
    barrio: str | None = Query(
        default=None, description="Filtrar por barrio del venue"
    ),
    gratis: bool | None = Query(
        default=None, description="Solo eventos gratuitos (true/false)"
    ),
    fecha_desde: datetime | None = Query(
        default=None, description="Eventos desde esta fecha (ISO 8601)"
    ),
    fecha_hasta: datetime | None = Query(
        default=None, description="Eventos hasta esta fecha (ISO 8601)"
    ),
    page: int = Query(default=1, ge=1, description="Número de página"),
    per_page: int = Query(
        default=20, ge=1, le=100, description="Resultados por página"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Lista eventos con filtros opcionales.

    Filtros disponibles:
    - **categoria**: nombre de la categoría (ej: teatro, música)
    - **barrio**: barrio del venue (ej: Palermo, San Telmo)
    - **gratis**: true para solo gratuitos
    - **fecha_desde** / **fecha_hasta**: rango de fechas
    - **page** / **per_page**: paginación
    """
    query = select(Event).options(
        selectinload(Event.venue), selectinload(Event.categoria)
    )

    if categoria:
        query = query.join(
            Category, Event.categoria_id == Category.id, isouter=True
        ).where(func.lower(Category.nombre) == categoria.lower())

    if barrio:
        query = query.join(
            Venue, Event.venue_id == Venue.id, isouter=True
        ).where(func.lower(Venue.barrio) == barrio.lower())

    if gratis is not None:
        query = query.where(Event.es_gratuito.is_(gratis))

    if fecha_desde:
        query = query.where(Event.fecha_inicio >= fecha_desde)

    if fecha_hasta:
        query = query.where(Event.fecha_inicio <= fecha_hasta)

    offset = (page - 1) * per_page
    query = query.order_by(Event.fecha_inicio.asc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    events = list(result.scalars().all())
    return [_serializar_evento(e) for e in events]


@router.get("/{event_id}", response_model=dict[str, Any])
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Obtiene el detalle de un evento por su ID.

    Retorna 404 si el evento no existe.
    """
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.venue), selectinload(Event.categoria))
        .where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return _serializar_evento(event)
