"""
Bahoy - Scrapy Settings
Configuración para el scraper de Agenda Buenos Aires.
"""

import os
import sys

# Añadir el directorio de la app al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings as app_settings


# ========== Configuración del Proyecto ==========
BOT_NAME = 'bahoy_scraper'

SPIDER_MODULES = ['app.scrapers']
NEWSPIDER_MODULE = 'app.scrapers'


# ========== Configuración del Robot ==========
# Identificación del bot
USER_AGENT = 'BahoyBot/1.0 (+https://bahoy.com.ar; info@bahoy.com.ar)'

# Respetar robots.txt
ROBOTSTXT_OBEY = True


# ========== Configuración de Delays y Concurrencia ==========
# Delay entre requests (2-3 segundos como solicitado)
DOWNLOAD_DELAY = 2.5

# Randomizar el delay para parecer más humano
RANDOMIZE_DOWNLOAD_DELAY = True

# Número de requests concurrentes
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # Solo 1 request a la vez por dominio

# Timeout para requests
DOWNLOAD_TIMEOUT = 30


# ========== Configuración de Reintentos ==========
# Número máximo de reintentos
RETRY_ENABLED = True
RETRY_TIMES = 3

# Códigos HTTP que disparan reintentos
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]


# ========== Configuración de Middlewares ==========
DOWNLOADER_MIDDLEWARES = {
    # Middleware de cookies
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    # Middleware de user agent
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    # Middleware de reintentos
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    # Middleware de redirecciones
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
}

SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 500,
    'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
}


# ========== Configuración de Pipelines ==========
ITEM_PIPELINES = {
    # Pipeline de procesamiento de datos
    'app.scrapers.pipelines.EventProcessingPipeline': 100,
    # Pipeline de guardado en PostgreSQL
    'app.scrapers.pipelines.PostgreSQLPipeline': 300,
}


# ========== Configuración de PostgreSQL ==========
# Usar configuración de la aplicación
POSTGRES_HOST = app_settings.POSTGRES_SERVER
POSTGRES_PORT = app_settings.POSTGRES_PORT
POSTGRES_USER = app_settings.POSTGRES_USER
POSTGRES_PASSWORD = app_settings.POSTGRES_PASSWORD
POSTGRES_DB = app_settings.POSTGRES_DB


# ========== Configuración de Caché ==========
# Cache de DNS
DNSCACHE_ENABLED = True

# Cache HTTP (usar con cuidado en producción)
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 horas
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


# ========== Configuración de Headers ==========
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


# ========== Configuración de Cookies ==========
COOKIES_ENABLED = True
COOKIES_DEBUG = False


# ========== Configuración de Logging ==========
# Nivel de logging
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Formato de logs
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Archivo de logs
LOG_FILE = None  # None para mostrar en consola
# Para guardar en archivo, descomentar:
# LOG_FILE = 'logs/scrapy.log'

# Encoding de logs
LOG_ENCODING = 'utf-8'

# Mostrar estadísticas al final
LOG_ENABLED = True
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'


# ========== Configuración de Profundidad ==========
DEPTH_LIMIT = 3  # Máxima profundidad de crawling
DEPTH_PRIORITY = 1
DEPTH_STATS_VERBOSE = True


# ========== Configuración de AutoThrottle ==========
# AutoThrottle ajusta automáticamente el delay basado en la carga del servidor
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2  # Delay inicial
AUTOTHROTTLE_MAX_DELAY = 10  # Delay máximo
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0  # Requests concurrentes promedio
AUTOTHROTTLE_DEBUG = False


# ========== Configuración de URLs ==========
# Longitud máxima de URLs
URLLENGTH_LIMIT = 2083

# Filtrar URLs duplicadas
DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'
DUPEFILTER_DEBUG = False


# ========== Configuración de Redirecciones ==========
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5


# ========== Configuración de Compresión ==========
COMPRESSION_ENABLED = True


# ========== Configuración de Telnet Console (Debugging) ==========
# Deshabilitado por defecto por seguridad
TELNETCONSOLE_ENABLED = False
# Si se habilita:
# TELNETCONSOLE_PORT = [6023, 6073]


# ========== Configuración de Memoria ==========
# Límite de memoria (MB) antes de cerrar el spider
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 512
MEMUSAGE_WARNING_MB = 384


# ========== Configuración de Feed Exports (Opcional) ==========
# Para exportar a JSON/CSV además de PostgreSQL
FEEDS = {
    # Descomentar para habilitar exportación a archivo
    # 'data/events_%(time)s.json': {
    #     'format': 'json',
    #     'encoding': 'utf8',
    #     'store_empty': False,
    #     'indent': 2,
    # },
}


# ========== Extensiones Habilitadas ==========
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'scrapy.extensions.corestats.CoreStats': 500,
    'scrapy.extensions.memusage.MemoryUsage': 500,
}


# ========== Configuración de Jobs (Para ejecuciones pausadas/resumidas) ==========
# Directorio para guardar estado del spider
JOBDIR = None
# Para habilitar:
# JOBDIR = 'crawls/agenda_ba'


# ========== Variables de Entorno Personalizadas ==========
# Cargar variables de entorno si existen
SCRAPER_ENV = os.getenv('SCRAPER_ENV', 'development')

# Ajustar configuración según el entorno
if SCRAPER_ENV == 'production':
    # En producción, ser más conservador
    DOWNLOAD_DELAY = 3
    CONCURRENT_REQUESTS_PER_DOMAIN = 1
    LOG_LEVEL = 'WARNING'
    HTTPCACHE_ENABLED = False

elif SCRAPER_ENV == 'development':
    # En desarrollo, más verbose
    LOG_LEVEL = 'DEBUG'
    HTTPCACHE_ENABLED = True


# ========== Configuración de Señales ==========
# Para hooks personalizados
# from scrapy import signals
# Implementar en el futuro si se necesitan hooks personalizados
