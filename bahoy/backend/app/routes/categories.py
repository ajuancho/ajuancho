"""
Bahoy - Rutas de categorías
Endpoint para obtener el árbol jerárquico de categorías con subcategorías.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.category import Category
from app.models.event import Event
from app.schemas.auxiliary import (
    CategoriaResponse,
    CategoriasListResponse,
    SubcategoriaResponse,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoriasListResponse)
async def get_categories(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Obtiene el árbol jerárquico de categorías.
    Devuelve solo las categorías raíz (sin parent) con sus subcategorías
    anidadas y la cantidad de eventos asociados a cada una.
    """
    # Obtener categorías raíz con sus subcategorías pre-cargadas
    result = await db.execute(
        select(Category)
        .where(Category.parent_id.is_(None))
        .options(selectinload(Category.subcategorias))
        .order_by(Category.nombre)
    )
    root_categories = result.scalars().all()

    categorias = []
    for cat in root_categories:
        # Contar eventos de la categoría padre + todos los de sus subcategorías
        sub_ids = [sub.id for sub in cat.subcategorias]
        all_ids = [cat.id] + sub_ids

        count_result = await db.execute(
            select(func.count(Event.id)).where(Event.categoria_id.in_(all_ids))
        )
        cantidad = count_result.scalar() or 0

        categorias.append(
            CategoriaResponse(
                id=cat.id,
                nombre=cat.nombre,
                icono=cat.icono,
                subcategorias=[
                    SubcategoriaResponse(id=sub.id, nombre=sub.nombre)
                    for sub in cat.subcategorias
                ],
                cantidad_eventos=cantidad,
            )
        )

    return {"categorias": categorias}
