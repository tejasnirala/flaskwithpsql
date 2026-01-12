# Docker Guide

## Overview

This application includes Docker support for both development and production environments.

## Quick Start

### Development

```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# View logs
docker compose logs -f web

# Stop all services
docker compose down
```

### Production

```bash
# Use production configuration
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │    web      │───▶│     db      │    │    redis    │         │
│  │  (Flask)    │    │ (PostgreSQL)│    │  (Cache)    │         │
│  │  :5500      │    │   :5432     │    │   :6379     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                  │
│  ┌─────────────┐                                                │
│  │  pgadmin    │                                                │
│  │ (Optional)  │                                                │
│  │   :5050     │                                                │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Services

### web (Flask Application)

The main Flask application.

#### Development Features:

- Hot-reload enabled
- Source code mounted as volume
- Debug mode on

#### Production Features:

- Gunicorn with multiple workers
- No source code mount (baked into image)
- Health checks enabled

### db (PostgreSQL)

PostgreSQL 15 database with Alpine base.

- Persisted via Docker volume
- Initializes `users` schema automatically
- Health checks for startup ordering

### redis

Redis 7 for rate limiting and caching.

- Persisted via Docker volume
- Used by Flask-Limiter

### pgadmin (Optional)

Web-based PostgreSQL admin interface.

```bash
# Start with pgAdmin
docker compose --profile tools up
```

Access at: http://localhost:5050

- Email: admin@example.com
- Password: admin

## Configuration

### Environment Variables

```yaml
# docker-compose.yml
services:
  web:
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/flaskwithpsql
      - SECRET_KEY=dev-secret-key
      - RATELIMIT_STORAGE_URL=redis://redis:6379
```

### Custom Environment

Create a `.env` file for overrides:

```env
# .env
DB_PASSWORD=secure-password
SECRET_KEY=your-production-secret
```

## Dockerfile Stages

### Base Stage

```dockerfile
FROM python:3.11-slim as base
```

- Sets up Python environment
- Creates non-root user for security
- Sets working directory

### Dependencies Stage

```dockerfile
FROM base as dependencies
```

- Installs system dependencies (libpq for PostgreSQL)
- Installs Python requirements

### Development Stage

```dockerfile
FROM dependencies as development
```

- Installs development tools (pytest, black, etc.)
- Volume mounts for hot-reload
- Runs Flask development server

### Production Stage

```dockerfile
FROM dependencies as production
```

- Copies application code
- Removes unnecessary files
- Runs Gunicorn with multiple workers
- Includes health check

## Commands

### Build

```bash
# Build for development
docker compose build

# Build for production
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Force rebuild
docker compose build --no-cache
```

### Run

```bash
# Development
docker compose up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers
docker compose up --scale web=3
```

### Database Operations

```bash
# Run migrations
docker compose exec web flask db upgrade

# Create migration
docker compose exec web flask db migrate -m "Add new field"

# Seed database
docker compose exec web python db_manage.py seed

# Access database shell
docker compose exec db psql -U postgres -d flaskwithpsql
```

### Testing

```bash
# Run tests
docker compose exec web pytest

# Run with coverage
docker compose exec web pytest --cov=app

# Run specific tests
docker compose exec web pytest tests/test_routes/
```

### Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs web

# Follow logs
docker compose logs -f web

# Last N lines
docker compose logs --tail=100 web
```

### Shell Access

```bash
# Flask app shell
docker compose exec web flask shell

# Bash shell
docker compose exec web bash

# Database shell
docker compose exec db psql -U postgres
```

## Volumes

### Persistent Data

```yaml
volumes:
  postgres_data: # Database files
  redis_data: # Rate limit data
  pgadmin_data: # pgAdmin config
```

### Managing Volumes

```bash
# List volumes
docker volume ls

# Remove volumes (WARNING: deletes data!)
docker compose down -v

# Backup database
docker compose exec db pg_dump -U postgres flaskwithpsql > backup.sql

# Restore database
cat backup.sql | docker compose exec -T db psql -U postgres flaskwithpsql
```

## Health Checks

### Flask Application

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5500/health')"
```

### PostgreSQL

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s
  timeout: 5s
  retries: 5
```

## Production Considerations

### Security

1. **Non-root user**: Application runs as `appuser`
2. **No secrets in image**: Use environment variables
3. **Minimal image**: Uses slim base, removes dev files

### Performance

1. **Gunicorn**: 4 workers, 2 threads each
2. **Redis caching**: For rate limiting
3. **Resource limits**: Memory and CPU constraints

### Scaling

```yaml
# docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: "1"
      memory: 512M
    reservations:
      cpus: "0.5"
      memory: 256M
```

### Monitoring

Use `docker stats` or integrate with:

- Prometheus + Grafana
- Datadog
- New Relic

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs web

# Check if port is in use
lsof -i :5500

# Rebuild
docker compose build --no-cache
```

### Database connection issues

```bash
# Wait for database to be ready
docker compose up -d db
docker compose exec db pg_isready
docker compose up web
```

### Permission issues

```bash
# Fix ownership (from inside container)
chown -R appuser:appgroup /app

# Check file permissions
ls -la /app
```

### Volume issues

```bash
# Remove and recreate volumes
docker compose down -v
docker compose up --build
```

## CI/CD Integration

The Dockerfile is designed for CI/CD:

```yaml
# GitHub Actions example
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    target: production
    push: true
    tags: myregistry/flaskwithpsql:latest
```
