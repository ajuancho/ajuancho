"""
Bahoy - API de Eventos
Endpoints para listar, buscar y obtener detalles de eventos culturales.
"""

import math
from datetime import date, datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.category import Category
from app.models.event import Event
from app.models.interaction import Interaction
from app.models.venue import Venue
from app.schemas.event import (
    CategoryOut,
    EventDestacadoItem,
    EventDestacadosResponse,
    EventDetailResponse,
    EventListItem,
    EventListResponse,
    EventSimilar,
    PaginationInfo,
    PriceHistoryEntry,
    VenueOut,
)

router = APIRouter(prefix="/events", tags=["events"])


# ========== GET /api/v1/events ==========


@router.get(
    "",
    response_model=EventListResponse,
    summary="Listar eventos con filtros y paginación",
    description=(
        "Lista eventos culturales con filtros avanzados y paginación. "
        "Soporta filtrado por categoría, fecha, ubicación, precio, tags y texto libre. "
        "Incluye búsqueda geográfica por coordenadas con radio en kilómetros."
    ),
)
async def list_events(
    categoria: Optional[str] = Query(
        None, description="Filtrar por nombre de categoría (ej: 'Teatro')"
    ),
    subcategoria: Optional[str] = Query(
        None, description="Filtrar por subcategoría"
    ),
    fecha_desde: Optional[date] = Query(
        None, description="Fecha mínima (YYYY-MM-DD)"
    ),
    fecha_hasta: Optional[date] = Query(
        None, description="Fecha máxima (YYYY-MM-DD)"
    ),
    barrio: Optional[str] = Query(
        None, description="Filtrar por barrio del venue"
    ),
    precio_max: Optional[float] = Query(
        None, ge=0, description="Precio máximo"
    ),
    gratuito: Optional[bool] = Query(
        None, description="Solo eventos gratuitos (true/false)"
    ),
    busqueda: Optional[str] = Query(
        None,
        min_length=1,
        max_length=200,
        description="Texto libre para buscar en título/descripción",
    ),
    tags: Optional[str] = Query(
        None, description="Lista de tags separados por coma"
    ),
    lat: Optional[float] = Query(
        None, ge=-90, le=90, description="Latitud para búsqueda geográfica"
    ),
    lng: Optional[float] = Query(
        None, ge=-180, le=180, description="Longitud para búsqueda geográfica"
    ),
    radio_km: Optional[float] = Query(
        None, gt=0, le=100, description="Radio en kilómetros"
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Eventos por página"),
    orden: Literal["fecha", "precio", "relevancia"] = Query(
        "fecha", description="Criterio de ordenamiento"
    ),
    db: AsyncSession = Depends(get_db),
) -> EventListResponse:
    # Base queries
    query = select(Event).options(
        selectinload(Event.categoria),
        selectinload(Event.venue),
    )
    count_query = select(func.count()).select_from(Event)

    # Track joins and conditions
    conditions: list = []
    needs_category_join = False
    needs_venue_join = False
    filters_applied: dict = {}

    # -- Filtro por categoría --
    if categoria:
        needs_category_join = True
        conditions.append(func.lower(Category.nombre) == func.lower(categoria))
        filters_applied["categoria"] = categoria

    # -- Filtro por subcategoría --
    if subcategoria:
        conditions.append(Event.subcategorias.contains([subcategoria]))
        filters_applied["subcategoria"] = subcategoria

    # -- Filtro por rango de fechas --
    if fecha_desde:
        dt_desde = datetime(
            fecha_desde.year, fecha_desde.month, fecha_desde.day,
            tzinfo=timezone.utc,
        )
        conditions.append(Event.fecha_inicio >= dt_desde)
        filters_applied["fecha_desde"] = fecha_desde.isoformat()

    if fecha_hasta:
        dt_hasta = datetime(
            fecha_hasta.year, fecha_hasta.month, fecha_hasta.day,
            23, 59, 59, tzinfo=timezone.utc,
        )
        conditions.append(Event.fecha_inicio <= dt_hasta)
        filters_applied["fecha_hasta"] = fecha_hasta.isoformat()

    # -- Filtro por barrio --
    if barrio:
        needs_venue_join = True
        conditions.append(func.lower(Venue.barrio) == func.lower(barrio))
        filters_applied["barrio"] = barrio

    # -- Filtro por precio máximo --
    if precio_max is not None:
        conditions.append(Event.precio_min <= precio_max)
        filters_applied["precio_max"] = precio_max

    # -- Filtro por gratuito --
    if gratuito is not None:
        conditions.append(Event.es_gratuito == gratuito)
        filters_applied["gratuito"] = gratuito

    # -- Búsqueda de texto libre --
    if busqueda:
        safe_search = busqueda.replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{safe_search}%"
        conditions.append(
            or_(
                Event.titulo.ilike(pattern),
                Event.descripcion.ilike(pattern),
            )
        )
        filters_applied["busqueda"] = busqueda

    # -- Filtro por tags --
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            conditions.append(Event.tags.overlap(tag_list))
            filters_applied["tags"] = tag_list

    # -- Búsqueda geográfica --
    if lat is not None and lng is not None and radio_km is not None:
        needs_venue_join = True
        # Fórmula de Haversine en SQL
        haversine = 6371.0 * func.acos(
            func.greatest(
                -1.0,
                func.least(
                    1.0,
                    func.cos(func.radians(lat))
                    * func.cos(func.radians(Venue.latitud))
                    * func.cos(func.radians(Venue.longitud) - func.radians(lng))
                    + func.sin(func.radians(lat))
                    * func.sin(func.radians(Venue.latitud)),
                ),
            )
        )
        conditions.append(Venue.latitud.isnot(None))
        conditions.append(Venue.longitud.isnot(None))
        conditions.append(haversine <= radio_km)
        filters_applied["lat"] = lat
        filters_applied["lng"] = lng
        filters_applied["radio_km"] = radio_km

    # -- Aplicar JOINs necesarios --
    if needs_category_join:
        query = query.join(Category, Event.categoria_id == Category.id)
        count_query = count_query.join(Category, Event.categoria_id == Category.id)

    if needs_venue_join:
        query = query.join(Venue, Event.venue_id == Venue.id)
        count_query = count_query.join(Venue, Event.venue_id == Venue.id)

    # -- Aplicar condiciones --
    if conditions:
        combined = and_(*conditions)
        query = query.where(combined)
        count_query = count_query.where(combined)

    # -- Obtener total --
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    total_pages = math.ceil(total / per_page) if total > 0 else 0

    # -- Ordenamiento --
    if orden == "fecha":
        query = query.order_by(Event.fecha_inicio.asc().nulls_last())
    elif orden == "precio":
        query = query.order_by(Event.precio_min.asc().nulls_last())
    elif orden == "relevancia":
        # Relevancia: fecha más próxima primero, luego más recientes
        query = query.order_by(
            Event.fecha_inicio.asc().nulls_last(),
            Event.created_at.desc(),
        )

    # -- Paginación --
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # -- Ejecutar consulta --
    result = await db.execute(query)
    events = result.scalars().all()

    return EventListResponse(
        data=[EventListItem.model_validate(e) for e in events],
        pagination=PaginationInfo(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
        filters_applied=filters_applied,
    )


# ========== GET /api/v1/events/destacados ==========
# IMPORTANTE: Este endpoint debe estar ANTES de /{event_id}
# para que FastAPI no interprete "destacados" como un UUID.


@router.get(
    "/destacados",
    response_model=EventDestacadosResponse,
    summary="Eventos destacados para la home",
    description=(
        "Retorna los próximos 5 eventos más relevantes, "
        "ordenados por fecha próxima y popularidad (cantidad de interacciones)."
    ),
)
async def get_featured_events(
    db: AsyncSession = Depends(get_db),
) -> EventDestacadosResponse:
    now = datetime.now(timezone.utc)

    # Subquery correlacionada: contar interacciones por evento
    interaction_count = (
        select(func.count(Interaction.id))
        .where(Interaction.event_id == Event.id)
        .correlate(Event)
        .scalar_subquery()
        .label("popularidad")
    )

    query = (
        select(Event, interaction_count)
        .options(
            selectinload(Event.categoria),
            selectinload(Event.venue),
        )
        .where(Event.fecha_inicio >= now)
        .order_by(Event.fecha_inicio.asc(), interaction_count.desc())
        .limit(5)
    )

    result = await db.execute(query)
    rows = result.all()

    data = []
    for event, popularidad in rows:
        item = EventDestacadoItem(
            id=event.id,
            titulo=event.titulo,
            descripcion=event.descripcion,
            fecha_inicio=event.fecha_inicio,
            precio_min=event.precio_min,
            precio_max=event.precio_max,
            es_gratuito=event.es_gratuito,
            imagen_url=event.imagen_url,
            categoria=(
                CategoryOut.model_validate(event.categoria)
                if event.categoria
                else None
            ),
            venue=(
                VenueOut.model_validate(event.venue)
                if event.venue
                else None
            ),
            popularidad=popularidad or 0,
        )
        data.append(item)

    return EventDestacadosResponse(data=data)


# ========== GET /api/v1/events/{event_id} ==========


@router.get(
    "/{event_id}",
    response_model=EventDetailResponse,
    summary="Detalle completo de un evento",
    description=(
        "Retorna el detalle completo de un evento incluyendo información del venue, "
        "eventos similares (misma categoría o fecha cercana) e historial de precios."
    ),
)
async def get_event_detail(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EventDetailResponse:
    # Obtener evento con relaciones cargadas
    query = (
        select(Event)
        .options(
            selectinload(Event.categoria),
            selectinload(Event.venue),
        )
        .where(Event.id == event_id)
    )
    result = await db.execute(query)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # -- Eventos similares (misma categoría O fecha cercana, excluyendo el actual) --
    similar_or_conditions: list = []

    if event.categoria_id:
        similar_or_conditions.append(Event.categoria_id == event.categoria_id)

    if event.fecha_inicio:
        delta = timedelta(days=7)
        similar_or_conditions.append(
            Event.fecha_inicio.between(
                event.fecha_inicio - delta,
                event.fecha_inicio + delta,
            )
        )

    similar_events: list = []
    if similar_or_conditions:
        similar_query = (
            select(Event)
            .where(
                and_(
                    Event.id != event_id,
                    or_(*similar_or_conditions),
                )
            )
            .order_by(Event.fecha_inicio.asc().nulls_last())
            .limit(5)
        )
        similar_result = await db.execute(similar_query)
        similar_events = list(similar_result.scalars().all())

    # -- Historial de precios --
    # El modelo actual no tiene tabla de historial de precios.
    # Se retorna el precio actual como único registro disponible.
    historial: list[PriceHistoryEntry] = []
    if event.precio_min is not None or event.precio_max is not None:
        historial.append(
            PriceHistoryEntry(
                precio_min=float(event.precio_min) if event.precio_min is not None else None,
                precio_max=float(event.precio_max) if event.precio_max is not None else None,
                fecha_registro=event.created_at,
            )
        )

    return EventDetailResponse(
        id=event.id,
        titulo=event.titulo,
        descripcion=event.descripcion,
        fecha_inicio=event.fecha_inicio,
        fecha_fin=event.fecha_fin,
        precio_min=event.precio_min,
        precio_max=event.precio_max,
        es_gratuito=event.es_gratuito,
        url_fuente=event.url_fuente,
        imagen_url=event.imagen_url,
        tags=event.tags,
        subcategorias=event.subcategorias,
        categoria=(
            CategoryOut.model_validate(event.categoria)
            if event.categoria
            else None
        ),
        venue=(
            VenueOut.model_validate(event.venue)
            if event.venue
            else None
        ),
        eventos_similares=[
            EventSimilar.model_validate(e) for e in similar_events
        ],
        historial_precios=historial,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
