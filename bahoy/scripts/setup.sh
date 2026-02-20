#!/usr/bin/env bash
# =============================================================================
# Bahoy - Script de Setup Inicial
# =============================================================================
# Uso: ./scripts/setup.sh [--no-docker] [--no-seed] [--help]
#
# Este script prepara el entorno de desarrollo completo:
#   1. Verifica dependencias del sistema
#   2. Configura variables de entorno
#   3. Levanta Docker (PostgreSQL, Redis)
#   4. Instala dependencias de Python y Node
#   5. Corre migraciones de base de datos
#   6. Carga datos de prueba
# =============================================================================

set -euo pipefail

# ── Colores para output ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'
BOLD='\033[1m'

# ── Flags ──────────────────────────────────────────────────────────────────────
NO_DOCKER=false
NO_SEED=false
SKIP_BACKEND_DEPS=false
SKIP_FRONTEND_DEPS=false

for arg in "$@"; do
  case $arg in
    --no-docker) NO_DOCKER=true ;;
    --no-seed) NO_SEED=true ;;
    --skip-backend) SKIP_BACKEND_DEPS=true ;;
    --skip-frontend) SKIP_FRONTEND_DEPS=true ;;
    --help|-h)
      echo ""
      echo "${BOLD}Bahoy Setup Script${RESET}"
      echo ""
      echo "Uso: ./scripts/setup.sh [opciones]"
      echo ""
      echo "Opciones:"
      echo "  --no-docker       No levantar Docker (asume servicios ya corriendo)"
      echo "  --no-seed         No cargar datos de prueba"
      echo "  --skip-backend    No instalar dependencias de Python"
      echo "  --skip-frontend   No instalar dependencias de Node"
      echo "  --help, -h        Mostrar esta ayuda"
      echo ""
      exit 0
      ;;
    *)
      echo -e "${RED}Opción desconocida: $arg${RESET}" >&2
      exit 1
      ;;
  esac
done

# ── Helpers ────────────────────────────────────────────────────────────────────
log()     { echo -e "${GREEN}[✔]${RESET} $1"; }
info()    { echo -e "${BLUE}[ℹ]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[⚠]${RESET} $1"; }
error()   { echo -e "${RED}[✘]${RESET} $1" >&2; }
section() { echo -e "\n${CYAN}${BOLD}══ $1 ══${RESET}\n"; }

require_cmd() {
  if ! command -v "$1" &> /dev/null; then
    error "Comando requerido no encontrado: '$1'"
    error "Por favor instálalo antes de continuar."
    exit 1
  fi
}

wait_for_service() {
  local host=$1 port=$2 name=$3 retries=30
  info "Esperando que $name esté disponible en $host:$port..."
  for i in $(seq 1 $retries); do
    if nc -z "$host" "$port" 2>/dev/null; then
      log "$name está listo."
      return 0
    fi
    echo -n "."
    sleep 2
  done
  error "$name no respondió en $((retries * 2)) segundos."
  exit 1
}

# ── Detección del directorio raíz ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"
info "Directorio raíz: $ROOT_DIR"

# =============================================================================
# 1. VERIFICAR DEPENDENCIAS DEL SISTEMA
# =============================================================================
section "1/6  Verificando dependencias del sistema"

require_cmd git
require_cmd curl

if [ "$NO_DOCKER" = false ]; then
  require_cmd docker
  if ! docker info &>/dev/null; then
    error "Docker no está corriendo. Por favor inicia Docker Desktop o el daemon."
    exit 1
  fi
  log "Docker: $(docker --version)"

  if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif docker-compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    error "docker compose (v2) o docker-compose (v1) requerido."
    exit 1
  fi
  log "Docker Compose: $($COMPOSE_CMD version --short 2>/dev/null || echo 'v1')"
fi

if [ "$SKIP_BACKEND_DEPS" = false ]; then
  require_cmd python3
  PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
  PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
  PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
  if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    warn "Se recomienda Python 3.11+. Versión actual: $PYTHON_VERSION"
  else
    log "Python: $(python3 --version)"
  fi
fi

if [ "$SKIP_FRONTEND_DEPS" = false ]; then
  require_cmd node
  require_cmd npm
  NODE_VERSION=$(node --version | grep -oP '\d+' | head -1)
  if [ "$NODE_VERSION" -lt 18 ]; then
    error "Se requiere Node.js 18+. Versión actual: $(node --version)"
    exit 1
  fi
  log "Node.js: $(node --version)"
  log "npm: $(npm --version)"
fi

# =============================================================================
# 2. CONFIGURAR VARIABLES DE ENTORNO
# =============================================================================
section "2/6  Configurando variables de entorno"

if [ ! -f "$ROOT_DIR/.env" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  log "Archivo .env creado desde .env.example"

  # Generar SECRET_KEY aleatoria
  if command -v openssl &>/dev/null; then
    SECRET_KEY=$(openssl rand -hex 32)
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s|tu-clave-secreta-super-segura-cambiar-en-produccion|$SECRET_KEY|g" "$ROOT_DIR/.env"
    else
      sed -i "s|tu-clave-secreta-super-segura-cambiar-en-produccion|$SECRET_KEY|g" "$ROOT_DIR/.env"
    fi
    log "SECRET_KEY generada automáticamente"
  else
    warn "openssl no encontrado. Edita SECRET_KEY en .env manualmente."
  fi

  warn "Revisa y edita $ROOT_DIR/.env según tu entorno antes de continuar."
  echo ""
  read -rp "  Presiona Enter para continuar con los valores por defecto, o Ctrl+C para editar .env primero... "
else
  log "Archivo .env ya existe, usando configuración existente."
fi

# Cargar variables
set -a
# shellcheck source=/dev/null
source "$ROOT_DIR/.env"
set +a

# =============================================================================
# 3. LEVANTAR DOCKER
# =============================================================================
section "3/6  Levantando servicios Docker"

if [ "$NO_DOCKER" = true ]; then
  info "Saltando Docker (--no-docker). Asegúrate de que PostgreSQL y Redis estén corriendo."
else
  info "Levantando PostgreSQL y Redis..."
  $COMPOSE_CMD up -d postgres redis

  # Esperar a que estén listos
  POSTGRES_HOST="${POSTGRES_SERVER:-localhost}"
  POSTGRES_PORT_NUM="${POSTGRES_PORT:-5432}"
  REDIS_HOST_VAR="${REDIS_HOST:-localhost}"
  REDIS_PORT_NUM="${REDIS_PORT:-6379}"

  wait_for_service "$POSTGRES_HOST" "$POSTGRES_PORT_NUM" "PostgreSQL"
  wait_for_service "$REDIS_HOST_VAR" "$REDIS_PORT_NUM" "Redis"

  log "Servicios de infraestructura listos."
fi

# =============================================================================
# 4. INSTALAR DEPENDENCIAS
# =============================================================================
section "4/6  Instalando dependencias"

# Backend (Python)
if [ "$SKIP_BACKEND_DEPS" = false ]; then
  info "Instalando dependencias de Python..."

  VENV_DIR="$ROOT_DIR/backend/venv"
  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    log "Entorno virtual Python creado en backend/venv"
  else
    log "Entorno virtual Python ya existe."
  fi

  # Activar venv e instalar
  # shellcheck source=/dev/null
  source "$VENV_DIR/bin/activate"
  pip install --quiet --upgrade pip
  pip install --quiet -r "$ROOT_DIR/backend/requirements.txt"
  log "Dependencias de Python instaladas."
else
  info "Saltando dependencias de Python (--skip-backend)."
fi

# Frontend (Node)
if [ "$SKIP_FRONTEND_DEPS" = false ]; then
  info "Instalando dependencias de Node.js..."
  cd "$ROOT_DIR/frontend"
  npm install --silent
  cd "$ROOT_DIR"
  log "Dependencias de Node.js instaladas."
else
  info "Saltando dependencias de Node.js (--skip-frontend)."
fi

# =============================================================================
# 5. CORRER MIGRACIONES
# =============================================================================
section "5/6  Ejecutando migraciones de base de datos"

# Activar venv si existe
VENV_DIR="$ROOT_DIR/backend/venv"
if [ -d "$VENV_DIR" ]; then
  # shellcheck source=/dev/null
  source "$VENV_DIR/bin/activate"
fi

cd "$ROOT_DIR/backend"

# Verificar si Alembic está configurado
if [ -f "alembic.ini" ]; then
  info "Aplicando migraciones con Alembic..."
  python -m alembic upgrade head
  log "Migraciones aplicadas correctamente."
else
  warn "alembic.ini no encontrado. Creando tablas directamente con SQLAlchemy..."
  python -c "
import asyncio
from app.database import engine
from app.models.base import Base
# Importar todos los modelos para que SQLAlchemy los registre
from app.models import event, user, venue, category, source, interaction, impression

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Tablas creadas correctamente.')

asyncio.run(create_tables())
" 2>/dev/null || warn "No se pudieron crear las tablas. Verifica la conexión a PostgreSQL."
fi

cd "$ROOT_DIR"

# =============================================================================
# 6. CARGAR DATOS DE PRUEBA
# =============================================================================
section "6/6  Cargando datos de prueba"

if [ "$NO_SEED" = true ]; then
  info "Saltando datos de prueba (--no-seed)."
else
  VENV_DIR="$ROOT_DIR/backend/venv"
  if [ -d "$VENV_DIR" ]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
  fi

  cd "$ROOT_DIR/backend"

  info "Cargando datos de prueba en la base de datos..."
  python -c "
import asyncio
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os, sys

# Leer configuración
sys.path.insert(0, '.')
from app.config import settings
from app.models.category import Category
from app.models.venue import Venue
from app.models.event import Event

fake = Faker('es_AR')

CATEGORIAS = [
    'Teatro', 'Música', 'Danza', 'Arte', 'Cine',
    'Literatura', 'Gastronomía', 'Deporte', 'Infantil', 'Taller'
]
BARRIOS = [
    'Palermo', 'San Telmo', 'La Boca', 'Belgrano', 'Recoleta',
    'Almagro', 'Boedo', 'Caballito', 'Villa Crespo', 'Colegiales'
]

async def seed():
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Categorías
        cats = []
        for nombre in CATEGORIAS:
            cat = Category(nombre=nombre, descripcion=f'Eventos de {nombre.lower()}')
            session.add(cat)
            cats.append(cat)
        await session.flush()

        # Venues
        venues = []
        for barrio in BARRIOS:
            venue = Venue(
                nombre=f'{fake.company()} - {barrio}',
                barrio=barrio,
                direccion=fake.address(),
                ciudad='Buenos Aires',
                pais='Argentina',
            )
            session.add(venue)
            venues.append(venue)
        await session.flush()

        # Eventos
        import random
        from datetime import datetime, timedelta
        for i in range(50):
            start = datetime.now() + timedelta(days=random.randint(0, 30))
            event = Event(
                titulo=f'{fake.catch_phrase()} - Evento {i+1}',
                descripcion=fake.text(max_nb_chars=300),
                categoria_id=random.choice(cats).id,
                venue_id=random.choice(venues).id,
                fecha_inicio=start,
                fecha_fin=start + timedelta(hours=random.choice([1, 2, 3])),
                es_gratuito=random.choice([True, False]),
                precio_min=0 if random.random() < 0.3 else random.randint(500, 3000),
                precio_max=None,
                tags=random.sample(['arte', 'cultura', 'familia', 'nocturno', 'al aire libre'], k=2),
                url_fuente='https://ejemplo.com/evento',
            )
            session.add(event)

        await session.commit()
        print('Datos de prueba cargados: 10 categorías, 10 venues, 50 eventos.')
    await engine.dispose()

asyncio.run(seed())
" 2>/dev/null && log "Datos de prueba cargados." || warn "No se pudieron cargar datos de prueba. Verifica la conexión a PostgreSQL y los modelos."

  cd "$ROOT_DIR"
fi

# =============================================================================
# RESUMEN FINAL
# =============================================================================
echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN}   Setup completado exitosamente        ${RESET}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════${RESET}"
echo ""
echo -e "  ${BOLD}Servicios disponibles:${RESET}"
echo -e "  ${CYAN}Backend API:${RESET}     http://localhost:8000"
echo -e "  ${CYAN}API Docs:${RESET}        http://localhost:8000/docs"
echo -e "  ${CYAN}Health Check:${RESET}    http://localhost:8000/health"
echo -e "  ${CYAN}Frontend:${RESET}        http://localhost:3000"
echo ""
echo -e "  ${BOLD}Próximos pasos:${RESET}"
echo ""
if [ "$NO_DOCKER" = false ]; then
  echo -e "  Para levantar todos los servicios:"
  echo -e "  ${YELLOW}  make up${RESET}  (o: $COMPOSE_CMD up -d)"
  echo ""
fi
echo -e "  Para desarrollo local del backend:"
echo -e "  ${YELLOW}  source backend/venv/bin/activate${RESET}"
echo -e "  ${YELLOW}  cd backend && uvicorn app.main:app --reload${RESET}"
echo ""
echo -e "  Para desarrollo local del frontend:"
echo -e "  ${YELLOW}  cd frontend && npm run dev${RESET}"
echo ""
echo -e "  Para correr los tests:"
echo -e "  ${YELLOW}  make test${RESET}  (o: cd backend && pytest)"
echo ""
