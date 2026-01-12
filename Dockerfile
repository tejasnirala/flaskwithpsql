# =============================================================================
# Base Image
# =============================================================================
# Using Python 3.11 slim for smaller image size while maintaining compatibility
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# =============================================================================
# Dependencies Stage
# =============================================================================
FROM base as dependencies

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Development Stage
# =============================================================================
FROM dependencies as development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-cov black isort flake8 mypy

# Copy application code
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5500

# Development command with hot-reload
CMD ["flask", "run", "--host=0.0.0.0", "--port=5500", "--reload"]

# =============================================================================
# Production Stage
# =============================================================================
FROM dependencies as production

# Copy application code
COPY --chown=appuser:appgroup . .

# Remove unnecessary files for production
RUN rm -rf tests/ docs/ *.md .git* .env.example

# Create logs directory
RUN mkdir -p logs && chown appuser:appgroup logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5500

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5500/health')" || exit 1

# Production command using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5500", "--workers", "4", "--threads", "2", "run:app"]
