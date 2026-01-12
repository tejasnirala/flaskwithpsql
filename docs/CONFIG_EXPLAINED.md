# Understanding `config.py` - Flask Configuration

> This guide explains how Flask configuration works, breaks down each part of the `config.py` file, and shows how configuration flows through your application.

---

## Table of Contents

1. [What is Configuration?](#what-is-configuration)
2. [Configuration Flow](#configuration-flow)
3. [Helper Functions](#helper-functions)
4. [The Config Classes](#the-config-classes)
5. [Configuration Properties](#configuration-properties)
6. [Validation System](#validation-system)
7. [Configuration Registry](#configuration-registry)
8. [How Flask Loads Configuration](#how-flask-loads-configuration)
9. [Environment Variables](#environment-variables)
10. [Best Practices](#best-practices)

---

## What is Configuration?

### Simple Definition

> **Configuration** = Settings that control how your application behaves

These settings include:

- Database connection details
- Security keys
- Debug mode on/off
- CORS settings
- And much more...

### Why Separate Configuration?

```
┌─────────────────────────────────────────────────────────────────────────┐
│  WHY USE A SEPARATE CONFIG FILE?                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. DIFFERENT ENVIRONMENTS NEED DIFFERENT SETTINGS                      │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│     │ Development  │  │   Testing    │  │  Production  │                │
│     ├──────────────┤  ├──────────────┤  ├──────────────┤                │
│     │ DEBUG=True   │  │ DEBUG=True   │  │ DEBUG=False  │                │
│     │ Local DB     │  │ Test DB      │  │ Cloud DB     │                │
│     │ Any CORS     │  │ Any CORS     │  │ Strict CORS  │                │
│     └──────────────┘  └──────────────┘  └──────────────┘                │
│                                                                         │
│  2. SECURITY - Keep secrets out of code                                 │
│     ❌ SECRET_KEY = 'my-secret' (in code, visible in Git)               │
│     ✅ SECRET_KEY = os.environ.get('SECRET_KEY') (from environment)     │
│                                                                         │
│  3. FLEXIBILITY - Change settings without changing code                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Flow

### How Config Gets Loaded

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Application starts (run.py)                                         │
│     │                                                                   │
│     │  config_name = os.environ.get('FLASK_ENV', 'development')          │
│     │  app = create_app(config_name)                                     │
│     │                                                                   │
│     ▼                                                                   │
│  2. create_app() in app/__init__.py                                     │
│     │                                                                   │
│     │  from config import config                                          │
│     │  app.config.from_object(config[config_name])                         │
│     │                              │                                    │
│     │                              ▼                                    │
│     │                    config = {                                      │
│     │                      'development': DevelopmentConfig,             │
│     │                      'production': ProductionConfig,               │
│     │                      'testing': TestingConfig,                     │
│     │                    }                                              │
│     │                                                                   │
│     ▼                                                                   │
│  3. Flask reads all UPPERCASE attributes from config class               │
│     │                                                                   │
│     │  DevelopmentConfig.DEBUG → app.config['DEBUG']                      │
│     │  DevelopmentConfig.SECRET_KEY → app.config['SECRET_KEY']            │
│     │  DevelopmentConfig.SQLALCHEMY_DATABASE_URI → app.config[...]        │
│     │                                                                   │
│     ▼                                                                   │
│  4. Extensions read from app.config                                      │
│     │                                                                   │
│     │  db.init_app(app)  # Reads SQLALCHEMY_DATABASE_URI                │
│     │  CORS(app, ...)    # Uses CORS settings                           │
│     │                                                                   │
│     ▼                                                                   │
│  5. Application is configured and ready!                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Code Flow Step by Step

```python
# Step 1: run.py
config_name = 'development'  # From FLASK_ENV
app = create_app(config_name)

# Step 2: app/__init__.py
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])  # config['development'] = DevelopmentConfig

# Step 3: Flask internally does this:
for key in dir(DevelopmentConfig):
    if key.isupper():  # Only UPPERCASE attributes
        app.config[key] = getattr(DevelopmentConfig, key)

# Step 4: Now you can access config anywhere
app.config['DEBUG']  # True
app.config['SECRET_KEY']  # 'dev-secret-key...'
```

---

## Helper Functions

The `config.py` file starts with three helper functions that convert environment variables to the correct Python types.

### 1. `get_env_bool()` - String to Boolean

```python
def get_env_bool(key: str, default: bool = False) -> bool:
    """Convert environment variable to boolean."""
    value = os.environ.get(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')
```

#### Why This is Needed

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PROBLEM: Environment variables are ALWAYS strings                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  In .env file:                                                           │
│  CORS_CREDENTIALS=true                                                  │
│                                                                         │
│  In Python:                                                             │
│  os.environ.get('CORS_CREDENTIALS')  # Returns 'true' (string!)         │
│                                                                         │
│  The problem:                                                           │
│  if os.environ.get('CORS_CREDENTIALS'):  # ALWAYS True!                 │
│      # Even 'false' string is truthy!                                   │
│                                                                         │
│  bool('false') → True   # String 'false' is truthy                      │
│  bool('0') → True       # String '0' is truthy                          │
│  bool('') → False       # Only empty string is falsy                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### How It Works

```python
# Example usage:
CORS_CREDENTIALS = get_env_bool('CORS_CREDENTIALS', False)

# Step by step:
# 1. Get env var or use default
value = os.environ.get('CORS_CREDENTIALS', 'False')  # 'true'

# 2. Convert to lowercase
value = value.lower()  # 'true'

# 3. Check if it's a "truthy" string
return value in ('true', '1', 'yes', 'on')  # True
```

#### Examples

| Environment Value           | Result  |
| --------------------------- | ------- |
| `CORS_CREDENTIALS=true`     | `True`  |
| `CORS_CREDENTIALS=1`        | `True`  |
| `CORS_CREDENTIALS=yes`      | `True`  |
| `CORS_CREDENTIALS=on`       | `True`  |
| `CORS_CREDENTIALS=false`    | `False` |
| `CORS_CREDENTIALS=0`        | `False` |
| `CORS_CREDENTIALS=anything` | `False` |
| (not set, default=False)    | `False` |

---

### 2. `get_env_int()` - String to Integer

```python
def get_env_int(key: str, default: int = 0) -> int:
    """Convert environment variable to integer."""
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default
```

#### Why This is Needed

```python
# Environment variables are strings!
os.environ.get('CORS_MAX_AGE')  # Returns '3600' (string)

# But Flask-CORS expects an integer:
CORS(app, max_age=3600)  # Not '3600'

# Without conversion:
max_age = os.environ.get('CORS_MAX_AGE', '3600')
max_age + 100  # ❌ Error: can't add int to string

# With conversion:
max_age = get_env_int('CORS_MAX_AGE', 3600)
max_age + 100  # ✅ Works: 3700
```

#### How It Works

```python
# Example: CORS_MAX_AGE=3600 in environment
result = get_env_int('CORS_MAX_AGE', 0)

# Step by step:
# 1. Get env var (string) or default
value = os.environ.get('CORS_MAX_AGE', 0)  # '3600'

# 2. Try to convert to int
try:
    return int('3600')  # 3600 (integer)
except (ValueError, TypeError):
    return 0  # Fallback if conversion fails
```

#### Error Handling

```python
# If env var has invalid value:
# CORS_MAX_AGE=not_a_number

get_env_int('CORS_MAX_AGE', 3600)
# int('not_a_number') raises ValueError
# Catches exception, returns default: 3600
```

---

### 3. `get_env_list()` - Comma-Separated String to List

```python
def get_env_list(key: str, default: str = '') -> List[str]:
    """Convert comma-separated environment variable to list."""
    value = os.environ.get(key, default)
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]
```

#### Why This is Needed

```python
# In .env file:
# CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://myapp.com

# Flask-CORS expects a list:
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173'])

# Not a string:
CORS(app, origins='http://localhost:3000,http://localhost:5173')  # Won't work correctly!
```

#### How It Works

```python
# Example: CORS_ORIGINS=http://localhost:3000, http://localhost:5173
result = get_env_list('CORS_ORIGINS')

# Step by step:
# 1. Get env var
value = 'http://localhost:3000, http://localhost:5173'

# 2. Check if empty
if not value:
    return []

# 3. Split by comma
items = value.split(',')  # ['http://localhost:3000', ' http://localhost:5173']

# 4. Strip whitespace and filter empty strings
result = [item.strip() for item in items if item.strip()]
# ['http://localhost:3000', 'http://localhost:5173']
```

#### Visual Explanation

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  get_env_list('CORS_ORIGINS')                                                        │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Input:  "http://localhost:3000, http://localhost:5173, https://myapp.com"           |
│                                                                                      │
│  Step 1: split(',')                                                                  │
│  ┌───────────────────────────┬────────────────────────────┬────────────────────────┐ │
│  │  'http://localhost:3000'  │  ' http://localhost:5173'  │  ' https://myapp.com'  │ │
│  └───────────────────────────┴────────────────────────────┴────────────────────────┘ │
│               ↓                              ↓                        ↓              │
│  Step 2: strip() each item                                                           │
│  ┌───────────────────────────┬───────────────────────────┬───────────────────────┐   │
│  │  'http://localhost:3000'  │  'http://localhost:5173'  │  'https://myapp.com'  │   │
│  └───────────────────────────┴───────────────────────────┴───────────────────────┘   │
│                                                                                      │
│  Output: ['http://localhost:3000', 'http://localhost:5173', 'https://myapp.com']     |
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## The Config Classes

### Class Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLASS INHERITANCE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                        ┌──────────────┐                                 │
│                        │    Config     │  ← Base class (common settings) │
│                        └──────┬───────┘                                 │
│                               │                                         │
│              ┌────────────────┼────────────────┐                        │
│              │                │                │                        │
│              ▼                ▼                ▼                        │
│  ┌──────────────────┐ ┌──────────────┐ ┌─────────────────┐              │
│  │ DevelopmentConfig │ │ TestingConfig │ │ ProductionConfig │              │
│  ├──────────────────┤ ├──────────────┤ ├─────────────────┤              │
│  │ DEBUG = True     │ │TESTING=True  │ │ DEBUG = False   │              │
│  │ SQLALCHEMY_ECHO  │ │ Test DB      │ │ Secure cookies  │              │
│  │ = True           │ │              │ │ HTTPS required  │              │
│  └──────────────────┘ └──────────────┘ └─────────────────┘              │
│                                                                         │
│  Child classes INHERIT all settings from Config                          │
│  and can OVERRIDE specific settings                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### How Inheritance Works

```python
class Config:
    SECRET_KEY = 'base-secret'
    DEBUG = False
    SQLALCHEMY_ECHO = False

class DevelopmentConfig(Config):  # Inherits from Config
    DEBUG = True  # Override
    SQLALCHEMY_ECHO = True  # Override
    # SECRET_KEY is inherited (not overridden)

# Result for DevelopmentConfig:
# SECRET_KEY = 'base-secret'  ← Inherited from Config
# DEBUG = True               ← Overridden
# SQLALCHEMY_ECHO = True     ← Overridden
```

---

### Base `Config` Class

The base class contains settings common to ALL environments:

```python
class Config:
    """Base configuration class."""

    # Security
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key...')
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'

    # CORS
    CORS_ORIGINS: List[str] = get_env_list('CORS_ORIGINS')
    CORS_METHODS: List[str] = get_env_list('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS')
    # ... more CORS settings

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {...}
```

#### Setting Categories

| Category    | Settings                                     | Purpose                       |
| ----------- | -------------------------------------------- | ----------------------------- |
| Security    | `SECRET_KEY`, `SESSION_COOKIE_*`             | Protect user sessions         |
| CORS        | `CORS_ORIGINS`, `CORS_METHODS`, etc.         | Control cross-origin requests |
| Database    | `SQLALCHEMY_*`                               | Database connection           |
| Application | `PREFERRED_URL_SCHEME`, `MAX_CONTENT_LENGTH` | General app behavior          |

---

### `DevelopmentConfig` Class

```python
class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG: bool = True  # Enable debug mode
    SQLALCHEMY_ECHO: bool = True  # Log SQL queries

    # Allow common local development ports
    CORS_ORIGINS: List[str] = [
        'http://localhost:3000',   # React
        'http://localhost:5173',   # Vite
        'http://localhost:8080',   # Vue CLI
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:8080',
    ]

    CORS_CREDENTIALS: bool = True
```

#### Why These Settings?

| Setting            | Value              | Reason                                       |
| ------------------ | ------------------ | -------------------------------------------- |
| `DEBUG`            | `True`             | Show detailed error pages during development |
| `SQLALCHEMY_ECHO`  | `True`             | See SQL queries in console for debugging     |
| `CORS_ORIGINS`     | Multiple localhost | Support various frontend frameworks          |
| `CORS_CREDENTIALS` | `True`             | Allow cookies during development             |

---

### `ProductionConfig` Class

```python
class ProductionConfig(Config):
    """Production configuration."""

    DEBUG: bool = False  # Never debug in production
    TESTING: bool = False
    SQLALCHEMY_ECHO: bool = False  # Don't log SQL (performance)

    # Security
    SESSION_COOKIE_SECURE: bool = True  # HTTPS only
    PREFERRED_URL_SCHEME: str = 'https'

    # CORS - from environment only
    CORS_CREDENTIALS: bool = get_env_bool('CORS_CREDENTIALS', True)

    # Better database pool for production
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }
```

#### Why These Settings?

| Setting                 | Value   | Reason                              |
| ----------------------- | ------- | ----------------------------------- |
| `DEBUG`                 | `False` | Never expose error details to users |
| `SESSION_COOKIE_SECURE` | `True`  | Cookies only sent over HTTPS        |
| `pool_size: 10`         | Larger  | Handle more concurrent requests     |

---

### `TestingConfig` Class

```python
class TestingConfig(Config):
    """Testing configuration."""

    TESTING: bool = True  # Enable testing mode
    DEBUG: bool = True    # Helpful for debugging tests

    # Use separate test database (class attribute, not @property)
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'TEST_DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/flaskwithpsql_test'
    )

    WTF_CSRF_ENABLED: bool = False  # Disable CSRF for tests
    CORS_ORIGINS: List[str] = ['*']  # Allow all in tests
```

#### Why These Settings?

| Setting            | Value                | Reason                                  |
| ------------------ | -------------------- | --------------------------------------- |
| `TESTING`          | `True`               | Flask enables testing-specific behavior  |
| Separate DB        | `flaskwithpsql_test`  | Don't pollute development data          |
| `WTF_CSRF_ENABLED` | `False`              | Simplify test requests                  |

---

## Building Database URI

### Why Not Use `@property`?

> ⚠️ **Important Lesson**: Flask's `from_object()` reads **class attributes**, not instance properties!

When you use `@property`, it only works on **instances**, not on the **class itself**:

```python
class Config:
    @property
    def DB_URL(self):
        return "postgresql://..."

# This is what Flask does:
app.config.from_object(Config)  # Passes the CLASS, not an instance!

# Flask internally does:
Config.DB_URL  # Returns <property object>, NOT the string!

# For @property to work, you need an INSTANCE:
config = Config()
config.DB_URL  # Returns "postgresql://..." ✅
```

### The Fix: Use a Helper Function

Instead of `@property`, we use a module-level function that's called at class definition time:

```python
# Helper function (at module level, before classes)
def _build_database_uri() -> str:
    """
    Build database URI from environment variables.
    Called at class definition time.
    """
    # Check for direct DATABASE_URL first
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Handle Heroku-style postgres:// URLs
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url

    # Build from individual components
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'flaskwithpsql')

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


class Config:
    # Called when class is defined - result stored as class attribute
    SQLALCHEMY_DATABASE_URI: str = _build_database_uri()
```

### Visual Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│  @property vs Helper Function with from_object()                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ❌ @property (DOESN'T WORK with from_object):                          │
│  ──────────────────────────────────────────────                         │
│  class Config:                                                           │
│      @property                                                          │
│      def SQLALCHEMY_DATABASE_URI(self):                                 │
│          return "postgresql://..."                                      │
│                                                                         │
│  app.config.from_object(Config)                                           │
│                              ↓                                          │
│  Config.SQLALCHEMY_DATABASE_URI  → <property object>  ❌                 │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────      │
│                                                                         │
│  ✅ Helper Function (WORKS with from_object):                           │
│  ─────────────────────────────────────────────                          │
│  def _build_database_uri():                                             │
│      return "postgresql://..."                                          │
│                                                                         │
│  class Config:                                                           │
│      SQLALCHEMY_DATABASE_URI = _build_database_uri()  # Called once!    │
│                                                                         │
│  app.config.from_object(Config)                                           │
│                              ↓                                          │
│  Config.SQLALCHEMY_DATABASE_URI  → "postgresql://..."  ✅                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  _build_database_uri() Function Flow                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Is DATABASE_URL set?                                                   │
│       │                                                                 │
│       ├── YES ──────────────────────────────────────────┐               │
│       │              ↓                                  │               │
│       │   Is it 'postgres://'?                          │               │
│       │       │                                         │               │
│       │       ├── YES: Replace with 'postgresql://'     │               │
│       │       │                                         │               │
│       │       └── NO: Use as-is                         │               │
│       │              ↓                                  │               │
│       │   Return DATABASE_URL ──────────────────────────┤               │
│       │                                                 │               │
│       │                                                 │               │
│       └── NO                                            │               │
│              ↓                                          │               │
│   Build from components:                                │               │
│   DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME       │               │
│              ↓                                          │               │
│   Return: postgresql://user:pass@host:port/dbname       |               │
│                                                         │               │
│                                                         ▼               │
│                              ┌─────────────────────────────┐            │
│                              │ Final Database URI          │            │
│                              └─────────────────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why the Heroku Fix?

```python
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
```

Heroku provides `DATABASE_URL` as `postgres://...` but SQLAlchemy 1.4+ requires `postgresql://...`:

```
Heroku gives:     postgres://user:pass@host:5432/db
SQLAlchemy needs: postgresql://user:pass@host:5432/db
```

### Key Takeaway

| Approach        | Works with `from_object(Class)`? | Works with `from_object(instance)`? |
| --------------- | -------------------------------- | ----------------------------------- |
| `@property`     | ❌ No                            | ✅ Yes                              |
| Helper function | ✅ Yes                           | ✅ Yes                              |
| Class attribute | ✅ Yes                           | ✅ Yes                              |

---

## Validation System

### The `validate()` Method

Each config class has a `validate()` method that checks for configuration problems:

```python
@classmethod
def validate(cls) -> List[str]:
    """
    Validate configuration and return list of errors.

    Returns:
        List of error messages. Empty list means valid.
    """
    errors = []

    if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
        errors.append("SECRET_KEY is using default value!")

    if len(cls.SECRET_KEY) < 32:
        errors.append("SECRET_KEY should be at least 32 characters")

    return errors
```

### Understanding `@classmethod`

```python
@classmethod
def validate(cls) -> List[str]:
    #          ↑
    #    First argument is the CLASS itself, not an instance
```

```
┌─────────────────────────────────────────────────────────────────────────┐
│  @classmethod vs Regular Method vs @staticmethod                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Regular method:                                                        │
│  def validate(self):     # Needs an instance: obj.validate()            │
│      return self.SECRET_KEY                                             │
│                                                                         │
│  @classmethod:                                                          │
│  def validate(cls):      # Called on class: Config.validate()            │
│      return cls.SECRET_KEY                                              │
│                                                                         │
│  @staticmethod:                                                         │
│  def validate():         # No access to class or instance               │
│      return "error"                                                     │
│                                                                         │
│  We use @classmethod because:                                           │
│  - We access class attributes (cls.SECRET_KEY)                          │
│  - We don't need an instance                                            │
│  - Subclasses get correct behavior (cls = DevelopmentConfig, etc.)       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Different Validation per Environment

```python
# Base Config - moderate validation
class Config:
    @classmethod
    def validate(cls):
        errors = []
        if cls.SECRET_KEY == 'dev-secret-key...':
            errors.append("Using default SECRET_KEY")
        return errors

# Development - lenient (allow defaults)
class DevelopmentConfig(Config):
    @classmethod
    def validate(cls):
        return []  # No validation, defaults are OK

# Production - strict (require everything)
class ProductionConfig(Config):
    @classmethod
    def validate(cls):
        errors = super().validate()  # Get base class errors

        if not os.environ.get('SECRET_KEY'):
            errors.append("SECRET_KEY required in production")
        if not cls.CORS_ORIGINS:
            errors.append("CORS_ORIGINS required in production")

        return errors
```

### How to Use Validation

```python
# In app/__init__.py or run.py
from config import config

def create_app(config_name='default'):
    config_class = config[config_name]

    # Validate configuration
    errors = config_class.validate()
    if errors:
        for error in errors:
            print(f"CONFIG ERROR: {error}")
        if config_name == 'production':
            raise ValueError("Invalid production configuration")

    app = Flask(__name__)
    app.config.from_object(config_class)
    # ...
```

---

## Configuration Registry

### The `config` Dictionary

```python
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

This dictionary maps string names to configuration classes:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CONFIGURATION REGISTRY                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  config['development'] ──────→ DevelopmentConfig class                    │
│  config['production']  ──────→ ProductionConfig class                     │
│  config['testing']     ──────→ TestingConfig class                        │
│  config['default']     ──────→ DevelopmentConfig class                    │
│                                                                         │
│  Usage:                                                                 │
│  app.config.from_object(config['development'])                            │
│                              │                                          │
│                              ▼                                          │
│                    DevelopmentConfig class                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### The `get_config()` Helper

```python
def get_config(env: Optional[str] = None) -> type:
    """
    Get configuration class for the specified environment.
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development').lower().strip()

    return config.get(env, config['default'])
```

This provides a cleaner way to get the config:

```python
# Instead of:
config_class = config[os.environ.get('FLASK_ENV', 'development')]

# You can use:
config_class = get_config()  # Automatically reads FLASK_ENV
```

---

## How Flask Loads Configuration

### The `from_object()` Method

When you call `app.config.from_object(ConfigClass)`:

```python
# Flask internally does something like this:
def from_object(self, obj):
    for key in dir(obj):
        if key.isupper():  # Only UPPERCASE
            self[key] = getattr(obj, key)
```

### What Gets Loaded

```python
class DevelopmentConfig:
    DEBUG = True                    # ✅ Loaded (uppercase)
    SQLALCHEMY_ECHO = True          # ✅ Loaded (uppercase)
    _private = 'secret'             # ❌ Not loaded (starts with _)
    helper_function = lambda: None  # ❌ Not loaded (lowercase)

    # ✅ Class attribute from function call - WORKS!
    SQLALCHEMY_DATABASE_URI = _build_database_uri()

    # ❌ @property - Does NOT work with from_object(Class)!
    # @property
    # def SOME_SETTING(self):       # Would return <property object>
    #     return '...'
```

### After Loading

```python
# After app.config.from_object(DevelopmentConfig):

app.config['DEBUG']  # True
app.config['SQLALCHEMY_DATABASE_URI']  # postgresql://...
app.config['SECRET_KEY']  # 'dev-secret...'

# These are NOT in app.config:
app.config['_private']  # KeyError
app.config['helper_function']  # KeyError
```

---

## Environment Variables

### How `.env` Works

```bash
# .env file
FLASK_ENV=development
SECRET_KEY=my-super-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

```python
# config.py
from dotenv import load_dotenv
load_dotenv()  # Loads .env file into os.environ

# Now these work:
os.environ.get('SECRET_KEY')  # 'my-super-secret-key-here'
os.environ.get('CORS_ORIGINS')  # 'http://localhost:3000,http://localhost:5173'
```

### Loading Order

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ENVIRONMENT VARIABLE PRIORITY (highest to lowest)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Actual environment variables (set in shell or system)               │
│     $ export SECRET_KEY=from-shell                                      │
│                                                                         │
│  2. .env file (loaded by python-dotenv)                                  │
│     SECRET_KEY=from-dotenv-file                                          │
│                                                                         │
│  3. Default values in code                                              │
│     os.environ.get('SECRET_KEY', 'default-value')                       │
│                                                                         │
│  Shell env vars OVERRIDE .env file!                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### 1. Never Commit Secrets

```bash
# .gitignore
.env
*.pem
*.key
```

### 2. Use `.env.example` for Documentation

```bash
# .env.example (committed to Git - template without real values)
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
CORS_ORIGINS=http://localhost:3000
```

### 3. Validate in Production

```python
if os.environ.get('FLASK_ENV') == 'production':
    errors = ProductionConfig.validate()
    if errors:
        raise ValueError(f"Config errors: {errors}")
```

### 4. Use Type Hints

```python
SECRET_KEY: str = os.environ.get('SECRET_KEY', 'default')
DEBUG: bool = True
CORS_MAX_AGE: int = 3600
```

### 5. Document All Settings

```python
class Config:
    # Security key for signing sessions
    # REQUIRED in production, minimum 32 characters
    SECRET_KEY: str = ...
```

---

## Summary

### Configuration Flow

```
.env file → load_dotenv() → os.environ → Helper Functions → Config Classes → Flask app.config
```

### Key Components

| Component           | Purpose                                |
| ------------------- | -------------------------------------- |
| `get_env_bool()`    | Convert env string to boolean          |
| `get_env_int()`     | Convert env string to integer          |
| `get_env_list()`    | Convert comma-separated string to list |
| `Config`             | Base settings for all environments     |
| `DevelopmentConfig`  | Debug mode, verbose logging            |
| `ProductionConfig`   | Security, performance optimizations    |
| `TestingConfig`      | Isolated test database                 |
| `validate()`        | Check configuration for errors          |
| `config` dict        | Map environment names to classes       |

---

Happy configuring! 🚀
