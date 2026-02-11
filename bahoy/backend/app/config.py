"""
Bahoy - Configuración de la aplicación
Este archivo contiene todas las configuraciones y variables de entorno de la aplicación.
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """
    Configuraciones de la aplicación usando Pydantic Settings.
    Las variables se cargan automáticamente desde variables de entorno o archivo .env
    """

    # ========== Configuración General ==========
    APP_NAME: str = "Bahoy"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production

    # ========== Configuración de la API ==========
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "tu-clave-secreta-super-segura-cambiar-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ========== Configuración de CORS ==========
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend en desarrollo
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # ========== Configuración de PostgreSQL ==========
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "bahoy_user"
    POSTGRES_PASSWORD: str = "bahoy_password"
    POSTGRES_DB: str = "bahoy_db"

    @property
    def DATABASE_URL(self) -> str:
        """
        Construye la URL de conexión a PostgreSQL.
        Formato: postgresql://usuario:contraseña@servidor:puerto/base_de_datos
        """
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        URL de conexión asíncrona para PostgreSQL con asyncpg.
        """
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # ========== Configuración de Redis ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        """
        Construye la URL de conexión a Redis.
        """
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ========== Configuración de pgvector ==========
    VECTOR_DIMENSION: int = 768  # Dimensión de los embeddings (depende del modelo de NLP)
    SIMILARITY_THRESHOLD: float = 0.7  # Umbral de similitud para búsquedas semánticas

    # ========== Configuración de NLP ==========
    NLP_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    NLP_DEVICE: str = "cpu"  # "cpu" o "cuda" para GPU
    MAX_SEQUENCE_LENGTH: int = 512

    # ========== Configuración de Web Scraping ==========
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    SCRAPER_TIMEOUT: int = 30  # Timeout en segundos
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_DELAY: float = 1.0  # Delay entre requests en segundos

    # ========== Configuración de Cache ==========
    CACHE_TTL: int = 3600  # Tiempo de vida del cache en segundos (1 hora)
    CACHE_ENABLED: bool = True

    # ========== Configuración de Logging ==========
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: str = "logs/bahoy.log"

    # ========== Configuración de Paginación ==========
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        """
        Configuración de Pydantic Settings.
        """
        env_file = ".env"  # Archivo de variables de entorno
        env_file_encoding = "utf-8"
        case_sensitive = True  # Las variables son sensibles a mayúsculas

# Instancia global de configuración
# Esta instancia se importa en toda la aplicación
settings = Settings()

# Función auxiliar para verificar el entorno
def is_production() -> bool:
    """
    Verifica si la aplicación está en modo producción.
    """
    return settings.ENVIRONMENT == "production"

def is_development() -> bool:
    """
    Verifica si la aplicación está en modo desarrollo.
    """
    return settings.ENVIRONMENT == "development"
