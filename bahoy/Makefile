# ========================================
# Makefile - Bahoy
# ========================================
# Comandos de conveniencia para gestionar el entorno Docker.
#
# Uso: make <comando>
# Ver todos los comandos: make help

# Variables
COMPOSE        = docker compose
COMPOSE_TOOLS  = docker compose --profile tools
BACKEND_URL    = http://localhost:8000
FRONTEND_URL   = http://localhost:3000

.PHONY: help setup up up-tools down build rebuild logs logs-backend \
        logs-frontend logs-worker logs-db ps restart restart-backend \
        clean shell-backend shell-db migrate test scrape-all

# ========== Ayuda ==========

help: ## Muestra este mensaje de ayuda
	@echo ""
	@echo "  Bahoy - Comandos disponibles"
	@echo "  ============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ========== Setup inicial ==========

setup: ## Primera vez: copia .env.example a .env y levanta los servicios
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "  .env creado desde .env.example (edítalo antes de continuar)"; \
	else \
		echo "  .env ya existe, no se sobreescribe"; \
	fi
	$(COMPOSE) up -d

# ========== Ciclo de vida de servicios ==========

up: ## Inicia todos los servicios en segundo plano
	$(COMPOSE) up -d

up-tools: ## Inicia servicios + herramientas de monitoreo (Flower, pgAdmin)
	$(COMPOSE_TOOLS) up -d

down: ## Detiene y elimina los contenedores (los datos persisten en volúmenes)
	$(COMPOSE) down

restart: ## Reinicia todos los servicios
	$(COMPOSE) restart

restart-backend: ## Reinicia solo el servicio backend
	$(COMPOSE) restart backend

clean: ## Elimina contenedores, redes y volúmenes (¡CUIDADO: borra datos!)
	@echo "  ADVERTENCIA: Esto eliminará todos los datos de la base de datos."
	@read -p "  ¿Estás seguro? (s/N): " confirm && [ "$$confirm" = "s" ]
	$(COMPOSE) down -v --remove-orphans

# ========== Build de imágenes ==========

build: ## Construye las imágenes Docker
	$(COMPOSE) build

rebuild: ## Reconstruye todas las imágenes desde cero (sin cache)
	$(COMPOSE) build --no-cache

# ========== Logs ==========

logs: ## Muestra logs en tiempo real de todos los servicios
	$(COMPOSE) logs -f

logs-backend: ## Muestra logs del backend (FastAPI)
	$(COMPOSE) logs -f backend

logs-frontend: ## Muestra logs del frontend (Next.js)
	$(COMPOSE) logs -f frontend

logs-worker: ## Muestra logs del worker de Celery
	$(COMPOSE) logs -f celery-worker

logs-db: ## Muestra logs de PostgreSQL
	$(COMPOSE) logs -f postgres

# ========== Estado de servicios ==========

ps: ## Muestra el estado de todos los contenedores
	$(COMPOSE) ps

# ========== Shells interactivos ==========

shell-backend: ## Abre una shell bash en el contenedor del backend
	$(COMPOSE) exec backend bash

shell-db: ## Abre psql en el contenedor de PostgreSQL
	$(COMPOSE) exec postgres psql -U bahoy_user -d bahoy_db

shell-redis: ## Abre la CLI de Redis
	$(COMPOSE) exec redis redis-cli

# ========== Base de datos ==========

migrate: ## Aplica las migraciones de Alembic (alembic upgrade head)
	$(COMPOSE) exec backend alembic upgrade head

migrate-new: ## Crea una nueva migración (uso: make migrate-new MSG="descripcion")
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Revierte la última migración
	$(COMPOSE) exec backend alembic downgrade -1

# ========== Tests ==========

test: ## Ejecuta los tests del backend con pytest
	$(COMPOSE) exec backend pytest tests/ -v

test-coverage: ## Ejecuta tests con reporte de cobertura
	$(COMPOSE) exec backend pytest tests/ --cov=app --cov-report=term-missing

# ========== Scrapers ==========

scrape-all: ## Dispara todos los scrapers manualmente vía API
	curl -s -X POST $(BACKEND_URL)/api/v1/admin/scrape/all | python3 -m json.tool

scrape-agenda: ## Dispara el scraper de Agenda BA
	curl -s -X POST $(BACKEND_URL)/api/v1/admin/scrape/agenda_ba | python3 -m json.tool

scrape-teatro: ## Dispara el scraper de Alternativa Teatral
	curl -s -X POST $(BACKEND_URL)/api/v1/admin/scrape/alternativa_teatral | python3 -m json.tool

# ========== URLs útiles ==========

open: ## Muestra las URLs de todos los servicios
	@echo ""
	@echo "  Servicios disponibles:"
	@echo "  ----------------------"
	@echo "  API:          $(BACKEND_URL)"
	@echo "  API Docs:     $(BACKEND_URL)/docs"
	@echo "  Frontend:     $(FRONTEND_URL)"
	@echo "  Flower:       http://localhost:5555  (requiere: make up-tools)"
	@echo "  pgAdmin:      http://localhost:5050  (requiere: make up-tools)"
	@echo ""
