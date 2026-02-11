# Scraper de Agenda Buenos Aires

Scraper robusto desarrollado con Scrapy para extraer eventos de la [Agenda de Buenos Aires](https://turismo.buenosaires.gob.ar/es/agenda).

## Características

- ✅ **Navegación automática**: Recorre la página de agenda y sigue enlaces a eventos individuales
- ✅ **Extracción completa**: Título, descripción, fechas, ubicación, categorías, precios, imágenes
- ✅ **Normalización de datos**: Parseo de fechas en español, limpieza de HTML, generación de hash único
- ✅ **Detección de duplicados**: Verifica eventos existentes por hash antes de insertar
- ✅ **Almacenamiento en PostgreSQL**: Guarda eventos en la base de datos con gestión de duplicados
- ✅ **Respetuoso**: Sigue robots.txt, delays configurables, User-Agent identificable
- ✅ **Logging detallado**: Información completa del proceso de scraping
- ✅ **Manejo de errores**: Reintentos automáticos y recuperación de errores

## Estructura de Archivos

```
app/scrapers/
├── __init__.py                 # Inicialización del paquete
├── README.md                   # Esta documentación
├── items.py                    # Definición de estructura de datos (EventItem)
├── agenda_ba_spider.py         # Spider principal
├── pipelines.py                # Procesamiento y guardado en DB
├── settings.py                 # Configuración de Scrapy
└── run_scraper.py              # Script de ejecución
```

## Instalación

### 1. Instalar dependencias

```bash
cd bahoy/backend
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL

Asegúrate de que PostgreSQL esté corriendo y las credenciales en `app/config.py` sean correctas:

```python
POSTGRES_SERVER = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = "bahoy_user"
POSTGRES_PASSWORD = "bahoy_password"
POSTGRES_DB = "bahoy_db"
```

### 3. Verificar la tabla

El scraper creará automáticamente la tabla `events` si no existe. La estructura incluye:

- Información del evento (título, descripción, fechas, etc.)
- Ubicación (lugar, dirección, barrio)
- Categorización (categoría, tags)
- Precio e información adicional
- Hash único para detectar duplicados
- Timestamps de creación y actualización

## Uso

### Ejecución básica

```bash
# Desde el directorio backend
cd app/scrapers
python run_scraper.py
```

Esto scrapeará todos los eventos y los guardará en PostgreSQL.

### Opciones avanzadas

```bash
# Con salida a archivo JSON
python run_scraper.py --output events.json

# Con salida a archivo CSV
python run_scraper.py --output events.csv

# Modo debug (logs detallados)
python run_scraper.py --debug

# Combinar opciones
python run_scraper.py --output events.json --debug
```

### Uso directo con Scrapy

```bash
# Desde el directorio backend
export SCRAPY_SETTINGS_MODULE=app.scrapers.settings
scrapy crawl agenda_ba
```

## Configuración

### Delays y concurrencia

En `settings.py`:

```python
DOWNLOAD_DELAY = 2.5                    # Delay entre requests
RANDOMIZE_DOWNLOAD_DELAY = True         # Randomizar delays
CONCURRENT_REQUESTS_PER_DOMAIN = 1      # 1 request a la vez por dominio
```

### Reintentos

```python
RETRY_TIMES = 3                         # Número de reintentos
RETRY_HTTP_CODES = [500, 502, 503, ...]  # Códigos que disparan reintentos
```

### Base de datos

```python
POSTGRES_HOST = 'localhost'
POSTGRES_PORT = 5432
POSTGRES_USER = 'bahoy_user'
POSTGRES_PASSWORD = 'bahoy_password'
POSTGRES_DB = 'bahoy_db'
```

## Campos Extraídos

### Información básica
- `title`: Título del evento
- `description`: Descripción completa
- `short_description`: Descripción corta (si existe)

### Fechas
- `start_date`: Fecha y hora de inicio (datetime)
- `end_date`: Fecha y hora de fin (datetime, opcional)
- `date_text`: Texto original de la fecha

### Ubicación
- `venue_name`: Nombre del lugar
- `venue_address`: Dirección completa
- `neighborhood`: Barrio
- `latitude`, `longitude`: Coordenadas (si están disponibles)

### Categorización
- `category`: Categoría mapeada a nuestro sistema
- `tags`: Lista de etiquetas

### Multimedia
- `image_url`: URL de la imagen principal

### Precio
- `price`: Precio del evento (decimal)
- `is_free`: Boolean indicando si es gratuito

### Metadata
- `url`: URL original del evento
- `source`: Fuente (siempre "agenda_ba")
- `event_hash`: Hash MD5 único para detectar duplicados
- `scraped_at`: Timestamp del scraping

## Mapeo de Categorías

El scraper mapea categorías del sitio web a nuestro sistema:

| Categoría Original | Categoría Mapeada |
|-------------------|-------------------|
| Música / Recital / Concierto | music |
| Teatro | theater |
| Arte / Exposición | art / exhibition |
| Danza | dance |
| Cine | cinema |
| Feria | fair |
| Gastronomía | food |
| Deporte | sports |
| Infantil | kids |
| Tango | tango |
| Festival | festival |
| Curso | workshop |

## Detección de Duplicados

El scraper genera un hash único para cada evento basado en:
- Título normalizado (lowercase, sin espacios extra)
- Fecha de inicio
- Nombre del lugar

Si un evento con el mismo hash ya existe en la base de datos:
- Se verifica si necesita actualización (cada 7 días o si la descripción cambió significativamente)
- Se actualiza si es necesario, o se omite si no hay cambios

## Logging y Monitoreo

El scraper proporciona información detallada:

```
[INFO] Parseando página de agenda: https://...
[INFO] Encontrados 15 enlaces a eventos
[INFO] Parseando evento: https://...
[INFO] Evento insertado: Concierto de Jazz en...
[INFO] Evento actualizado: Festival de...
[INFO] Spider cerrado
[INFO] Total eventos scrapeados: 15
[INFO] Estadísticas de guardado:
[INFO]   - Eventos insertados: 12
[INFO]   - Eventos actualizados: 2
[INFO]   - Eventos omitidos: 1
```

## Solución de Problemas

### Error de conexión a PostgreSQL

```
Error conectando a PostgreSQL: could not connect to server
```

**Solución**: Verifica que PostgreSQL esté corriendo y las credenciales sean correctas en `app/config.py`.

### No se encuentran eventos

```
No se encontraron eventos en https://...
```

**Solución**: El sitio web puede haber cambiado su estructura HTML. Revisa los selectores CSS en `agenda_ba_spider.py` y ajústalos según sea necesario.

### Fechas no se parsean correctamente

**Solución**: Revisa el método `parse_date()` en el spider y ajusta los patrones de regex según el formato de fechas del sitio.

## Mantenimiento

### Actualizar selectores CSS

Si el sitio web cambia su estructura, actualiza los selectores en `agenda_ba_spider.py`:

```python
def extract_title(self, response: Response) -> Optional[str]:
    # Actualizar estos selectores según la nueva estructura
    title = response.css('h1.event-title::text').get()
    if not title:
        title = response.css('h1::text').get()
    return title
```

### Añadir nuevos campos

1. Añadir el campo en `items.py`:
```python
class EventItem(scrapy.Item):
    new_field = Field()
```

2. Extraer el campo en el spider:
```python
item['new_field'] = self.extract_new_field(response)
```

3. Añadir la columna en la tabla de PostgreSQL (en `pipelines.py`):
```python
new_field VARCHAR(100),
```

## Programación Automática

Para ejecutar el scraper periódicamente, usa cron (Linux) o Task Scheduler (Windows):

### Cron (Linux/Mac)

```bash
# Editar crontab
crontab -e

# Ejecutar diariamente a las 3 AM
0 3 * * * cd /path/to/bahoy/backend && python app/scrapers/run_scraper.py >> /var/log/bahoy_scraper.log 2>&1
```

### Systemd Timer (Linux)

Ver documentación de systemd para crear un servicio y timer.

## Licencia

Parte del proyecto Bahoy.

## Contacto

Para preguntas o problemas, contactar al equipo de desarrollo de Bahoy.
