"""
Bahoy - Punto de entrada principal de la aplicación
Este archivo inicializa la aplicación FastAPI y configura todos los componentes necesarios.
"""

import sys
import time
from datetime import datetime, timezone

import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings

# Importar routers
from app.routes import admin, barrios, categories, events, recommendations, search, stats, users, venues
# from app.routes import propiedades, busqueda

# ── Logging estructurado (JSON en producción) ──────────────────────────────────
logger.remove()  # Eliminar handler por defecto

if settings.ENVIRONMENT == "production":
    # JSON estructurado para parseo en sistemas de log centralizados
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        serialize=True,  # JSON output
        backtrace=False,
        diagnose=False,
    )
else:
    # Formato legible en desarrollo
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

# Log a archivo siempre (rotación diaria, retención 7 días)
logger.add(
    settings.LOG_FILE,
    level=settings.LOG_LEVEL,
    serialize=True,  # JSON en archivo para facilitar análisis
    rotation="00:00",
    retention="7 days",
    compression="gz",
    encoding="utf-8",
    enqueue=True,  # Thread-safe
)

# ── Timestamp de inicio (para calcular uptime en /health) ─────────────────────
_START_TIME = time.time()

# ── Inicializar la aplicación FastAPI ─────────────────────────────────────────
app = FastAPI(
    title="Bahoy API",
    description="API para la plataforma de búsqueda de eventos culturales en Buenos Aires",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware de logging de requests ─────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    """Loguea cada request con método, ruta, status y duración."""
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "HTTP request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        client=request.client.host if request.client else "unknown",
    )
    return response


# ── Eventos del ciclo de vida ─────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando aplicación Bahoy", environment=settings.ENVIRONMENT, version=settings.APP_VERSION)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Cerrando aplicación Bahoy")


# ── Raíz ──────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    """Endpoint raíz para verificar que la API está online."""
    return {
        "message": "Bienvenido a Bahoy API",
        "status": "online",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# ── Health Check detallado ─────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """
    Health check detallado del sistema.

    Verifica el estado de todos los componentes críticos:
    - PostgreSQL (conectividad y extensión pgvector)
    - Redis (ping y versión del servidor)
    - Uptime de la aplicación

    Devuelve `status: ok` solo si todos los componentes están operativos.
    Devuelve `status: degraded` si algún componente falla.
    """
    check_start = time.time()

    result = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "components": {
            "database": {
                "status": "disconnected",
                "pgvector": False,
                "extensions": [],
                "error": None,
            },
            "redis": {
                "status": "disconnected",
                "server_version": None,
                "error": None,
            },
        },
    }

    # ── Verificar PostgreSQL ───────────────────────────────────────────────────
    try:
        conn = await asyncpg.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            timeout=5,
        )
        try:
            # Versión de PostgreSQL
            pg_version = await conn.fetchval("SELECT version()")
            # Extensiones instaladas
            ext_rows = await conn.fetch(
                "SELECT extname FROM pg_extension WHERE extname = ANY($1::text[])",
                ["vector", "uuid-ossp", "unaccent", "pg_trgm"],
            )
            extensions = [r["extname"] for r in ext_rows]

            result["components"]["database"].update(
                {
                    "status": "connected",
                    "pgvector": "vector" in extensions,
                    "extensions": extensions,
                    "pg_version": pg_version.split(",")[0] if pg_version else None,
                    "error": None,
                }
            )
        finally:
            await conn.close()
    except Exception as exc:
        result["components"]["database"]["error"] = str(exc)
        result["status"] = "degraded"
        logger.warning("Health check: PostgreSQL no disponible", error=str(exc))

    # ── Verificar Redis ────────────────────────────────────────────────────────
    try:
        r = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        try:
            if await r.ping():
                info = await r.info("server")
                result["components"]["redis"].update(
                    {
                        "status": "connected",
                        "server_version": info.get("redis_version"),
                        "error": None,
                    }
                )
        finally:
            await r.aclose()
    except Exception as exc:
        result["components"]["redis"]["error"] = str(exc)
        result["status"] = "degraded"
        logger.warning("Health check: Redis no disponible", error=str(exc))

    result["check_duration_ms"] = round((time.time() - check_start) * 1000, 2)

    return result


# ── Métricas Prometheus (opcional) ───────────────────────────────────────────
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )

    REQUEST_COUNT = Counter(
        "bahoy_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "bahoy_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "endpoint"],
    )

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Expone métricas en formato Prometheus."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    logger.info("Endpoint /metrics de Prometheus habilitado.")
except ImportError:
    logger.debug("prometheus_client no instalado. Endpoint /metrics no disponible.")


# ── Registrar routers ──────────────────────────────────────────────────────────
app.include_router(admin.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(venues.router, prefix="/api")
app.include_router(barrios.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
# app.include_router(propiedades.router, prefix="/api/v1/propiedades", tags=["propiedades"])
# app.include_router(busqueda.router, prefix="/api/v1/busqueda", tags=["busqueda"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
