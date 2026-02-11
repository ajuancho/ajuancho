"""
Bahoy - Configuración de base de datos async
Provee el engine SQLAlchemy y la dependencia de sesión para FastAPI.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=settings.DEBUG)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia FastAPI que provee una sesión de base de datos."""
    async with AsyncSessionLocal() as session:
        yield session
