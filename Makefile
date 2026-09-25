.PHONY: test test-core test-backend test-frontend dev-backend dev-frontend install help

help:
	@echo "Reconstruct Monorepo Commands:"
	@echo "  make test          - Run core and frontend tests"
	@echo "  make test-core     - Run core interface pytest suite"
	@echo "  make test-backend  - Run backend FastAPI pytest suite"
	@echo "  make test-frontend - Run frontend vitest suite"
	@echo "  make dev-backend   - Start FastAPI dev server"
	@echo "  make dev-frontend  - Start React dev server"

test: test-core test-frontend

test-core:
	pytest core/tests -v || backend/.venv/Scripts/pytest core/tests -v

test-backend:
	pytest backend/tests -v || backend/.venv/Scripts/pytest backend/tests -v

test-frontend:
	npm --prefix frontend test

dev-backend:
	backend/.venv/Scripts/uvicorn backend.main:app --reload --port 8000

dev-frontend:
	npm --prefix frontend run dev
