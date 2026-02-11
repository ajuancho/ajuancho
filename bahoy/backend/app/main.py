"""
Bahoy - Punto de entrada principal de la aplicación
Este archivo inicializa la aplicación FastAPI y configura todos los componentes necesarios.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Importar routers cuando estén disponibles
# from app.routes import usuarios, propiedades, busqueda

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="Bahoy API",
    description="API para la plataforma de búsqueda de propiedades Bahoy",
    version="1.0.0",
    docs_url="/docs",  # Documentación Swagger UI
    redoc_url="/redoc"  # Documentación ReDoc
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Lista de orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP
    allow_headers=["*"],  # Permitir todos los headers
)

# Evento que se ejecuta al iniciar la aplicación
@app.on_event("startup")
async def startup_event():
    """
    Inicializa conexiones a bases de datos, cache, etc.
    """
    print("🚀 Iniciando aplicación Bahoy...")
    # TODO: Inicializar conexión a PostgreSQL
    # TODO: Inicializar conexión a Redis
    # TODO: Cargar modelos de NLP si es necesario

# Evento que se ejecuta al cerrar la aplicación
@app.on_event("shutdown")
async def shutdown_event():
    """
    Cierra conexiones y limpia recursos.
    """
    print("👋 Cerrando aplicación Bahoy...")
    # TODO: Cerrar conexión a PostgreSQL
    # TODO: Cerrar conexión a Redis

# Ruta de prueba para verificar que la API está funcionando
@app.get("/")
async def root():
    """
    Endpoint raíz para verificar el estado de la API.
    """
    return {
        "message": "Bienvenido a Bahoy API",
        "status": "online",
        "version": "1.0.0"
    }

# Ruta de health check para monitoreo
@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado de salud de la aplicación.
    Útil para balanceadores de carga y sistemas de monitoreo.
    """
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Verificar conexión real
        "cache": "connected"  # TODO: Verificar conexión real
    }

# Registrar routers cuando estén disponibles
# app.include_router(usuarios.router, prefix="/api/v1/usuarios", tags=["usuarios"])
# app.include_router(propiedades.router, prefix="/api/v1/propiedades", tags=["propiedades"])
# app.include_router(busqueda.router, prefix="/api/v1/busqueda", tags=["busqueda"])

if __name__ == "__main__":
    import uvicorn
    # Ejecutar el servidor en modo desarrollo
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Recarga automática en desarrollo
    )
