# Bahoy

Plataforma de descubrimiento de eventos culturales en Buenos Aires potenciada por IA. Bahoy agrega eventos de múltiples fuentes, aplica procesamiento de lenguaje natural para enriquecer el contenido, y ofrece búsqueda semántica y recomendaciones personalizadas.

---

## Descripción del proyecto

Bahoy resuelve la fragmentación de la agenda cultural porteña: scraping automático de fuentes oficiales (Agenda BA) y plataformas especializadas (Alternativa Teatral), almacenamiento con embeddings vectoriales para búsqueda semántica, y un motor de recomendaciones con análisis de sesgos incorporado.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENTE                                    │
│   Browser / App  →  Next.js 14 (puerto 3000)                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP / REST
┌────────────────────────────▼────────────────────────────────────────┐
│                      BACKEND (FastAPI)                              │
│   Puerto 8000                                                       │
│   ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│   │   Routes    │  │   Services   │  │        NLP             │    │
│   │  /events    │  │ recommender  │  │  sentence-transformers │    │
│   │  /search    │  │ bias_analysis│  │  embeddings (dim=768)  │    │
│   │  /users     │  │ metrics      │  └────────────────────────┘    │
│   │  /admin     │  └──────────────┘                                │
│   └─────────────┘                                                   │
└──────┬──────────────────────────────────────────┬───────────────────┘
       │ asyncpg                                  │ redis.asyncio
┌──────▼───────────────────┐        ┌─────────────▼──────────────────┐
│   PostgreSQL 16           │        │         Redis 7                │
│   + pgvector             │        │   • Cache de respuestas        │
│   • Eventos, usuarios    │        │   • Broker Celery              │
│   • Venues, categorías   │        │   • Backend de resultados      │
│   • Vectores (768d)      │        └────────────────────────────────┘
└──────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│                   CELERY (tareas asíncronas)                        │
│   celery-worker: scraping + NLP                                     │
│   celery-beat: scheduler diario (Agenda BA 6 AM, Teatro 7 AM)      │
│                                                                     │
│   ┌──────────────────────┐  ┌───────────────────────────────────┐  │
│   │  Agenda Buenos Aires │  │    Alternativa Teatral            │  │
│   │  (Scrapy + BS4)      │  │    (Scrapy + Playwright)          │  │
│   └──────────────────────┘  └───────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11, FastAPI 0.109, Uvicorn |
| Frontend | Next.js 14, TypeScript, Tailwind CSS, React Query |
| Base de datos | PostgreSQL 16 + pgvector |
| Cache / Queue | Redis 7 |
| Task queue | Celery 5.3, Celery Beat |
| NLP | sentence-transformers, Hugging Face Transformers |
| Scraping | Scrapy, BeautifulSoup4, Playwright |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| Monitoreo | Loguru (JSON logs), Sentry, Prometheus (opcional) |
| Contenedores | Docker, Docker Compose |

---

## Cómo levantar en desarrollo

### Prerrequisitos

- Docker >= 24 y Docker Compose v2
- (Opcional) Python 3.11+ y Node.js 18+ para desarrollo local sin Docker

### Setup automático (recomendado)

```bash
git clone <url-repositorio>
cd bahoy
./scripts/setup.sh
```

El script instala dependencias, crea el `.env`, levanta Docker, corre migraciones y carga datos de prueba.

### Setup manual paso a paso

**1. Variables de entorno**

```bash
cp .env.example .env
# Editar .env con tus valores (ver sección Variables de entorno)
```

**2. Levantar infraestructura**

```bash
# Servicios principales (PostgreSQL, Redis, Backend, Frontend, Celery)
docker compose up -d

# Con herramientas opcionales (Flower, pgAdmin)
docker compose --profile tools up -d
```

**3. Verificar estado**

```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T12:00:00+00:00",
  "version": "1.0.0",
  "environment": "development",
  "uptime_seconds": 42.1,
  "components": {
    "database": {
      "status": "connected",
      "pgvector": true,
      "extensions": ["vector", "uuid-ossp", "unaccent", "pg_trgm"]
    },
    "redis": {
      "status": "connected",
      "server_version": "7.2.4"
    }
  },
  "check_duration_ms": 12.5
}
```

### Desarrollo local (sin Docker para el código)

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**Worker Celery**

```bash
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

### Servicios disponibles

| Servicio | URL |
|----------|-----|
| API REST | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |
| Métricas Prometheus | http://localhost:8000/metrics |
| Frontend | http://localhost:3000 |
| Flower (Celery UI) | http://localhost:5555 |
| pgAdmin | http://localhost:5050 |

---

## Cómo correr tests

### Backend

```bash
# Todos los tests
cd backend && pytest

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing

# Solo tests unitarios (rápidos)
pytest -m unit

# Solo tests de integración
pytest -m integration

# Via Make
make test
make test-coverage
```

### Frontend

```bash
cd frontend
npm run lint        # ESLint
npm run type-check  # TypeScript
npm run format      # Prettier (check)
```

---

## Cómo deployar

### Opción 1: Railway (recomendado para MVP)

Railway despliega servicios de forma independiente desde el mismo repositorio.

**Requisitos previos:**
- Cuenta en [Railway](https://railway.app)
- CLI de Railway instalada: `npm install -g @railway/cli`

**Pasos:**

```bash
# 1. Login
railway login

# 2. Crear proyecto
railway init

# 3. Agregar addons de base de datos
railway add --plugin postgresql
railway add --plugin redis

# 4. Habilitar pgvector en PostgreSQL
# En el dashboard de Railway → PostgreSQL → Query:
# CREATE EXTENSION IF NOT EXISTS vector;
# CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
# CREATE EXTENSION IF NOT EXISTS unaccent;
# CREATE EXTENSION IF NOT EXISTS pg_trgm;

# 5. Configurar variables de entorno (ver sección Variables de entorno)
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO

# 6. Deploy del backend
railway up

# 7. Para el frontend, crear un segundo servicio apuntando a frontend/
```

La configuración del build está en `railway.json`. El `Procfile` define los procesos disponibles.

**Variables Railway automáticas:**
Railway inyecta `DATABASE_URL` y `REDIS_URL`. Configura el backend para leerlas:

```bash
railway variables set POSTGRES_SERVER=$PGHOST
railway variables set POSTGRES_PORT=$PGPORT
railway variables set POSTGRES_USER=$PGUSER
railway variables set POSTGRES_PASSWORD=$PGPASSWORD
railway variables set POSTGRES_DB=$PGDATABASE
```

### Opción 2: Render

Render usa `render.yaml` para definir todos los servicios en un blueprint.

```bash
# 1. Fork/push del repositorio a GitHub
# 2. En Render Dashboard → New → Blueprint
# 3. Conectar repositorio → Render detecta render.yaml automáticamente
# 4. Configurar SECRET_KEY como variable secreta en el dashboard
# 5. Deploy (Render provisiona PostgreSQL y Redis automáticamente)
```

**Nota:** Render Free tier pone servicios a dormir después de 15 min de inactividad. Para producción usar plan Starter.

### Opción 3: Docker Compose en VPS

```bash
# En el servidor
git clone <url-repositorio>
cd bahoy
cp .env.example .env
# Editar .env con valores de producción
ENVIRONMENT=production docker compose up -d
```

---

## Variables de entorno

Copiar `.env.example` a `.env` y ajustar:

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `ENVIRONMENT` | `development` \| `staging` \| `production` | `development` |
| `DEBUG` | Modo debug (no usar en producción) | `true` |
| `SECRET_KEY` | Clave JWT — generar con `openssl rand -hex 32` | **cambiar** |
| `POSTGRES_SERVER` | Host de PostgreSQL | `localhost` |
| `POSTGRES_PORT` | Puerto de PostgreSQL | `5432` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `bahoy_user` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `bahoy_password` |
| `POSTGRES_DB` | Nombre de la base de datos | `bahoy_db` |
| `REDIS_HOST` | Host de Redis | `localhost` |
| `REDIS_PORT` | Puerto de Redis | `6379` |
| `REDIS_PASSWORD` | Contraseña de Redis (vacío = sin auth) | `` |
| `NEXT_PUBLIC_API_URL` | URL del backend desde el frontend | `http://localhost:8000` |
| `NLP_MODEL_NAME` | Modelo de sentence-transformers | `paraphrase-multilingual-MiniLM-L12-v2` |
| `NLP_DEVICE` | `cpu` o `cuda` | `cpu` |
| `LOG_LEVEL` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` | `INFO` |
| `CACHE_TTL` | TTL de cache en segundos | `3600` |
| `ALLOWED_ORIGINS` | CORS: orígenes permitidos (comma-separated) | `http://localhost:3000` |
| `SENTRY_DSN` | DSN de Sentry (opcional) | — |

---

## Comandos Make disponibles

```bash
make setup          # Setup inicial (copia .env, levanta servicios)
make up             # Levantar todos los servicios
make up-tools       # Levantar con Flower + pgAdmin
make down           # Detener servicios
make build          # Construir imágenes Docker
make rebuild        # Reconstruir sin cache
make logs           # Ver logs de todos los servicios
make logs-backend   # Logs del backend
make logs-worker    # Logs del worker Celery
make test           # Correr tests
make test-coverage  # Tests con cobertura
make migrate        # Aplicar migraciones
make shell-backend  # Shell en el contenedor del backend
make shell-db       # Consola de PostgreSQL
make scrape-all     # Disparar todos los scrapers manualmente
make open           # Mostrar URLs de todos los servicios
```

---

## Migraciones de base de datos

```bash
# Crear nueva migración (detecta cambios en modelos)
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Via Docker
make migrate
make migrate-new MSG="Agregar columna precio_sugerido"
make migrate-down
```

---

## Documentación adicional

- [docs/API.md](docs/API.md) — Documentación completa de endpoints
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Arquitectura, flujo de datos y decisiones técnicas
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — Guía de contribución
- [backend/CELERY_SETUP.md](backend/CELERY_SETUP.md) — Configuración detallada de Celery
