# Understanding CORS in Flask

> CORS (Cross-Origin Resource Sharing) controls which websites can access your API. This guide explains how Flask-CORS works and how to configure it properly.

---

## Table of Contents

1. [What is CORS?](#what-is-cors)
2. [Why Do We Need CORS?](#why-do-we-need-cors)
3. [Flask-CORS Default Behavior](#flask-cors-default-behavior)
4. [Configuration Options](#configuration-options)
5. [Node.js vs Flask Comparison](#nodejs-vs-flask-comparison)
6. [Common Configurations](#common-configurations)
7. [Route-Specific CORS](#route-specific-cors)
8. [Environment-Based Configuration](#environment-based-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## What is CORS?

### Simple Definition

> **CORS** = Cross-Origin Resource Sharing

It's a security feature built into browsers that controls which websites can make requests to your API.

### What is an "Origin"?

An **origin** is the combination of:

- **Protocol** (http or https)
- **Domain** (localhost, example.com)
- **Port** (3000, 5500, 80)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WHAT IS AN ORIGIN?                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  http://localhost:3000                                                  │
│  ─┬──   ─────┬─── ─┬──                                                  │
│   │          │     │                                                    │
│   │          │     └── Port: 3000                                       │
│   │          └── Domain: localhost                                      │
│   └── Protocol: http                                                    │
│                                                                         │
│  Different origins (each is unique):                                    │
│  • http://localhost:3000                                                │
│  • http://localhost:5000   ← Different port                             │
│  • https://localhost:3000  ← Different protocol                         │
│  • http://example.com:3000 ← Different domain                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Same-Origin vs Cross-Origin

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SAME-ORIGIN vs CROSS-ORIGIN                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Your API is at: http://localhost:5500                                  │
│                                                                         │
│  SAME-ORIGIN (allowed by default):                                      │
│  ├── http://localhost:5500/page1  ──→ http://localhost:5500/api  ✅     │
│  └── Same protocol, domain, and port                                    │
│                                                                         │
│  CROSS-ORIGIN (blocked by default):                                     │
│  ├── http://localhost:3000  ──→ http://localhost:5500/api  ❌           │
│  │   └── Different port!                                                │
│  ├── https://myapp.com  ──→ http://localhost:5500/api  ❌               │
│  │   └── Different domain and protocol!                                 │
│  └── Browser blocks these unless CORS is configured                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Why Do We Need CORS?

### The Problem

When you have:

- **Frontend** at `http://localhost:3000` (React, Vue, etc.)
- **Backend** at `http://localhost:5500` (Flask API)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THE CORS PROBLEM                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Frontend (localhost:3000)                                              │
│       │                                                                 │
│       │  fetch('http://localhost:5500/api/users')                       │
│       │                                                                 │
│       ▼                                                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         BROWSER                                   │  │
│  │                                                                   │  │
│  │  "Wait! This request is going to a DIFFERENT origin!"             │  │
│  │  "I need to check if the server allows this..."                   │  │
│  │                                                                   │  │
│  │  Does server send: Access-Control-Allow-Origin?                   │  │
│  │  ├── YES → Allow the request ✅                                   │  │
│  │  └── NO  → Block the request ❌                                   │  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│       │                                                                 │
│       ▼                                                                 │
│  Backend (localhost:5500)                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Without CORS Configuration

```javascript
// Frontend code
fetch("http://localhost:5500/api/users")
  .then((response) => response.json())
  .then((data) => console.log(data));

// Browser Console Error:
// ❌ Access to fetch at 'http://localhost:5500/api/users' from origin
//    'http://localhost:3000' has been blocked by CORS policy:
//    No 'Access-Control-Allow-Origin' header is present.
```

### With CORS Configuration

```python
# Backend (Flask)
from flask_cors import CORS

CORS(app, origins=['http://localhost:3000'])

# Now the response includes:
# Access-Control-Allow-Origin: http://localhost:3000

# Browser sees this header and allows the request ✅
```

---

## Flask-CORS Default Behavior

### Your Current Code

```python
# app/__init__.py
from flask_cors import CORS

CORS(app)  # No configuration provided
```

### What Default Does

When you call `CORS(app)` without any configuration:

| Setting                | Default Value | Meaning                      |
| ---------------------- | ------------- | ---------------------------- |
| `origins`              | `*`           | ALL origins allowed          |
| `methods`              | All methods   | GET, POST, PUT, DELETE, etc. |
| `allow_headers`        | `*`           | All headers allowed          |
| `supports_credentials` | `False`       | No cookies/auth              |

### Default Response Headers

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: *
```

### Is This Secure?

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SECURITY IMPLICATIONS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CORS(app) with no config allows ALL origins:                            │
│                                                                         │
│  ✅ http://localhost:3000        → Your frontend (good)                 │
│  ✅ https://your-production.com  → Your production site (good)          │
│  ⚠️ https://malicious-site.com   → Attacker's site (bad!)               │
│  ⚠️ https://phishing-page.com    → Phishing attempt (bad!)              │
│                                                                         │
│  For DEVELOPMENT:  CORS(app) is fine                                     │
│  For PRODUCTION:   You MUST specify allowed origins!                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Options

### All Available Options

```python
CORS(app,
    # Which origins can access your API
    origins=['http://localhost:3000', 'https://myapp.com'],

    # Which HTTP methods are allowed
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],

    # Which headers the client can send
    allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],

    # Which headers the client can read from response
    expose_headers=['X-Custom-Header', 'Content-Length'],

    # Allow cookies and authentication
    supports_credentials=True,

    # How long (seconds) browser can cache preflight response
    max_age=3600,

    # Send CORS headers even on error responses
    send_wildcard=False,

    # Automatically handle OPTIONS requests
    automatic_options=True
)
```

### Options Explained

#### 1. `origins` - Allowed Origins

```python
# Allow specific origins
origins=['http://localhost:3000', 'https://myapp.com']

# Allow all origins (not recommended for production)
origins='*'

# Allow origins matching a pattern (regex)
origins=r'https://.*\.myapp\.com'  # Allows all subdomains
```

#### 2. `methods` - Allowed HTTP Methods

```python
# Allow only safe methods
methods=['GET', 'HEAD', 'OPTIONS']

# Allow all CRUD operations
methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
```

#### 3. `allow_headers` - Request Headers

```python
# Common headers needed for APIs
allow_headers=['Content-Type', 'Authorization']

# Allow all headers
allow_headers='*'
```

#### 4. `supports_credentials` - Cookies & Auth

```python
# If your frontend sends cookies or Authorization headers
supports_credentials=True

# Important: Cannot use origins='*' with credentials=True!
# You must specify exact origins when using credentials
```

#### 5. `max_age` - Preflight Cache

```python
# Cache preflight response for 1 hour (3600 seconds)
max_age=3600

# Browser won't send OPTIONS request again for 1 hour
```

---

## Node.js vs Flask Comparison

### Node.js/Express CORS

```javascript
const cors = require("cors");

// Basic - allow all
app.use(cors());

// With configuration
app.use(
  cors({
    origin: ["http://localhost:3000", "https://myapp.com"],
    methods: ["GET", "POST", "PUT", "DELETE"],
    allowedHeaders: ["Content-Type", "Authorization"],
    credentials: true,
    maxAge: 3600,
  })
);

// Dynamic origin
app.use(
  cors({
    origin: function (origin, callback) {
      const allowedOrigins = ["http://localhost:3000"];
      if (!origin || allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error("Not allowed by CORS"));
      }
    },
  })
);
```

### Flask-CORS (Equivalent)

```python
from flask_cors import CORS

# Basic - allow all
CORS(app)

# With configuration
CORS(app,
    origins=['http://localhost:3000', 'https://myapp.com'],
    methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['Content-Type', 'Authorization'],
    supports_credentials=True,
    max_age=3600
)

# Dynamic origin (using a function)
def check_origin(origin):
    allowed_origins = ['http://localhost:3000']
    return origin in allowed_origins

CORS(app, origins=check_origin)
```

### Side-by-Side Comparison

| Feature     | Express (Node.js)              | Flask                         |
| ----------- | ------------------------------ | ----------------------------- |
| Package     | `cors`                         | `flask-cors`                   |
| Import      | `const cors = require('cors')` | `from flask_cors import CORS`  |
| Basic usage | `app.use(cors())`              | `CORS(app)`                   |
| Origins     | `origin: [...]`                | `origins=[...]`               |
| Methods     | `methods: [...]`               | `methods=[...]`               |
| Headers     | `allowedHeaders: [...]`        | `allow_headers=[...]`         |
| Credentials | `credentials: true`            | `supports_credentials=True`   |
| Max Age     | `maxAge: 3600`                 | `max_age=3600`                |

---

## Common Configurations

### 1. Development (Allow All)

```python
# Good for local development
CORS(app)
```

### 2. Production (Specific Origins)

```python
# Only allow your frontend domains
CORS(app,
    origins=[
        'https://myapp.com',
        'https://www.myapp.com'
    ]
)
```

### 3. API with Authentication

```python
# When frontend sends cookies or Authorization header
CORS(app,
    origins=['https://myapp.com'],
    supports_credentials=True,
    allow_headers=['Content-Type', 'Authorization']
)
```

### 4. Public API (Read-Only)

```python
# Public API that anyone can read
CORS(app,
    origins='*',
    methods=['GET', 'HEAD', 'OPTIONS']
)
```

### 5. Microservices (Internal APIs)

```python
# Only allow other internal services
CORS(app,
    origins=[
        'http://user-service:8001',
        'http://order-service:8002',
        'http://payment-service:8003'
    ]
)
```

---

## Route-Specific CORS

### Different CORS for Different Routes

```python
from flask_cors import CORS

CORS(app, resources={
    # Public API - anyone can access
    r"/api/public/*": {
        "origins": "*",
        "methods": ["GET"]
    },

    # Private API - only your frontend
    r"/api/private/*": {
        "origins": ["https://myapp.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "supports_credentials": True
    },

    # Admin API - only admin dashboard
    r"/api/admin/*": {
        "origins": ["https://admin.myapp.com"],
        "supports_credentials": True
    }
})
```

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ROUTE-SPECIFIC CORS                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  /api/public/*                                                          │
│  ├── Origins: * (anyone)                                                │
│  ├── Methods: GET only                                                  │
│  └── Example: /api/public/products                                      │
│                                                                         │
│  /api/private/*                                                         │
│  ├── Origins: https://myapp.com                                         │
│  ├── Methods: GET, POST, PUT, DELETE                                    │
│  ├── Credentials: Yes                                                   │
│  └── Example: /api/private/users/me                                     │
│                                                                         │
│  /api/admin/*                                                           │
│  ├── Origins: https://admin.myapp.com                                   │
│  ├── Credentials: Yes                                                   │
│  └── Example: /api/admin/dashboard                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Blueprint-Specific CORS

```python
from flask import Blueprint
from flask_cors import CORS

# Create blueprints
public_bp = Blueprint('public', __name__)
private_bp = Blueprint('private', __name__)

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(public_bp, url_prefix='/api/public')
    app.register_blueprint(private_bp, url_prefix='/api/private')

    # Apply CORS with route-specific config
    CORS(app, resources={
        r"/api/public/*": {"origins": "*"},
        r"/api/private/*": {"origins": ["https://myapp.com"]}
    })

    return app
```

---

## Environment-Based Configuration

### Using Environment Variables

```python
# config.py
import os

class Config:
    """Base configuration."""
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE']
    CORS_SUPPORTS_CREDENTIALS = True


class DevelopmentConfig(Config):
    """Development - allow all."""
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']


class ProductionConfig(Config):
    """Production - specific origins only."""
    CORS_ORIGINS = [
        'https://myapp.com',
        'https://www.myapp.com'
    ]
```

```python
# app/__init__.py
from flask import Flask
from flask_cors import CORS

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Apply CORS from config
    CORS(app,
        origins=app.config.get('CORS_ORIGINS', '*'),
        methods=app.config.get('CORS_METHODS', ['GET']),
        supports_credentials=app.config.get('CORS_SUPPORTS_CREDENTIALS', False)
    )

    return app
```

### Using .env File

```bash
# .env (development)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# .env (production)
CORS_ORIGINS=https://myapp.com,https://www.myapp.com
```

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Parse comma-separated origins from environment
    _cors_origins = os.environ.get('CORS_ORIGINS', '*')
    CORS_ORIGINS = _cors_origins.split(',') if _cors_origins != '*' else '*'
```

---

## Troubleshooting

### Common Errors

#### Error 1: "No 'Access-Control-Allow-Origin' header present"

```
❌ Access to fetch at 'http://localhost:5500/api' from origin
   'http://localhost:3000' has been blocked by CORS policy
```

**Cause:** CORS not configured or origin not in allowed list.

**Solution:**

```python
CORS(app, origins=['http://localhost:3000'])
```

---

#### Error 2: "Credential is not supported if the CORS header 'Access-Control-Allow-Origin' is '\*'"

```
❌ The value of the 'Access-Control-Allow-Origin' header must not be
   the wildcard '*' when the request's credentials mode is 'include'
```

**Cause:** Using `credentials: 'include'` in frontend with `origins='*'`.

**Solution:**

```python
# ❌ Wrong
CORS(app, origins='*', supports_credentials=True)

# ✅ Correct - specify exact origins
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
```

---

#### Error 3: "Method PUT is not allowed"

```
❌ Method PUT is not allowed by Access-Control-Allow-Methods
```

**Cause:** Method not in allowed list.

**Solution:**

```python
CORS(app, methods=['GET', 'POST', 'PUT', 'DELETE'])
```

---

#### Error 4: "Request header field Authorization is not allowed"

```
❌ Request header field Authorization is not allowed by
   Access-Control-Allow-Headers
```

**Cause:** Custom header not in allowed list.

**Solution:**

```python
CORS(app, allow_headers=['Content-Type', 'Authorization'])
```

---

### Debugging CORS

#### 1. Check Response Headers

```bash
# Use curl to see CORS headers
curl -I -X OPTIONS http://localhost:5500/api/users \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"

# Look for these headers in response:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET, POST, ...
# Access-Control-Allow-Headers: ...
```

#### 2. Check Browser DevTools

```
1. Open DevTools (F12)
2. Go to Network tab
3. Find the failed request
4. Check Response Headers for Access-Control-* headers
5. Check Console for specific error message
```

#### 3. Enable Flask-CORS Logging

```python
import logging
logging.getLogger('flask_cors').level = logging.DEBUG

CORS(app, origins=['http://localhost:3000'])
```

---

## Best Practices

### 1. Never Use Wildcard in Production

```python
# ❌ Bad for production
CORS(app)  # Allows all origins

# ✅ Good for production
CORS(app, origins=['https://myapp.com'])
```

### 2. Use Environment-Based Config

```python
# ✅ Different settings for different environments
if os.environ.get('FLASK_ENV') == 'production':
    CORS(app, origins=['https://myapp.com'])
else:
    CORS(app, origins=['http://localhost:3000'])
```

### 3. Be Specific with Headers

```python
# ❌ Too permissive
CORS(app, allow_headers='*')

# ✅ Only what you need
CORS(app, allow_headers=['Content-Type', 'Authorization'])
```

### 4. Only Enable Credentials When Needed

```python
# ❌ Don't enable by default
CORS(app, supports_credentials=True)

# ✅ Only if sending cookies/auth
# Check if your frontend actually needs it first
```

### 5. Limit Methods for Public APIs

```python
# ✅ Read-only for public endpoints
CORS(app, resources={
    r"/api/public/*": {
        "origins": "*",
        "methods": ["GET", "HEAD", "OPTIONS"]  # No POST, PUT, DELETE
    }
})
```

---

## Summary

### Quick Reference

```python
from flask_cors import CORS

# Development (allow all)
CORS(app)

# Production (specific origins)
CORS(app,
    origins=['https://myapp.com'],
    methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['Content-Type', 'Authorization'],
    supports_credentials=True
)

# Route-specific
CORS(app, resources={
    r"/api/public/*": {"origins": "*"},
    r"/api/private/*": {"origins": ["https://myapp.com"]}
})
```

### Configuration Cheat Sheet

| What You Want     | Configuration                               |
| ----------------- | ------------------------------------------ |
| Allow all origins | `origins='*'`                              |
| Specific origins   | `origins=['http://localhost:3000']`        |
| All HTTP methods  | `methods=['GET', 'POST', 'PUT', 'DELETE']` |
| Send cookies      | `supports_credentials=True`                |
| Custom headers    | `allow_headers=['Authorization']`          |
| Cache preflight    | `max_age=3600`                             |

### Development vs Production

| Environment | Configuration                                                  |
| ----------- | ------------------------------------------------------------- |
| Development | `CORS(app)` - Allow all for easy testing                      |
| Production  | `CORS(app, origins=['https://yoursite.com'])` - Specific only  |

---

Happy coding! 🚀
