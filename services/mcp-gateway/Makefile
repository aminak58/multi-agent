.PHONY: help test test-unit test-integration test-performance test-fast lint format clean install run docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "MCP Gateway - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Dependencies installed"

install-dev: install ## Install development dependencies
	. venv/bin/activate && pip install pytest pytest-asyncio pytest-cov flake8 black isort mypy pylint
	@echo "✓ Development dependencies installed"

test: ## Run all tests with coverage
	@bash scripts/run_tests.sh all true

test-unit: ## Run unit tests only
	@bash scripts/run_tests.sh unit true

test-integration: ## Run integration tests only
	@bash scripts/run_tests.sh integration true

test-performance: ## Run performance tests
	@bash scripts/run_tests.sh performance false

test-fast: ## Run fast tests (exclude slow tests)
	@bash scripts/run_tests.sh fast true

test-docker: ## Run tests in Docker environment
	@bash scripts/test_docker.sh

lint: ## Run code quality checks
	@bash scripts/lint.sh

format: ## Format code with black and isort
	@echo "Formatting code..."
	. venv/bin/activate && black app/ tests/
	. venv/bin/activate && isort app/ tests/
	@echo "✓ Code formatted"

clean: ## Clean up temporary files
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov coverage.xml
	@echo "✓ Cleaned up"

run: ## Run the application locally
	. venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the application in production mode
	. venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

docker-build: ## Build Docker image
	docker build -t mcp-gateway:latest .

docker-up: ## Start services with Docker Compose
	cd ../../.. && docker-compose up -d redis postgres
	cd ../../.. && docker-compose up --build mcp-gateway

docker-down: ## Stop Docker services
	cd ../../.. && docker-compose down

docker-logs: ## View Docker logs
	cd ../../.. && docker-compose logs -f mcp-gateway

db-migrate: ## Run database migrations
	. venv/bin/activate && alembic upgrade head

db-migrate-create: ## Create a new migration
	@read -p "Enter migration name: " name; \
	. venv/bin/activate && alembic revision -m "$$name"

db-downgrade: ## Downgrade database by one revision
	. venv/bin/activate && alembic downgrade -1

coverage-html: ## Generate HTML coverage report
	. venv/bin/activate && pytest --cov=app --cov-report=html tests/
	@echo "✓ Coverage report: htmlcov/index.html"

coverage-report: ## Show coverage report in terminal
	. venv/bin/activate && pytest --cov=app --cov-report=term-missing tests/

shell: ## Start Python shell with app context
	. venv/bin/activate && python -i -c "from app.main import app; from app.config import settings"

check: lint test ## Run all checks (lint + test)

ci: clean install-dev lint test ## Run CI pipeline (clean, install, lint, test)

.PHONY: all
all: clean install-dev lint test ## Run everything
