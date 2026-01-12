# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

-   Placeholder for upcoming features

---

## [1.0.0] - 2026-01-13

### Added

#### Core Features

-   Flask 3.0 application with application factory pattern
-   PostgreSQL database with SQLAlchemy ORM
-   Flask-Migrate for database migrations
-   OpenAPI/Swagger documentation with flask-openapi3

#### Authentication

-   JWT authentication with Flask-JWT-Extended
-   Access tokens (15 min) and refresh tokens (30 days)
-   Token blacklisting for secure logout
-   `/api/auth/login`, `/api/auth/logout`, `/api/auth/refresh`, `/api/auth/me` endpoints

#### Security

-   Secure password hashing with werkzeug (PBKDF2)
-   Rate limiting with Flask-Limiter
-   Input validation with Pydantic v2
-   Soft delete support for data recovery

#### API Endpoints

-   User registration: `POST /api/users/register`
-   User login: `POST /api/users/login`
-   User CRUD: `GET/PUT/DELETE /api/users/<id>`
-   User listing with pagination: `GET /api/users/`
-   Health check: `GET /health`

#### Architecture

-   Service layer for business logic separation
-   Standardized API response format
-   Centralized error handling
-   Structured logging with request correlation

#### DevOps

-   Docker support with multi-stage builds
-   docker-compose for local development
-   GitHub Actions CI/CD pipeline
-   Pre-commit hooks for code quality

#### Code Quality

-   Black code formatting
-   isort import sorting
-   Flake8 linting
-   mypy type checking
-   Bandit security scanning
-   pytest test suite with coverage

#### Documentation

-   Comprehensive README
-   API documentation via Swagger/ReDoc
-   Detailed docs for each feature
-   Code comments and docstrings

### Security

-   Replaced insecure SHA256 password hashing with PBKDF2
-   Added rate limiting to prevent brute-force attacks
-   Implemented JWT token blacklisting
-   Added security headers documentation

---

## [0.1.0] - 2026-01-01

### Added

-   Initial project setup
-   Basic Flask application
-   User model with SQLAlchemy
-   Basic CRUD endpoints

---

[Unreleased]: https://github.com/username/flaskwithpsql/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/username/flaskwithpsql/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/username/flaskwithpsql/releases/tag/v0.1.0
