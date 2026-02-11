# ========== Dockerfile para Backend de Bahoy ==========
# Este archivo define cómo construir la imagen Docker del backend

# Usar imagen oficial de Python 3.11 slim (más liviana)
FROM python:3.11-slim

# Información del mantenedor
LABEL maintainer="equipo@bahoy.com"
LABEL description="Backend de Bahoy - API con FastAPI"

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Variables de entorno para Python
# PYTHONUNBUFFERED: Evita que Python guarde en buffer stdout y stderr (mejor para logs)
# PYTHONDONTWRITEBYTECODE: Evita que Python escriba archivos .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para algunas librerías Python
# - build-essential: Compiladores necesarios para algunas dependencias
# - libpq-dev: Librerías de desarrollo de PostgreSQL
# - curl: Para health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de dependencias primero (para aprovechar cache de Docker)
# Si requirements.txt no cambia, esta capa se reutiliza
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Instalar modelo de spaCy para español (si es necesario)
# Descomentar la siguiente línea si se usa spaCy
# RUN python -m spacy download es_core_news_sm

# Copiar el código de la aplicación
COPY ./app /app/app

# Crear directorio para logs
RUN mkdir -p /app/logs

# Crear usuario no-root para ejecutar la aplicación (seguridad)
RUN useradd -m -u 1000 bahoy && \
    chown -R bahoy:bahoy /app

# Cambiar al usuario no-root
USER bahoy

# Exponer el puerto en el que correrá la aplicación
EXPOSE 8000

# Health check para verificar que el contenedor está saludable
# Docker verificará cada 30 segundos si la aplicación responde
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando para ejecutar la aplicación
# En producción, se recomienda usar gunicorn con uvicorn workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Para producción con gunicorn, usar este comando en su lugar:
# CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
