"""
Bahoy - Modelo User (Usuarios)
Representa a los usuarios de la plataforma con sus preferencias personalizadas.
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    Modelo para los usuarios de Bahoy.
    Almacena perfil básico y preferencias para personalizar recomendaciones.
    """

    __tablename__ = "users"

    # Email del usuario (único, usado para autenticación)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # Nombre del usuario
    nombre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Preferencias del usuario en formato JSON.
    # Estructura esperada:
    # {
    #     "categorias_favoritas": ["teatro", "música"],
    #     "barrios_favoritos": ["Palermo", "San Telmo"],
    #     "rango_precios": {"min": 0, "max": 5000},
    #     "dias_preferidos": ["viernes", "sábado"]
    # }
    preferencias: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Barrio habitual del usuario (para recomendaciones por cercanía)
    ubicacion_habitual: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # -- Relaciones --
    # Interacciones del usuario con eventos
    interacciones = relationship("Interaction", back_populates="user")

    __table_args__ = (
        # Índice único para búsqueda y login por email
        Index("ix_users_email", "email", unique=True),
        # Índice para filtrar usuarios por barrio
        Index("ix_users_ubicacion_habitual", "ubicacion_habitual"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
