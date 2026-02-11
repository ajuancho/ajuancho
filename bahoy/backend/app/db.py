"""
Bahoy - Configuración de la base de datos
Inicializa el motor y la sesión asíncrona de SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependencia de FastAPI que provee una sesión de base de datos."""
    async with AsyncSessionLocal() as session:
        yield session
