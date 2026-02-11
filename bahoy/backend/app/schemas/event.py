"""
Bahoy - Esquemas Pydantic para Eventos
Modelos de validación de entrada y salida para los endpoints de eventos.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ========== Esquemas auxiliares ==========


class CategoryOut(BaseModel):
    """Categoría resumida para incluir en respuestas de eventos."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    icono: Optional[str] = None


class VenueOut(BaseModel):
    """Venue completo para incluir en respuestas de eventos."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    barrio: Optional[str] = None
    tipo: Optional[str] = None
    capacidad: Optional[int] = None


# ========== GET /api/v1/events ==========


class EventListItem(BaseModel):
    """Evento resumido para listados."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descripcion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    es_gratuito: bool
    imagen_url: Optional[str] = None
    tags: Optional[list[str]] = None
    categoria: Optional[CategoryOut] = None
    venue: Optional[VenueOut] = None


class PaginationInfo(BaseModel):
    """Información de paginación."""

    page: int
    per_page: int
    total: int
    total_pages: int


class EventListResponse(BaseModel):
    """Respuesta paginada del listado de eventos."""

    data: list[EventListItem]
    pagination: PaginationInfo
    filters_applied: dict


# ========== GET /api/v1/events/{id} ==========


class EventSimilar(BaseModel):
    """Evento similar resumido."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    fecha_inicio: Optional[datetime] = None
    imagen_url: Optional[str] = None
    precio_min: Optional[float] = None
    es_gratuito: bool


class PriceHistoryEntry(BaseModel):
    """Entrada del historial de precios."""

    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    fecha_registro: datetime


class EventDetailResponse(BaseModel):
    """Detalle completo de un evento."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descripcion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    es_gratuito: bool
    url_fuente: Optional[str] = None
    imagen_url: Optional[str] = None
    tags: Optional[list[str]] = None
    subcategorias: Optional[list[str]] = None
    categoria: Optional[CategoryOut] = None
    venue: Optional[VenueOut] = None
    eventos_similares: list[EventSimilar] = []
    historial_precios: list[PriceHistoryEntry] = []
    created_at: datetime
    updated_at: datetime


# ========== GET /api/v1/events/destacados ==========


class EventDestacadoItem(BaseModel):
    """Evento destacado con indicador de popularidad."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descripcion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    es_gratuito: bool
    imagen_url: Optional[str] = None
    categoria: Optional[CategoryOut] = None
    venue: Optional[VenueOut] = None
    popularidad: int = 0


class EventDestacadosResponse(BaseModel):
    """Respuesta de eventos destacados para la home."""

    data: list[EventDestacadoItem]
