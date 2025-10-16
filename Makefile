.PHONY: help setup run docker-up docker-down migrate migrate-create clean test

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup:  ## Setup the project (create venv, install dependencies)
	@./setup.sh

run:  ## Run the FastAPI application
	@./run.sh

docker-up:  ## Start PostgreSQL and Elasticsearch with Docker
	docker-compose up -d

docker-down:  ## Stop Docker services
	docker-compose down

migrate:  ## Run database migrations
	alembic upgrade head

migrate-create:  ## Create a new migration (usage: make migrate-create MSG="description")
	alembic revision --autogenerate -m "$(MSG)"

clean:  ## Clean up Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

test:  ## Run tests (when implemented)
	@echo "Tests not yet implemented"
