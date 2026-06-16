.PHONY: install dev test lint format typecheck docker-up docker-down demo worker migrate upgrade clean help

install: ## Install shared-core and project dependencies
	pip install -e "../shared-core[dev,docparse]" numpy
	pip install -e ".[dev]"

dev: ## Start the FastAPI development server
	python -m issue_pr_agent.main

test: ## Run the test suite with pytest
	pytest

lint: ## Lint source, tests, examples, and alembic with ruff
	ruff check src/issue_pr_agent tests examples alembic

format: ## Auto-format with ruff
	ruff format src/issue_pr_agent tests examples alembic

typecheck: ## Static type checking with pyright
	pyright src/

docker-up: ## Start PostgreSQL and Redis containers
	docker compose up -d

docker-down: ## Stop all Docker containers
	docker compose down

demo: ## Run the before/after walkthrough on demo_repo
	python examples/run_demo.py

worker: ## Start the Celery worker (requires a running broker)
	celery -A issue_pr_agent.worker worker --loglevel=info

migrate: ## Generate a new Alembic migration
	alembic revision --autogenerate -m "auto"

upgrade: ## Apply all pending Alembic migrations
	alembic upgrade head

clean: ## Remove caches and temporary files
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; shutil.rmtree('.pytest_cache', ignore_errors=True); shutil.rmtree('.ruff_cache', ignore_errors=True)"

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
