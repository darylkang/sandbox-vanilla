SHELL := /bin/bash

ENV ?= .env
export $(shell sed -n 's/^[A-Za-z_][A-Za-z0-9_]*=.*/\1/p' $(ENV) 2>/dev/null)

.PHONY: help dev app redis-up redis-down logs lint fmt clean reset

help:
	@echo "Targets:"
	@echo "  make dev         - Start Redis (compose) and run Streamlit (loads .env)"
	@echo "  make app         - Run Streamlit only (loads .env)"
	@echo "  make redis-up    - Start Redis via Docker Compose"
	@echo "  make redis-down  - Stop Redis and remove container"
	@echo "  make logs        - Tail Redis logs"
	@echo "  make lint        - Lint with ruff (if installed)"
	@echo "  make fmt         - Format with ruff (if installed)"
	@echo "  make clean       - Remove __pycache__ and temp files"
	@echo "  make reset       - Flush Redis DB 0 (DANGEROUS: blows away keys)"

dev: redis-up app

app:
	@python -c "import dotenv, os; dotenv.load_dotenv('$(ENV)'); import os; os.system('streamlit run app.py')"

redis-up:
	@docker compose up -d
	@docker ps --filter "name=redis" --format "table {{.Names}}\t{{.Status}}"

redis-down:
	@docker compose down

logs:
	@docker compose logs -f

lint:
	@command -v ruff >/dev/null 2>&1 && ruff check . || echo "ruff not installed; skip"

fmt:
	@command -v ruff >/dev/null 2>&1 && ruff format . || echo "ruff not installed; skip"

clean:
	@find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete

reset:
	@echo "Flushing Redis DB 0 (are you sure)?"
	@echo "3.."; sleep 0.5; echo "2.."; sleep 0.5; echo "1.."; sleep 0.5
	@docker exec -it redis-local redis-cli FLUSHDB
