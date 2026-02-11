"""
Bahoy - Rutas de usuarios
Endpoints para registro, preferencias, interacciones e historial de usuarios.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.interaction import Interaction, InteractionType
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


# ========== Schemas de request/response ==========


class UserRegisterRequest(BaseModel):
    email: EmailStr
    nombre: str
    preferencias: dict[str, Any] | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    nombre: str | None
    preferencias: dict[str, Any] | None
    ubicacion_habitual: str | None

    model_config = {"from_attributes": True}


class PreferenciasRequest(BaseModel):
    user_id: uuid.UUID
    categorias_favoritas: list[str] | None = None
    barrios_preferidos: list[str] | None = None
    rango_precio: dict[str, int] | None = None
    horarios_preferidos: list[str] | None = None
    tags_interes: list[str] | None = None


class PreferenciasResponse(BaseModel):
    user_id: uuid.UUID
    preferencias: dict[str, Any] | None

    model_config = {"from_attributes": True}


class InteractionRequest(BaseModel):
    event_id: uuid.UUID
    tipo: str  # "vista" | "clic" | "guardado" | "compartido"


class InteractionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_id: uuid.UUID
    tipo: str
    timestamp: Any

    model_config = {"from_attributes": True}


class HistorialItem(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    tipo: str
    timestamp: Any

    model_config = {"from_attributes": True}


# ========== Endpoints ==========


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Registro simple de usuario (sin auth completa por ahora).
    Requiere email (unico) y nombre. Preferencias es opcional.
    """
    # Verificar que el email no exista
    result = await db.execute(select(User).where(User.email == payload.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="El email ya esta registrado")

    user = User(
        email=payload.email,
        nombre=payload.nombre,
        preferencias=payload.preferencias,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/preferences", response_model=PreferenciasResponse)
async def save_preferences(
    payload: PreferenciasRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Guardar o actualizar preferencias del usuario.
    Acepta: categorias_favoritas, barrios_preferidos, rango_precio,
    horarios_preferidos, tags_interes.
    """
    result = await db.execute(select(User).where(User.id == payload.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    prefs: dict[str, Any] = {}
    if payload.categorias_favoritas is not None:
        prefs["categorias_favoritas"] = payload.categorias_favoritas
    if payload.barrios_preferidos is not None:
        prefs["barrios_preferidos"] = payload.barrios_preferidos
    if payload.rango_precio is not None:
        prefs["rango_precio"] = payload.rango_precio
    if payload.horarios_preferidos is not None:
        prefs["horarios_preferidos"] = payload.horarios_preferidos
    if payload.tags_interes is not None:
        prefs["tags_interes"] = payload.tags_interes

    # Merge con preferencias existentes si las hay
    existing_prefs = user.preferencias or {}
    existing_prefs.update(prefs)
    user.preferencias = existing_prefs

    await db.commit()
    await db.refresh(user)
    return {"user_id": user.id, "preferencias": user.preferencias}


@router.get("/{user_id}/preferences", response_model=PreferenciasResponse)
async def get_preferences(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Obtener preferencias actuales del usuario."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"user_id": user.id, "preferencias": user.preferencias}


@router.post("/{user_id}/interactions", response_model=InteractionResponse, status_code=201)
async def register_interaction(
    user_id: uuid.UUID,
    payload: InteractionRequest,
    db: AsyncSession = Depends(get_db),
) -> Interaction:
    """
    Registrar interaccion del usuario con un evento.
    Tipos validos: vista, clic, guardado, compartido.
    """
    # Validar tipo de interaccion
    valid_types = {t.value for t in InteractionType}
    if payload.tipo not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de interaccion invalido. Validos: {sorted(valid_types)}",
        )

    # Verificar que el usuario existe
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    interaction = Interaction(
        user_id=user_id,
        event_id=payload.event_id,
        tipo=InteractionType(payload.tipo),
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return interaction


@router.get("/{user_id}/historial", response_model=list[HistorialItem])
async def get_historial(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[Interaction]:
    """
    Historial de eventos vistos/guardados por el usuario.
    Devuelve interacciones de tipo vista y guardado, ordenadas por timestamp descendente.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    result = await db.execute(
        select(Interaction)
        .where(
            Interaction.user_id == user_id,
            Interaction.tipo.in_([InteractionType.VISTA, InteractionType.GUARDADO]),
        )
        .order_by(Interaction.timestamp.desc())
    )
    return list(result.scalars().all())


@router.get("/{user_id}/guardados", response_model=list[HistorialItem])
async def get_guardados(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[Interaction]:
    """
    Lista de eventos guardados como favoritos por el usuario.
    Devuelve solo interacciones de tipo guardado, ordenadas por timestamp descendente.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    result = await db.execute(
        select(Interaction)
        .where(
            Interaction.user_id == user_id,
            Interaction.tipo == InteractionType.GUARDADO,
        )
        .order_by(Interaction.timestamp.desc())
    )
    return list(result.scalars().all())
