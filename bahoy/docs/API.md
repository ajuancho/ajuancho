# Bahoy API — Documentación de Endpoints

Base URL: `http://localhost:8000`
Formato: JSON
Codificación: UTF-8
Paginación: parámetros `page` (1-based) y `per_page` (máx 100)

La documentación interactiva con ejemplos en vivo está disponible en:
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`

---

## Índice

- [Sistema](#sistema)
- [Eventos](#eventos)
- [Búsqueda y Sugerencias](#búsqueda-y-sugerencias)
- [Usuarios](#usuarios)
- [Recomendaciones](#recomendaciones)
- [Venues](#venues)
- [Categorías](#categorías)
- [Barrios](#barrios)
- [Estadísticas](#estadísticas)
- [Admin](#admin)
- [Códigos de error](#códigos-de-error)

---

## Sistema

### `GET /`

Verifica que la API está online.

**Response 200**
```json
{
  "message": "Bienvenido a Bahoy API",
  "status": "online",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### `GET /health`

Health check detallado. Verifica PostgreSQL, pgvector y Redis.

**Response 200 — Todo OK**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T15:30:00+00:00",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600.5,
  "components": {
    "database": {
      "status": "connected",
      "pgvector": true,
      "extensions": ["vector", "uuid-ossp", "unaccent", "pg_trgm"],
      "pg_version": "PostgreSQL 16.1"
    },
    "redis": {
      "status": "connected",
      "server_version": "7.2.4"
    }
  },
  "check_duration_ms": 15.2
}
```

**Response 200 — Degradado** (`status: "degraded"` si algún componente falla)
```json
{
  "status": "degraded",
  "components": {
    "database": {
      "status": "disconnected",
      "error": "Connection refused"
    },
    "redis": { "status": "connected", "server_version": "7.2.4" }
  }
}
```

---

### `GET /metrics`

Métricas en formato Prometheus (requiere `prometheus-client` instalado).

**Response 200** — Texto plano en formato Prometheus exposition format.

---

## Eventos

Base path: `/api/events`

### `GET /api/events`

Lista eventos con filtros opcionales y paginación.

**Query params**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `categoria` | string | Filtrar por nombre de categoría (ej: `teatro`) |
| `barrio` | string | Filtrar por barrio del venue (ej: `Palermo`) |
| `gratis` | boolean | `true` para solo eventos gratuitos |
| `fecha_desde` | datetime ISO 8601 | Fecha de inicio mínima |
| `fecha_hasta` | datetime ISO 8601 | Fecha de inicio máxima |
| `page` | int ≥ 1 | Página (default: 1) |
| `per_page` | int 1–100 | Resultados por página (default: 20) |

**Request**
```
GET /api/events?categoria=teatro&barrio=palermo&gratis=false&page=1&per_page=10
```

**Response 200**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "titulo": "La Gaviota — Teatro San Martín",
    "descripcion": "Obra clásica de Chéjov con producción nacional...",
    "categoria": "Teatro",
    "subcategorias": ["drama", "clásico"],
    "fecha_inicio": "2024-02-10T20:00:00",
    "fecha_fin": "2024-02-10T22:30:00",
    "venue": {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "nombre": "Teatro San Martín",
      "barrio": "Centro",
      "direccion": "Av. Corrientes 1530"
    },
    "precio_min": 2500.0,
    "precio_max": 4500.0,
    "es_gratuito": false,
    "imagen_url": "https://ejemplo.com/imagen.jpg",
    "url_fuente": "https://alternativateatral.com/obra/1234",
    "tags": ["teatro", "drama", "presencial"]
  }
]
```

---

### `GET /api/events/{event_id}`

Detalle de un evento por UUID.

**Path params**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `event_id` | UUID | ID del evento |

**Request**
```
GET /api/events/550e8400-e29b-41d4-a716-446655440000
```

**Response 200** — Mismo objeto que el ítem del listado.

**Response 404**
```json
{ "detail": "Evento no encontrado" }
```

---

## Búsqueda y Sugerencias

### `GET /api/search/suggestions`

Autocompletado: retorna sugerencias de eventos, venues y categorías que coincidan con el texto ingresado.

**Query params**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `query` | string (min 2 chars) | Texto parcial para buscar |

**Request**
```
GET /api/search/suggestions?query=teat
```

**Response 200**
```json
{
  "sugerencias": [
    {
      "tipo": "evento",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "texto": "Teatro de la Memoria",
      "extra": "15/02/2024"
    },
    {
      "tipo": "venue",
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "texto": "Teatro San Martín",
      "extra": "Centro"
    },
    {
      "tipo": "categoria",
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "texto": "Teatro",
      "extra": null
    }
  ]
}
```

Tipos de sugerencia:
- `evento`: título del evento + fecha (extra)
- `venue`: nombre del venue + barrio (extra)
- `categoria`: nombre de la categoría

---

## Usuarios

Base path: `/api/users`

### `POST /api/users/register`

Registro de nuevo usuario. El email debe ser único.

**Request body**
```json
{
  "email": "usuario@ejemplo.com",
  "nombre": "Juan Pérez",
  "preferencias": {
    "categorias_favoritas": ["teatro", "música"],
    "barrios_preferidos": ["Palermo", "San Telmo"]
  }
}
```

**Response 201**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@ejemplo.com",
  "nombre": "Juan Pérez",
  "preferencias": {
    "categorias_favoritas": ["teatro", "música"],
    "barrios_preferidos": ["Palermo", "San Telmo"]
  },
  "ubicacion_habitual": null
}
```

**Response 409**
```json
{ "detail": "El email ya esta registrado" }
```

---

### `POST /api/users/preferences`

Guarda o actualiza preferencias del usuario. Hace merge con las preferencias existentes.

**Request body**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "categorias_favoritas": ["teatro", "danza"],
  "barrios_preferidos": ["Palermo"],
  "rango_precio": { "min": 0, "max": 3000 },
  "horarios_preferidos": ["noche"],
  "tags_interes": ["al aire libre", "familiar"]
}
```

**Response 200**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "preferencias": {
    "categorias_favoritas": ["teatro", "danza"],
    "barrios_preferidos": ["Palermo"],
    "rango_precio": { "min": 0, "max": 3000 },
    "horarios_preferidos": ["noche"],
    "tags_interes": ["al aire libre", "familiar"]
  }
}
```

---

### `GET /api/users/{user_id}/preferences`

Obtiene las preferencias actuales del usuario.

**Response 200**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "preferencias": { "categorias_favoritas": ["teatro"] }
}
```

---

### `POST /api/users/{user_id}/interactions`

Registra una interacción del usuario con un evento.

**Tipos válidos:** `vista` | `clic` | `guardado` | `compartido`

**Request body**
```json
{
  "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "tipo": "guardado"
}
```

**Response 201**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "tipo": "guardado",
  "timestamp": "2024-01-15T20:00:00"
}
```

**Response 400**
```json
{ "detail": "Tipo de interaccion invalido. Validos: ['clic', 'compartido', 'guardado', 'vista']" }
```

---

### `GET /api/users/{user_id}/historial`

Historial de eventos vistos y guardados. Orden: más reciente primero.

**Response 200**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "tipo": "guardado",
    "timestamp": "2024-01-15T20:00:00"
  }
]
```

---

### `GET /api/users/{user_id}/guardados`

Lista de eventos guardados como favoritos.

**Response 200** — Mismo formato que `/historial`, solo tipo `guardado`.

---

## Recomendaciones

Base path: `/api/recommendations`

### `GET /api/recommendations/{user_id}`

Recomendaciones personalizadas para el usuario.

**Query params**

| Parámetro | Tipo | Valores | Descripción |
|-----------|------|---------|-------------|
| `tipo` | string | `personalizadas` \| `populares` \| `similares` \| `contenido` \| `hibrido` | Tipo de recomendación (default: `personalizadas`) |
| `event_id` | UUID | — | Requerido si `tipo=similares` |
| `limite` | int 1–50 | — | Número de resultados (default: 10) |

**Tipos de recomendación:**

| Tipo | Descripción |
|------|-------------|
| `personalizadas` | Basadas en preferencias declaradas (categorías, barrios, precio) |
| `populares` | Eventos más interactuados (fallback para usuarios nuevos) |
| `similares` | Similares a un evento dado (requiere `event_id`) |
| `contenido` | Basadas en comportamiento implícito (embeddings de eventos vistos/guardados) |
| `hibrido` | 50% preferencias + 50% comportamiento con diversificación |

**Request**
```
GET /api/recommendations/550e8400-e29b-41d4-a716-446655440000?tipo=hibrido&limite=5
```

**Response 200**
```json
[
  {
    "event": {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "titulo": "La Gaviota",
      "categoria": "Teatro",
      "fecha_inicio": "2024-02-10T20:00:00",
      "venue": { "nombre": "Teatro San Martín", "barrio": "Centro" },
      "es_gratuito": false,
      "precio_min": 2500.0
    },
    "razon": "Porque te gustan: eventos de Teatro · en Palermo"
  }
]
```

**Response 422** (cuando `tipo=similares` pero no se provee `event_id`)
```json
{ "detail": "Se requiere 'event_id' cuando tipo=similares" }
```

---

### `GET /api/recommendations/contexto/buscar`

Recomendaciones contextuales sin autenticación. Acepta lenguaje natural.

**Query params**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `query` | string | Texto libre: `"esta noche"`, `"gratis"`, `"con niños"`, `"fin de semana"` |
| `barrio` | string | Filtrar por barrio |
| `gratis` | boolean | Solo eventos gratuitos |
| `limite` | int 1–50 | Número de resultados (default: 10) |

**Request**
```
GET /api/recommendations/contexto/buscar?query=gratis esta noche&barrio=Palermo&limite=5
```

**Response 200** — Lista de eventos con razón de recomendación.

---

## Venues

### `GET /api/venues`

Lista todos los venues.

**Response 200**
```json
[
  {
    "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "nombre": "Teatro San Martín",
    "barrio": "Centro",
    "direccion": "Av. Corrientes 1530",
    "ciudad": "Buenos Aires",
    "pais": "Argentina"
  }
]
```

### `GET /api/venues/{venue_id}`

Detalle de un venue por UUID. Retorna 404 si no existe.

---

## Categorías

### `GET /api/categories`

Lista todas las categorías de eventos.

**Response 200**
```json
[
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "nombre": "Teatro",
    "descripcion": "Eventos teatrales y espectáculos en vivo"
  }
]
```

### `GET /api/categories/{category_id}`

Detalle de una categoría por UUID. Retorna 404 si no existe.

---

## Barrios

### `GET /api/barrios`

Lista los barrios de Buenos Aires con eventos disponibles.

**Response 200**
```json
[
  "Palermo",
  "San Telmo",
  "La Boca",
  "Belgrano",
  "Recoleta"
]
```

---

## Estadísticas

### `GET /api/stats`

Estadísticas generales del sistema.

**Response 200**
```json
{
  "total_events": 1250,
  "total_users": 340,
  "total_venues": 85,
  "total_categories": 10,
  "events_by_category": {
    "Teatro": 320,
    "Música": 280,
    "Arte": 190
  },
  "events_by_barrio": {
    "Palermo": 210,
    "San Telmo": 180
  }
}
```

---

## Admin

Base path: `/api/v1/admin`

Estos endpoints son para administración interna del sistema.

### `POST /api/v1/admin/scrape/{source_name}`

Dispara un scraper de forma manual.

**Path params**

| Valor | Descripción |
|-------|-------------|
| `agenda_ba` | Agenda Buenos Aires |
| `alternativa_teatral` | Alternativa Teatral |
| `all` | Todos los scrapers en secuencia |

**Request**
```
POST /api/v1/admin/scrape/agenda_ba
```

**Response 200**
```json
{
  "message": "Scraper 'agenda_ba' iniciado exitosamente",
  "task_id": "c6a50d2a-5a9c-4b6a-8e5f-1a2b3c4d5e6f",
  "source": "agenda_ba",
  "status": "pending"
}
```

**Response 400** (scraper no válido)
```json
{
  "detail": {
    "error": "Scraper 'foo' no encontrado",
    "available_scrapers": ["agenda_ba", "alternativa_teatral", "all"]
  }
}
```

---

### `GET /api/v1/admin/scrape/status/{task_id}`

Estado de una tarea de scraping Celery.

**Response 200 — En progreso**
```json
{
  "task_id": "c6a50d2a-5a9c-4b6a-8e5f-1a2b3c4d5e6f",
  "state": "PENDING",
  "result": null,
  "error": null
}
```

**Response 200 — Completado**
```json
{
  "task_id": "c6a50d2a-5a9c-4b6a-8e5f-1a2b3c4d5e6f",
  "state": "SUCCESS",
  "result": { "events_scraped": 42, "events_saved": 38 },
  "error": null
}
```

**Response 200 — Fallido**
```json
{
  "task_id": "c6a50d2a-5a9c-4b6a-8e5f-1a2b3c4d5e6f",
  "state": "FAILURE",
  "result": null,
  "error": "Connection timeout to source"
}
```

Estados posibles: `PENDING` | `STARTED` | `SUCCESS` | `FAILURE` | `RETRY` | `REVOKED`

---

### `GET /api/v1/admin/scrape/list`

Lista todos los scrapers disponibles.

**Response 200**
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

---

### `GET /api/v1/admin/metrics`

Reporte de métricas del sistema de recomendaciones.

**Query params**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `periodo` | int 1–365 | Días a analizar (default: 30) |

**Response 200**
```json
{
  "periodo_dias": 30,
  "ctr": 0.12,
  "tasa_guardado": 0.08,
  "diversidad": 0.75,
  "cobertura": 0.42,
  "precision_at_10": 0.65,
  "total_impresiones": 4200,
  "total_interacciones": 504
}
```

---

### `GET /api/v1/admin/bias-report`

Reporte de sesgos del sistema de recomendaciones.

**Query params**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `periodo` | int 1–365 | Días a analizar (default: 30) |

**Response 200**
```json
{
  "periodo_dias": 30,
  "sesgos": {
    "popularidad": {
      "score": 0.3,
      "alerta": false,
      "descripcion": "El sistema recomienda eventos con popularidad variada"
    },
    "geografico": {
      "score": 0.7,
      "alerta": true,
      "barrios_sobrerepresentados": ["Palermo", "Recoleta"],
      "sugerencia": "Considerar boosting de eventos en barrios periféricos"
    },
    "precio": { "score": 0.2, "alerta": false },
    "burbuja_de_filtro": { "score": 0.4, "alerta": false },
    "fuente": { "score": 0.15, "alerta": false }
  }
}
```

---

### `POST /api/v1/admin/test/celery`

Envía una tarea de prueba a Celery para verificar que el worker está funcionando.

**Query params**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `message` | string | Mensaje de prueba (default: `"Hola desde la API!"`) |

**Response 200**
```json
{
  "message": "Tarea de prueba enviada a Celery",
  "task_id": "a1b2c3d4-...",
  "input_message": "test",
  "status": "pending"
}
```

---

## Códigos de error

| Código | Significado |
|--------|-------------|
| 200 | OK — Petición exitosa |
| 201 | Created — Recurso creado exitosamente |
| 400 | Bad Request — Parámetros inválidos |
| 404 | Not Found — Recurso no encontrado |
| 409 | Conflict — El recurso ya existe (ej: email duplicado) |
| 422 | Unprocessable Entity — Fallo de validación de datos |
| 500 | Internal Server Error — Error inesperado del servidor |

Todos los errores retornan:
```json
{ "detail": "Descripción del error" }
```
