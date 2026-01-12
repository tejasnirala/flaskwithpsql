# =============================================================================
# Makefile - Convenience commands for development
# =============================================================================
# Usage: make <command>
#
# Examples:
#   make install    - Install dependencies
#   make run        - Start development server
#   make test       - Run tests
#   make docker-up  - Start with Docker
# =============================================================================

.PHONY: help install run test lint format type-check security clean \
        docker-up docker-down docker-build docker-logs docker-shell \
        db-init db-migrate db-upgrade db-seed db-reset \
        pre-commit coverage docs

# Default target
help:
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║               Flask with PostgreSQL - Makefile                    ║"
	@echo "╠══════════════════════════════════════════════════════════════════╣"
	@echo "║ Development:                                                      ║"
	@echo "║   make install      - Install all dependencies                    ║"
	@echo "║   make run          - Start development server                    ║"
	@echo "║   make shell        - Open Flask shell                            ║"
	@echo "║                                                                   ║"
	@echo "║ Testing:                                                          ║"
	@echo "║   make test         - Run tests                                   ║"
	@echo "║   make coverage     - Run tests with coverage report              ║"
	@echo "║                                                                   ║"
	@echo "║ Code Quality:                                                     ║"
	@echo "║   make lint         - Run linters (flake8)                        ║"
	@echo "║   make format       - Format code (black, isort)                  ║"
	@echo "║   make type-check   - Run type checker (mypy)                     ║"
	@echo "║   make security     - Run security scan (bandit)                  ║"
	@echo "║   make pre-commit   - Run all pre-commit hooks                    ║"
	@echo "║                                                                   ║"
	@echo "║ Database:                                                         ║"
	@echo "║   make db-init      - Initialize migrations                       ║"
	@echo "║   make db-migrate   - Create new migration                        ║"
	@echo "║   make db-upgrade   - Apply migrations                            ║"
	@echo "║   make db-seed      - Seed sample data                            ║"
	@echo "║   make db-reset     - Reset database                              ║"
	@echo "║                                                                   ║"
	@echo "║ Docker:                                                           ║"
	@echo "║   make docker-up    - Start all services                          ║"
	@echo "║   make docker-down  - Stop all services                           ║"
	@echo "║   make docker-build - Rebuild images                              ║"
	@echo "║   make docker-logs  - View logs                                   ║"
	@echo "║   make docker-shell - Access container shell                      ║"
	@echo "║                                                                   ║"
	@echo "║ Cleanup:                                                          ║"
	@echo "║   make clean        - Remove cache and build files                ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"

# =============================================================================
# Development
# =============================================================================

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	pip install -e ".[dev]"
	@echo "✅ Dependencies installed!"

install-dev:
	@echo "🔧 Installing development dependencies..."
	pip install -r requirements.txt
	pip install black isort flake8 mypy bandit pytest pytest-cov pre-commit
	pre-commit install
	@echo "✅ Development environment ready!"

run:
	@echo "🚀 Starting development server..."
	python run.py

shell:
	@echo "🐚 Opening Flask shell..."
	flask shell

# =============================================================================
# Testing
# =============================================================================

test:
	@echo "🧪 Running tests..."
	pytest -v

test-fast:
	@echo "🧪 Running tests (fail fast)..."
	pytest -x -v

coverage:
	@echo "📊 Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "📄 Coverage report saved to htmlcov/index.html"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "🔍 Running linter..."
	flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503

format:
	@echo "🎨 Formatting code..."
	black app/ tests/ --line-length=100
	isort app/ tests/ --profile=black --line-length=100
	@echo "✅ Code formatted!"

type-check:
	@echo "🔎 Running type checker..."
	mypy app/ --ignore-missing-imports

security:
	@echo "🔒 Running security scan..."
	bandit -r app/ -x tests/

pre-commit:
	@echo "🔄 Running pre-commit hooks..."
	pre-commit run --all-files

check: lint type-check security test
	@echo "✅ All checks passed!"

# =============================================================================
# Database
# =============================================================================

db-init:
	@echo "🗄️ Initializing migrations..."
	python db_manage.py init

db-migrate:
	@echo "📝 Creating migration..."
	python db_manage.py migrate

db-upgrade:
	@echo "⬆️ Applying migrations..."
	python db_manage.py upgrade

db-downgrade:
	@echo "⬇️ Rolling back migration..."
	python db_manage.py downgrade

db-seed:
	@echo "🌱 Seeding database..."
	python db_manage.py seed

db-reset:
	@echo "🔄 Resetting database..."
	python db_manage.py reset

db-setup:
	@echo "🚀 Full database setup..."
	python db_manage.py setup

# =============================================================================
# Docker
# =============================================================================

docker-up:
	@echo "🐳 Starting Docker services..."
	docker compose up -d
	@echo "✅ Services started!"
	@echo "   - API: http://localhost:5500"
	@echo "   - Swagger: http://localhost:5500/docs"

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker compose down
	@echo "✅ Services stopped!"

docker-build:
	@echo "🔨 Building Docker images..."
	docker compose build --no-cache

docker-logs:
	@echo "📋 Showing logs..."
	docker compose logs -f

docker-shell:
	@echo "🐚 Opening container shell..."
	docker compose exec web bash

docker-test:
	@echo "🧪 Running tests in Docker..."
	docker compose exec web pytest -v

docker-prod:
	@echo "🚀 Starting production services..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	docker compose down -v --rmi local
	@echo "✅ Docker resources cleaned!"

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

clean-all: clean
	@echo "🧹 Deep cleaning..."
	rm -rf build/ dist/
	@echo "✅ Deep cleanup complete!"
