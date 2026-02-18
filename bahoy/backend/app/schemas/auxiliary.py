"""
Bahoy - Schemas para endpoints auxiliares
Schemas Pydantic para categories, venues, barrios, search suggestions y stats.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ========== Categories ==========


class SubcategoriaResponse(BaseModel):
    id: uuid.UUID
    nombre: str

    model_config = {"from_attributes": True}


class CategoriaResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    icono: str | None
    subcategorias: list[SubcategoriaResponse]
    cantidad_eventos: int

    model_config = {"from_attributes": True}


class CategoriasListResponse(BaseModel):
    categorias: list[CategoriaResponse]


# ========== Venues ==========


class VenueListItem(BaseModel):
    id: uuid.UUID
    nombre: str
    direccion: str | None
    barrio: str | None
    tipo: str | None
    latitud: float | None
    longitud: float | None
    capacidad: int | None
    cantidad_eventos: int

    model_config = {"from_attributes": True}


class VenuesListResponse(BaseModel):
    venues: list[VenueListItem]
    total: int


class EventoEnVenue(BaseModel):
    id: uuid.UUID
    titulo: str
    fecha_inicio: datetime | None
    fecha_fin: datetime | None
    precio_min: float | None
    precio_max: float | None
    es_gratuito: bool
    imagen_url: str | None

    model_config = {"from_attributes": True}


class VenueDetailResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    direccion: str | None
    barrio: str | None
    tipo: str | None
    latitud: float | None
    longitud: float | None
    capacidad: int | None
    proximos_eventos: list[EventoEnVenue]

    model_config = {"from_attributes": True}


# ========== Barrios ==========


class BarrioResponse(BaseModel):
    nombre: str
    cantidad_eventos: int


class BarriosListResponse(BaseModel):
    barrios: list[BarrioResponse]


# ========== Search Suggestions ==========


class SuggestionItem(BaseModel):
    tipo: str  # "evento", "venue", "categoria"
    id: uuid.UUID
    texto: str
    extra: str | None = None


class SearchSuggestionsResponse(BaseModel):
    sugerencias: list[SuggestionItem]


# ========== Stats ==========


class CategoriaStats(BaseModel):
    nombre: str
    cantidad: int


class StatsResponse(BaseModel):
    total_eventos_activos: int
    eventos_por_categoria: list[CategoriaStats]
    eventos_esta_semana: int
