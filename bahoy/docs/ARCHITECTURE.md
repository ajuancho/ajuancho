# Bahoy — Arquitectura

## Diagrama de componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTE                                        │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    Next.js 14 (puerto 3000)                         │  │
│   │                                                                     │  │
│   │  App Router       Components          Lib                           │  │
│   │  ├── page.tsx     ├── EventCard       ├── api.ts (axios client)     │  │
│   │  ├── buscar/      ├── EventList       └── utils.ts                  │  │
│   │  ├── explorar/    ├── SearchBar                                     │  │
│   │  ├── evento/[id]/ ├── FilterSidebar   State Management              │  │
│   │  ├── perfil/      └── ...             ├── React Query (server)      │  │
│   │  └── admin/                           └── Zustand (client)          │  │
│   └──────────────────────────┬──────────────────────────────────────────┘  │
└──────────────────────────────│──────────────────────────────────────────────┘
                               │ HTTP/REST (JSON)
                               │ CORS: allowedOrigins configurados
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                        FASTAPI BACKEND (puerto 8000)                        │
│                                                                             │
│  Middleware                                                                 │
│  ├── CORSMiddleware                                                         │
│  └── HTTP logging middleware (loguru → JSON)                                │
│                                                                             │
│  Routers (REST API)          Services               NLP                    │
│  ├── /api/events             ├── RecommenderService ├── SentenceTransformer │
│  ├── /api/search             ├── BiasAnalyzer       │   (dim=768, multilin) │
│  ├── /api/users              └── MetricsService     └── spaCy / langdetect  │
│  ├── /api/recommendations                                                   │
│  ├── /api/venues             Scrapers                                       │
│  ├── /api/categories         ├── AgendaBASpider (Scrapy + BS4)             │
│  ├── /api/barrios            └── AlternativaTeatralSpider (Scrapy+Playwright)│
│  ├── /api/stats                                                             │
│  ├── /api/v1/admin           ORM (SQLAlchemy 2.0 async)                    │
│  ├── /health                 └── Models: Event, User, Venue, Category,     │
│  └── /metrics (Prometheus)         Interaction, Impression, Source         │
└────────────┬─────────────────────────────────────────┬───────────────────────┘
             │ asyncpg (async)                         │ redis.asyncio
┌────────────▼──────────────┐            ┌─────────────▼──────────────────────┐
│    PostgreSQL 16           │            │           Redis 7                  │
│    + pgvector             │            │                                    │
│                           │            │  DB 0: Cache de API               │
│  Tablas:                  │            │  DB 0: Broker Celery              │
│  ├── events (+ embedding) │            │  DB 0: Backend resultados         │
│  ├── users                │            │                                    │
│  ├── venues               │            └────────────────────────────────────┘
│  ├── categories           │
│  ├── sources              │
│  ├── interactions         │
│  └── impressions          │
│                           │
│  Extensiones:             │
│  ├── vector (pgvector)    │
│  ├── uuid-ossp            │
│  ├── unaccent             │
│  └── pg_trgm              │
└───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         CELERY (tareas asíncronas)                          │
│                                                                             │
│  celery-worker                    celery-beat                               │
│  ├── task_scrape_agenda_ba        ├── agenda_ba: diario 06:00 AM           │
│  ├── task_scrape_alternativa      ├── alternativa_teatral: diario 07:00 AM │
│  ├── task_full_scrape             └── TZ: America/Argentina/Buenos_Aires   │
│  └── test_task                                                              │
│                                                                             │
│  Broker/Backend: Redis (redis://redis:6379/0)                               │
│  Monitoreo: Flower (puerto 5555)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Flujo de datos

### 1. Scraping y enriquecimiento de eventos

```
Fuente externa (HTTP)
       │
       ▼
  Scrapy Spider
  (descarga, parsea HTML)
       │
       ▼
  Scrapy Pipeline
  ├── Limpieza y normalización de texto
  ├── Deduplicación (URL fuente como clave)
  ├── Clasificación NLP (categoría, subcategorías, tags)
  ├── Generación de embedding (sentence-transformers, 768d)
  └── Persistencia en PostgreSQL (Event.embedding = vector)
       │
       ▼
  PostgreSQL
  (eventos indexados con pgvector)
```

### 2. Búsqueda semántica

```
Usuario: "obra de teatro clásica gratuita en Palermo"
       │
       ▼
  GET /api/search/suggestions?query=...
  (búsqueda textual ILIKE en titles, venues, categories)
       │
  (futuro: embedding de query → cosine similarity con pgvector)
       │
       ▼
  Resultados ordenados por relevancia
```

### 3. Recomendaciones

```
Usuario autenticado
       │
       ├─── tipo=personalizadas
       │    └── filtros por preferencias declaradas (categorías, barrios, precio)
       │
       ├─── tipo=contenido
       │    └── embeddings de eventos vistos/guardados → similitud coseno
       │
       ├─── tipo=hibrido
       │    └── merge 50/50 con diversificación por categoría
       │
       ├─── tipo=similares + event_id
       │    └── vecinos más cercanos del embedding del evento base
       │
       └─── tipo=populares (fallback sin historial)
            └── ranking por suma de interacciones ponderadas
```

### 4. Request HTTP típico

```
Browser
  │  GET /api/events?categoria=teatro
  ▼
Next.js (getServerSideProps o fetch en RSC)
  │  GET http://backend:8000/api/events?categoria=teatro
  ▼
FastAPI route handler
  │  AsyncSession → SQLAlchemy SELECT con filtros
  ▼
PostgreSQL
  │  Result set
  ▼
FastAPI serializa a JSON
  │  Redis: cache miss → cachear respuesta (TTL 3600s)
  ▼
Response al browser
```

---

## Modelos de datos

### Event

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID PK | Identificador único |
| `titulo` | TEXT | Nombre del evento |
| `descripcion` | TEXT | Descripción larga |
| `categoria_id` | UUID FK | Categoría principal |
| `subcategorias` | JSONB | Lista de subcategorías |
| `venue_id` | UUID FK | Venue donde ocurre |
| `fecha_inicio` | TIMESTAMPTZ | Inicio del evento |
| `fecha_fin` | TIMESTAMPTZ | Fin del evento |
| `precio_min` | NUMERIC | Precio mínimo de entrada |
| `precio_max` | NUMERIC | Precio máximo de entrada |
| `es_gratuito` | BOOLEAN | Si es gratis |
| `embedding` | VECTOR(768) | Embedding semántico (pgvector) |
| `imagen_url` | TEXT | URL de imagen del evento |
| `url_fuente` | TEXT UNIQUE | URL original (clave dedup) |
| `tags` | JSONB | Lista de etiquetas |
| `source_id` | UUID FK | Fuente scraper |
| `created_at` | TIMESTAMPTZ | Fecha de creación |
| `updated_at` | TIMESTAMPTZ | Última actualización |

### User

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID PK | Identificador único |
| `email` | TEXT UNIQUE | Email (clave de autenticación) |
| `nombre` | TEXT | Nombre del usuario |
| `preferencias` | JSONB | Preferencias declaradas |
| `ubicacion_habitual` | TEXT | Barrio habitual del usuario |
| `created_at` | TIMESTAMPTZ | Fecha de registro |

### Interaction

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID PK | Identificador único |
| `user_id` | UUID FK | Usuario |
| `event_id` | UUID FK | Evento |
| `tipo` | ENUM | `vista` / `clic` / `guardado` / `compartido` |
| `timestamp` | TIMESTAMPTZ | Momento de la interacción |

---

## Decisiones técnicas

### Por qué FastAPI

- Soporte nativo async/await → fundamental para I/O bound (DB + Redis + scrapers)
- Validación automática con Pydantic: menos bugs, documentación OpenAPI gratuita
- Performance comparable a Node.js/Go para servicios API
- Ecosistema Python rico para NLP/ML (no hay alternativa con mejor integración)

### Por qué pgvector en vez de una DB vectorial dedicada (Pinecone, Weaviate)

- Reducción de infraestructura: un solo servicio de DB para datos relacionales y vectoriales
- Transaccionalidad: el embedding se persiste en la misma transacción que el evento
- Suficiente para el volumen actual (< 100k eventos): índice HNSW de pgvector tiene latencia < 10ms en ese rango
- Migrar a Pinecone requeriría menos de una semana si se superan los 1M de vectores

### Por qué Celery + Redis en vez de un cron simple

- Los scrapers pueden tardar 5-15 minutos: necesitamos ejecución en background
- Retries automáticos ante fallos de red
- Monitoreo con Flower (visibilidad de tareas activas, fallidas, historial)
- El mismo Redis que usamos para cache actúa como broker → sin infraestructura extra

### Por qué Next.js 14 App Router

- Server Components: menor JavaScript al cliente, mejor performance inicial
- Streaming con Suspense: UX mejorada para listados grandes
- TypeScript first: menos bugs en tiempo de ejecución
- React Query para cache de server state: evita refetch innecesarios

### Logging con loguru en vez del módulo `logging` estándar

- JSON serializable directamente (`serialize=True`): parseable por Datadog, CloudWatch, Loki
- Rotación y compresión automáticas del archivo de log
- API más simple: `logger.info("msg", key=value)` en vez de `logger.info(f"...")`

### Autenticación simplificada (sin OAuth por ahora)

MVP usa registro simple por email sin contraseña. El `SECRET_KEY` protege los JWT.
Para producción real se planea agregar OAuth2 con Google/GitHub via FastAPI-Users.

---

## Índices de base de datos

Para optimizar las queries más frecuentes:

```sql
-- Búsqueda por categoría
CREATE INDEX idx_events_categoria ON events(categoria_id);

-- Búsqueda por fecha (filtros de agenda)
CREATE INDEX idx_events_fecha ON events(fecha_inicio);

-- Deduplicación de scrapers
CREATE UNIQUE INDEX idx_events_url_fuente ON events(url_fuente);

-- Búsqueda vectorial (HNSW: mejor para búsqueda aproximada)
CREATE INDEX idx_events_embedding ON events
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Búsqueda textual fuzzy
CREATE INDEX idx_events_titulo_trgm ON events
  USING gin (titulo gin_trgm_ops);
```

---

## Escalabilidad horizontal

El diseño soporta escalar horizontalmente:

- **Backend**: sin estado → múltiples instancias detrás de un load balancer
- **Celery workers**: agregar más workers sin cambiar código (`--concurrency=N`)
- **PostgreSQL**: réplicas de lectura para queries de búsqueda (read-heavy)
- **Redis**: Redis Cluster para alta disponibilidad del broker

Cuello de botella actual: el modelo NLP se carga en CPU por worker. Para escala grande, mover a un servicio de embeddings dedicado (FastAPI + sentence-transformers en GPU, o usar OpenAI/Cohere API).
