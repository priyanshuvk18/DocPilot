# ==============================================================================
# DocPilot — Makefile
# ==============================================================================
# Usage: make <target>
# Requires: make, docker compose, pnpm, python 3.12, uv (or pip)
#
# Windows users: run via Git Bash, WSL2, or see README.md §Windows Setup
# for equivalent PowerShell one-liners.
# ==============================================================================

.DEFAULT_GOAL := help
.PHONY: help dev stop logs db-reset db-migrate db-shell \
        api-dev api-test api-lint api-type-check \
        web-dev web-test web-lint web-type-check web-e2e \
        test lint type-check generate-types \
        install ci-check clean

# ─── Colors ───────────────────────────────────────────────────────────────────
CYAN  := \033[0;36m
RESET := \033[0m

# ─── Help ─────────────────────────────────────────────────────────────────────
help: ## Show this help message
	@echo ""
	@echo "  DocPilot development commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ─── Infrastructure ───────────────────────────────────────────────────────────
dev: ## Start all infra services (Postgres, Redis, MinIO) + API + web
	@echo "Starting infrastructure..."
	docker compose -f infra/docker-compose.yml up -d
	@echo "Starting API (background)..."
	$(MAKE) api-dev &
	@echo "Starting web..."
	$(MAKE) web-dev

infra-up: ## Start only infra services (Postgres, Redis, MinIO)
	docker compose -f infra/docker-compose.yml up -d

infra-down: ## Stop infra services
	docker compose -f infra/docker-compose.yml down

infra-logs: ## Tail infra logs
	docker compose -f infra/docker-compose.yml logs -f

infra-reset: ## Destroy and recreate all infra volumes (WIPES DATA)
	@echo "WARNING: This will delete all local data."
	@read -p "Press ENTER to continue or Ctrl+C to cancel..."
	docker compose -f infra/docker-compose.yml down -v
	docker compose -f infra/docker-compose.yml up -d

# ─── Database ─────────────────────────────────────────────────────────────────
db-migrate: ## Run Alembic migrations (apply pending)
	cd apps/api && uv run alembic upgrade head

db-rollback: ## Rollback last Alembic migration
	cd apps/api && uv run alembic downgrade -1

db-shell: ## Open psql shell in the running Postgres container
	docker compose -f infra/docker-compose.yml exec postgres \
	  psql -U docpilot -d docpilot

db-reset: ## Drop + recreate DB and run migrations (WIPES DATA)
	bash scripts/reset-db.sh

# ─── API (FastAPI) ────────────────────────────────────────────────────────────
api-install: ## Install Python dependencies via uv
	cd apps/api && uv sync --all-extras

api-dev: ## Run FastAPI dev server with hot reload
	cd apps/api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

api-worker: ## Run ARQ background worker
	cd apps/api && uv run arq app.workers.settings.WorkerSettings

api-test: ## Run API unit tests (fast, no external deps)
	cd apps/api && uv run pytest -m unit -v

api-test-integration: ## Run API integration tests (requires Postgres + Redis)
	cd apps/api && uv run pytest -m integration -v

api-lint: ## Lint API with ruff
	cd apps/api && uv run ruff check .

api-format: ## Format API with ruff
	cd apps/api && uv run ruff format .

api-type-check: ## Type-check API with mypy
	cd apps/api && uv run mypy app

# ─── Web (Next.js) ────────────────────────────────────────────────────────────
web-install: ## Install web dependencies via pnpm
	pnpm --filter web install

web-dev: ## Run Next.js dev server
	pnpm --filter web dev

web-build: ## Build Next.js for production
	pnpm --filter web build

web-test: ## Run Vitest unit tests
	pnpm --filter web test

web-test-watch: ## Run Vitest in watch mode
	pnpm --filter web test -- --watch

web-lint: ## Lint web with ESLint
	pnpm --filter web lint

web-type-check: ## Type-check web with tsc
	pnpm --filter web type-check

web-e2e: ## Run Playwright end-to-end tests
	pnpm --filter web test:e2e

# ─── Combined targets ─────────────────────────────────────────────────────────
install: ## Install all dependencies (pnpm + uv)
	pnpm install
	$(MAKE) api-install

lint: ## Lint everything
	$(MAKE) web-lint
	$(MAKE) api-lint

type-check: ## Type-check everything
	$(MAKE) web-type-check
	$(MAKE) api-type-check

test: ## Run all unit tests (web + API)
	$(MAKE) web-test
	$(MAKE) api-test

generate-types: ## Generate TypeScript client from FastAPI OpenAPI spec
	bash scripts/generate-types.sh

ci-check: ## Run all CI checks locally (lint + type-check + tests)
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test

# ─── Cleanup ─────────────────────────────────────────────────────────────────
clean: ## Remove build artefacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	rm -rf apps/web/.next apps/web/out apps/web/coverage
	rm -rf apps/api/htmlcov apps/api/.coverage
