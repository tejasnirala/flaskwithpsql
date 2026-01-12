# Flask with PostgreSQL

A production-grade Flask backend application with PostgreSQL database.
Built for learning purposes with best practices and comprehensive documentation.

## ✨ Features

| Feature                    | Description                                                      |
| -------------------------- | ---------------------------------------------------------------- |
| 🔐 **JWT Authentication**  | Secure token-based authentication with access and refresh tokens |
| 🛡️ **Rate Limiting**       | Protect APIs from abuse with configurable rate limits            |
| 📖 **OpenAPI/Swagger**     | Auto-generated API documentation                                 |
| ✅ **Input Validation**    | Pydantic-based request validation                                |
| 🏗️ **Service Layer**       | Clean architecture with separated business logic                 |
| 📊 **Structured Logging**  | JSON logs with request correlation                               |
| 🐳 **Docker Ready**        | Multi-stage Dockerfile for dev and production                    |
| 🔄 **CI/CD Pipeline**      | GitHub Actions for testing and deployment                        |
| 🧪 **Comprehensive Tests** | Unit, integration, and API tests                                 |

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and start
git clone https://github.com/yourusername/flaskwithpsql
cd flaskwithpsql
docker compose up

# Access the API at http://localhost:5500
# Swagger docs at http://localhost:5500/docs
```

### Option 2: Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python db_manage.py setup

# Run the application
python run.py
```

## 📁 Project Structure

```
flaskwithpsql/
├── app/
│   ├── __init__.py              # Application factory
│   ├── auth/                     # JWT authentication
│   │   ├── __init__.py          # JWT configuration
│   │   └── routes.py            # Auth endpoints
│   ├── models/                   # SQLAlchemy models
│   ├── routes/                   # API endpoints
│   ├── schemas/                  # Pydantic validation
│   ├── services/                 # Business logic
│   └── utils/                    # Utilities (logging, responses, rate limiting)
├── tests/                        # Test suite
├── docs/                         # Documentation
├── migrations/                   # Database migrations
├── docker/                       # Docker configuration
├── .github/workflows/            # CI/CD pipelines
├── config.py                     # Application configuration
├── run.py                        # Application entry point
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Docker Compose configuration
├── pyproject.toml                # Project configuration
└── requirements.txt              # Python dependencies
```

## 📖 API Documentation

Once running, access the interactive API docs:

| UI           | URL                                |
| ------------ | ---------------------------------- |
| Swagger UI   | http://localhost:5500/docs         |
| ReDoc        | http://localhost:5500/redoc        |
| OpenAPI JSON | http://localhost:5500/openapi.json |

## 🔐 Authentication

### Login

```bash
curl -X POST http://localhost:5500/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
```

### Use Token

```bash
curl http://localhost:5500/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## 📡 API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint   | Description          |
| ------ | ---------- | -------------------- |
| POST   | `/login`   | Get JWT tokens       |
| POST   | `/logout`  | Revoke token         |
| POST   | `/refresh` | Refresh access token |
| GET    | `/me`      | Get current user     |

### Users (`/api/users`)

| Method | Endpoint    | Description                |
| ------ | ----------- | -------------------------- |
| POST   | `/register` | Register new user          |
| GET    | `/`         | List all users (paginated) |
| GET    | `/<id>`     | Get user by ID             |
| PUT    | `/<id>`     | Update user                |
| DELETE | `/<id>`     | Soft delete user           |

### Health

| Method | Endpoint  | Description     |
| ------ | --------- | --------------- |
| GET    | `/`       | Welcome message |
| GET    | `/health` | Health check    |

## 🐳 Docker

### Development

```bash
# Start all services
docker compose up

# Run tests
docker compose exec web pytest

# Database migrations
docker compose exec web flask db upgrade
```

### Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_routes/test_users.py -v
```

## 🔧 Code Quality

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run all checks
pre-commit run --all-files

# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/

# Security scan
bandit -r app/
```

## ⚙️ Configuration

### Environment Variables

| Variable                    | Description                          | Default     |
| --------------------------- | ------------------------------------ | ----------- |
| `FLASK_ENV`                 | Environment (development/production) | development |
| `SECRET_KEY`                | Secret key for JWT                   | Required    |
| `DATABASE_URL`              | PostgreSQL connection URL            | Required    |
| `RATELIMIT_STORAGE_URL`     | Rate limit storage (memory/redis)    | memory://   |
| `JWT_ACCESS_TOKEN_EXPIRES`  | Access token lifetime (seconds)      | 900         |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh token lifetime (seconds)     | 2592000     |

## 📚 Documentation

Detailed documentation is available in the `docs/` folder:

| Document                                                 | Description                 |
| -------------------------------------------------------- | --------------------------- |
| [JWT Authentication](docs/JWT_AUTHENTICATION.md)         | Token-based auth guide      |
| [Rate Limiting](docs/RATE_LIMITING.md)                   | API rate limiting           |
| [Docker Guide](docs/DOCKER_GUIDE.md)                     | Container deployment        |
| [Testing Guide](docs/TESTING_GUIDE.md)                   | Writing and running tests   |
| [Services Layer](docs/SERVICES_LAYER.md)                 | Business logic architecture |
| [Logging System](docs/LOGGING_SYSTEM.md)                 | Structured logging          |
| [Pydantic Validation](docs/PYDANTIC_VALIDATION_GUIDE.md) | Input validation            |
| [API Responses](docs/STANDARDIZED_API_RESPONSES.md)      | Response format             |

## 🏗️ Architecture

```
HTTP Request
     │
     ▼
┌─────────────┐
│   Route     │  ← Thin, handles HTTP only
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Service    │  ← Business logic, transactions
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Model     │  ← Data access (SQLAlchemy)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │
└─────────────┘
```

## 🔗 Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- [Flask-Limiter](https://flask-limiter.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.
