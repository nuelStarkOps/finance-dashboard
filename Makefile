# Personal Finance OS — developer commands.
# Requires: Docker + Docker Compose, Python 3.12+, Node.js LTS, pnpm.
.DEFAULT_GOAL := help

PYTHON ?= python3
PNPM ?= pnpm

.PHONY: help up down logs db-up db-down \
        backend-install backend-dev frontend-install frontend-dev \
        fmt lint test check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

## ---- Full local environment (Docker) ----

up: ## Build and start the full stack (db + backend + frontend)
	docker compose up --build -d

down: ## Stop the stack
	docker compose down

logs: ## Tail all service logs
	docker compose logs -f

db-up: ## Start only PostgreSQL
	docker compose up -d db

db-down: ## Stop only PostgreSQL
	docker compose down db

## ---- Host-based development (Postgres in Docker) ----

backend-install: ## Install backend dependencies into a local venv
	cd backend && $(PYTHON) -m venv .venv && .venv/bin/pip install -e ".[dev]"

backend-dev: ## Run FastAPI with auto-reload on :8000
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend-install: ## Install frontend dependencies
	cd frontend && $(PNPM) install

frontend-dev: ## Run Next.js dev server on :3000
	cd frontend && $(PNPM) dev

## ---- Quality gates ----

fmt: ## Format all code
	cd backend && .venv/bin/ruff format . && .venv/bin/ruff check --fix .
	cd frontend && $(PNPM) format

lint: ## Lint all code
	cd backend && .venv/bin/ruff check .
	cd frontend && $(PNPM) lint

test: ## Run all tests (frontend tests arrive in Phase 3+)
	cd backend && .venv/bin/pytest

check: fmt lint test ## Run the full local quality gate
