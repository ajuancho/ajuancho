"""
Bahoy - Modelo Category (Categorías jerárquicas)
Representa las categorías de eventos con soporte para subcategorías anidadas.
"""

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class Category(Base, UUIDMixin):
    """
    Modelo para categorías de eventos con jerarquía padre-hijo.
    Permite crear árboles de categorías (ej: "Música" -> "Rock", "Jazz").
    """

    __tablename__ = "categories"

    # Nombre de la categoría (ej: "Teatro", "Música", "Danza")
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # FK a la categoría padre (NULL si es categoría raíz)
    parent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )

    # Nombre del ícono para la UI (ej: "music", "theater_comedy")
    icono: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # -- Relaciones --
    # Categoría padre (si existe)
    parent = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="subcategorias",
    )

    # Subcategorías hijas
    subcategorias = relationship(
        "Category",
        back_populates="parent",
    )

    # Eventos pertenecientes a esta categoría
    eventos = relationship("Event", back_populates="categoria")

    __table_args__ = (
        # Índice para búsquedas por nombre de categoría
        Index("ix_categories_nombre", "nombre"),
        # Índice para obtener subcategorías de una categoría padre
        Index("ix_categories_parent_id", "parent_id"),
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, nombre='{self.nombre}')>"
