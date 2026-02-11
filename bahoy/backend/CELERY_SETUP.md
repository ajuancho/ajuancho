# Celery - Orquestador de Scrapers

Este documento describe la configuración de Celery para ejecutar scrapers de forma programada en Bahoy.

## 📋 Descripción General

Celery es un sistema de cola de tareas distribuido que se utiliza para ejecutar scrapers de forma asíncrona y programada. Utiliza Redis como broker de mensajes y backend de resultados.

## 🏗️ Arquitectura

```
┌─────────────────┐
│   FastAPI API   │ ──┐
└─────────────────┘   │
                      │  Dispara tareas manualmente
                      ▼
┌─────────────────┐   ┌──────────────┐   ┌─────────────────┐
│  Celery Beat    │──▶│    Redis     │◀──│ Celery Worker   │
│  (Scheduler)    │   │   (Broker)   │   │  (Ejecutor)     │
└─────────────────┘   └──────────────┘   └─────────────────┘
                                                  │
                                                  │ Ejecuta
                                                  ▼
                      ┌─────────────────┐   ┌──────────────┐
                      │   Scrapy        │──▶│  PostgreSQL  │
                      │   Spiders       │   │  (Storage)   │
                      └─────────────────┘   └──────────────┘
```

## 📁 Estructura de Archivos

```
bahoy/backend/app/
├── celery_app.py         # Configuración de Celery y scheduler
├── tasks.py              # Definición de tareas (scrapers)
├── routes/
│   └── admin.py          # Endpoints para disparar scrapers manualmente
└── scrapers/
    ├── agenda_ba_spider.py
    └── alternativa_teatral_spider.py
```

## 🚀 Servicios Docker

### 1. Celery Worker
Ejecuta las tareas asíncronas (scrapers).

```bash
docker-compose up -d celery-worker
```

**Comando:** `celery -A app.celery_app worker --loglevel=info --concurrency=2`

**Configuración:**
- Concurrencia: 2 workers simultáneos
- Loglevel: INFO
- Prefetch multiplier: 1 (una tarea a la vez)
- Max tasks per child: 50 (previene memory leaks)

### 2. Celery Beat
Programa y dispara tareas según el calendario definido.

```bash
docker-compose up -d celery-beat
```

**Comando:** `celery -A app.celery_app beat --loglevel=info`

**Tareas programadas:**
- **Agenda BA**: Diariamente a las 6:00 AM (Buenos Aires)
- **Alternativa Teatral**: Diariamente a las 7:00 AM (Buenos Aires)

### 3. Flower (Opcional)
Interfaz web para monitorear Celery.

```bash
docker-compose --profile tools up -d flower
```

**Acceso:** http://localhost:5555

## 📝 Tareas Disponibles

### 1. task_scrape_agenda_ba
Ejecuta el scraper de Agenda Buenos Aires.

**Programación:** Diaria a las 6:00 AM
**Reintentos:** 3 intentos con backoff exponencial
**Timeout:** 1 hora

```python
from app.tasks import task_scrape_agenda_ba

# Ejecutar inmediatamente
task = task_scrape_agenda_ba.delay()
print(f"Task ID: {task.id}")
```

### 2. task_scrape_alternativa_teatral
Ejecuta el scraper de Alternativa Teatral.

**Programación:** Diaria a las 7:00 AM
**Reintentos:** 3 intentos con backoff exponencial
**Timeout:** 1 hora

```python
from app.tasks import task_scrape_alternativa_teatral

# Ejecutar inmediatamente
task = task_scrape_alternativa_teatral.delay()
print(f"Task ID: {task.id}")
```

### 3. task_full_scrape
Ejecuta todos los scrapers en secuencia.

**Programación:** Manual (no programada)
**Reintentos:** 3 intentos con backoff exponencial
**Timeout:** 1 hora

```python
from app.tasks import task_full_scrape

# Ejecutar todos los scrapers
task = task_full_scrape.delay()
print(f"Task ID: {task.id}")
```

## 🌐 API Endpoints

### Disparar Scraper Manualmente

```http
POST /api/v1/admin/scrape/{source_name}
```

**Parámetros:**
- `source_name`: Nombre del scraper
  - `agenda_ba`: Scraper de Agenda Buenos Aires
  - `alternativa_teatral`: Scraper de Alternativa Teatral
  - `all`: Todos los scrapers

**Ejemplo con curl:**

```bash
# Scraper de Agenda BA
curl -X POST http://localhost:8000/api/v1/admin/scrape/agenda_ba

# Scraper de Alternativa Teatral
curl -X POST http://localhost:8000/api/v1/admin/scrape/alternativa_teatral

# Todos los scrapers
curl -X POST http://localhost:8000/api/v1/admin/scrape/all
```

**Respuesta:**

```json
{
  "message": "Scraper 'agenda_ba' iniciado exitosamente",
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "source": "agenda_ba",
  "status": "pending"
}
```

### Obtener Estado de Tarea

```http
GET /api/v1/admin/scrape/status/{task_id}
```

**Ejemplo:**

```bash
curl http://localhost:8000/api/v1/admin/scrape/status/a1b2c3d4-5678-90ab-cdef-1234567890ab
```

**Respuesta (en progreso):**

```json
{
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "state": "PENDING"
}
```

**Respuesta (completada):**

```json
{
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "state": "SUCCESS",
  "result": {
    "status": "success",
    "spider": "agenda_ba",
    "start_time": "2024-03-15T06:00:00",
    "end_time": "2024-03-15T06:05:30",
    "duration_seconds": 330
  }
}
```

### Listar Scrapers Disponibles

```http
GET /api/v1/admin/scrape/list
```

**Ejemplo:**

```bash
curl http://localhost:8000/api/v1/admin/scrape/list
```

**Respuesta:**

```json
{
  "scrapers": [
    {
      "name": "agenda_ba",
      "description": "Scraper de Agenda Buenos Aires",
      "source": "https://turismo.buenosaires.gob.ar/es/agenda",
      "schedule": "Diario a las 6:00 AM",
      "endpoint": "/api/v1/admin/scrape/agenda_ba"
    },
    {
      "name": "alternativa_teatral",
      "description": "Scraper de Alternativa Teatral",
      "source": "https://www.alternativateatral.com/cartelera",
      "schedule": "Diario a las 7:00 AM",
      "endpoint": "/api/v1/admin/scrape/alternativa_teatral"
    },
    {
      "name": "all",
      "description": "Ejecuta todos los scrapers en secuencia",
      "schedule": "Manual",
      "endpoint": "/api/v1/admin/scrape/all"
    }
  ],
  "total": 3
}
```

## 🔧 Configuración

### Variables de Entorno

Las siguientes variables de entorno son necesarias:

```bash
# Redis (Broker de Celery)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# PostgreSQL (Storage de eventos)
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_USER=bahoy_user
POSTGRES_PASSWORD=bahoy_password
POSTGRES_DB=bahoy_db
```

### Configuración de Celery

Ver `app/celery_app.py` para la configuración completa.

**Parámetros clave:**
- **Zona horaria:** America/Argentina/Buenos_Aires
- **Result expiry:** 3600 segundos (1 hora)
- **Task time limit:** 3600 segundos (1 hora)
- **Task soft time limit:** 3300 segundos (55 minutos)
- **Worker prefetch:** 1 tarea a la vez
- **Worker max tasks per child:** 50

### Modificar el Calendario

Para cambiar los horarios de ejecución, edita el `beat_schedule` en `app/celery_app.py`:

```python
beat_schedule={
    "scrape-agenda-ba-daily": {
        "task": "app.tasks.task_scrape_agenda_ba",
        "schedule": crontab(hour=6, minute=0),  # 6:00 AM
        "options": {
            "expires": 3600,
        }
    },
    # Ejemplo: Ejecutar cada 12 horas
    "scrape-alternativa-teatral-twice-daily": {
        "task": "app.tasks.task_scrape_alternativa_teatral",
        "schedule": crontab(hour="*/12", minute=0),  # Cada 12 horas
        "options": {
            "expires": 3600,
        }
    },
}
```

**Ejemplos de crontab:**
- `crontab(hour=6, minute=0)` - Diario a las 6:00 AM
- `crontab(hour="*/6", minute=0)` - Cada 6 horas
- `crontab(day_of_week=1, hour=9, minute=0)` - Lunes a las 9:00 AM
- `crontab(minute="*/30")` - Cada 30 minutos

## 🐛 Troubleshooting

### Ver logs del worker

```bash
docker-compose logs -f celery-worker
```

### Ver logs del scheduler

```bash
docker-compose logs -f celery-beat
```

### Reiniciar los servicios de Celery

```bash
docker-compose restart celery-worker celery-beat
```

### Purgar todas las tareas pendientes

```bash
docker-compose exec celery-worker celery -A app.celery_app purge
```

### Inspeccionar tareas activas

```bash
docker-compose exec celery-worker celery -A app.celery_app inspect active
```

### Ver tareas programadas

```bash
docker-compose exec celery-worker celery -A app.celery_app inspect scheduled
```

### Verificar la configuración

```bash
docker-compose exec celery-worker celery -A app.celery_app inspect conf
```

## 📊 Monitoreo con Flower

Flower proporciona una interfaz web para monitorear Celery en tiempo real.

**Iniciar Flower:**

```bash
docker-compose --profile tools up -d flower
```

**Acceder:**

Abre http://localhost:5555 en tu navegador.

**Funcionalidades:**
- Ver tareas activas, completadas y fallidas
- Monitorear workers en tiempo real
- Ver estadísticas de rendimiento
- Reintentar tareas fallidas
- Ver cola de tareas pendientes

## 🧪 Testing

### Tarea de Prueba

Ejecuta una tarea de prueba para verificar que Celery está funcionando:

```bash
curl -X POST "http://localhost:8000/api/v1/admin/test/celery?message=Hola%20Celery"
```

### Ejecutar Scraper de Forma Local

Para probar un scraper sin Celery:

```bash
cd bahoy/backend
python app/scrapers/run_scraper.py --spider agenda_ba --debug
```

## 🔒 Manejo de Errores

### Reintentos Automáticos

Todas las tareas de scraping tienen configuración de reintentos automáticos:

- **Max retries:** 3 intentos
- **Countdown:** 300 segundos (5 minutos) entre reintentos
- **Retry backoff:** Activado (backoff exponencial)
- **Retry jitter:** Activado (añade variación aleatoria)

### Logging

Todos los scrapers registran:
- ✅ Hora de inicio
- ✅ Hora de finalización
- ✅ Duración de la ejecución
- ✅ ID de la tarea
- ❌ Errores detallados con stack trace

Los logs se guardan en `/app/logs/` dentro del contenedor.

## 📚 Referencias

- [Celery Documentation](https://docs.celeryq.dev/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [Scrapy Documentation](https://docs.scrapy.org/)
- [Redis Documentation](https://redis.io/documentation)

## ✅ Checklist de Implementación

- [x] Configuración de Celery (`celery_app.py`)
- [x] Definición de tareas (`tasks.py`)
- [x] Configuración de Celery Beat (scheduler)
- [x] Endpoints de API para disparar scrapers manualmente
- [x] Manejo de errores y reintentos
- [x] Logging completo
- [x] Docker Compose con worker y beat
- [x] Flower para monitoreo (opcional)
- [x] Documentación completa

## 🎯 Próximos Pasos

1. **Agregar más scrapers**: Añadir nuevos spiders en `app/scrapers/`
2. **Notificaciones**: Implementar notificaciones por email/Slack en caso de errores
3. **Métricas**: Integrar con Prometheus/Grafana para métricas avanzadas
4. **Rate limiting**: Implementar limitación de tasa por fuente
5. **Prioridades**: Añadir priorización de tareas
