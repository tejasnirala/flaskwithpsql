# Rate Limiting Guide

## Overview

Rate limiting protects your API from abuse by limiting how many requests a client can make in a given time period. This application uses Flask-Limiter for rate limiting.

## Why Rate Limiting?

1. **Prevent Brute-Force Attacks**: Limit login attempts
2. **Protect Against DoS**: Stop request floods
3. **Ensure Fair Usage**: No single client monopolizes resources
4. **Reduce Server Load**: Reject excess requests early

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     REQUEST FLOW                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────┐
│ Client  │───▶│ Rate Limit  │───▶│ Application │───▶│ Response│
│ Request │    │   Check     │    │   Logic     │    │         │
└─────────┘    └──────┬──────┘    └─────────────┘    └─────────┘
                      │
                      ▼
               ┌─────────────┐
               │ Under limit?│
               └──────┬──────┘
                      │
            ┌─────────┴─────────┐
            ▼                   ▼
      ┌──────────┐        ┌──────────┐
      │   YES    │        │    NO    │
      │ Continue │        │ 429 Error│
      └──────────┘        └──────────┘
```

## Default Limits

| Limit Type | Rate             | Description                |
| ---------- | ---------------- | -------------------------- |
| Global     | 200/day, 50/hour | Applied to all routes      |
| API        | 60/minute        | Standard API endpoints     |
| Auth       | 5/minute         | Login/sensitive operations |
| Read       | 120/minute       | GET requests               |
| Strict     | 3/minute         | Very sensitive operations  |

## Configuration

### Environment Variables

```env
# Rate limit storage (use Redis in production)
RATELIMIT_STORAGE_URL=memory://                    # Development
RATELIMIT_STORAGE_URL=redis://localhost:6379       # Production
```

### Code Configuration

```python
# app/utils/rate_limiter.py

limiter = Limiter(
    key_func=get_client_ip,
    storage_uri="memory://",            # or "redis://..."
    default_limits=["200 per day", "50 per hour"],
)
```

## Usage

### Apply to Routes

```python
from app.utils.rate_limiter import limiter, auth_limit, api_limit

# Use preset limits
@app.route("/api/login")
@auth_limit      # 5 per minute
def login():
    ...

@app.route("/api/users")
@api_limit       # 60 per minute
def get_users():
    ...

# Custom limit
@app.route("/api/resource")
@limiter.limit("10 per minute")
def get_resource():
    ...
```

### Available Decorators

```python
from app.utils.rate_limiter import (
    limiter,       # Base limiter (for custom limits)
    auth_limit,    # 5 per minute (login endpoints)
    api_limit,     # 60 per minute (standard API)
    read_limit,    # 120 per minute (GET requests)
    strict_limit,  # 3 per minute (sensitive operations)
)
```

## Rate Limit Headers

Responses include headers showing limit status:

```
X-RateLimit-Limit: 60           # Total allowed per period
X-RateLimit-Remaining: 45       # Remaining in current period
X-RateLimit-Reset: 1609459200   # When the limit resets (Unix timestamp)
```

## Error Response

When rate limited, clients receive a 429 response:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded: 5 per 1 minute"
  }
}
```

## Limit Syntax

Flask-Limiter supports various limit formats:

```python
# Fixed window
"100 per day"
"50 per hour"
"10 per minute"
"1 per second"

# Multiple limits
"100 per day; 10 per hour; 1 per minute"

# Dynamic limits
def dynamic_limit():
    if is_premium_user():
        return "1000 per day"
    return "100 per day"

@limiter.limit(dynamic_limit)
def api_endpoint():
    ...
```

## Identifying Clients

By default, clients are identified by IP address:

```python
def get_client_ip():
    # Check for proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr
```

### By User (when authenticated)

```python
def get_user_key():
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    if user_id:
        return f"user:{user_id}"
    return get_client_ip()

@limiter.limit("100 per hour", key_func=get_user_key)
def user_endpoint():
    ...
```

## Storage Backends

### Memory (Development)

```python
RATELIMIT_STORAGE_URL = "memory://"
```

- Simple, no setup required
- Resets on server restart
- Not distributed (doesn't work with multiple workers)

### Redis (Production)

```python
RATELIMIT_STORAGE_URL = "redis://localhost:6379/0"
```

- Persistent across restarts
- Works with multiple workers
- Supports distributed systems

### Redis Configuration

```python
# With authentication
RATELIMIT_STORAGE_URL = "redis://:password@localhost:6379/0"

# With SSL
RATELIMIT_STORAGE_URL = "rediss://localhost:6379/0"
```

## Best Practices

1. **Different Limits for Different Endpoints**

   - Stricter limits on authentication endpoints
   - Relaxed limits on read-only endpoints

2. **Consider User Context**

   - Higher limits for authenticated users
   - Premium users might get higher limits

3. **Use Redis in Production**

   - Memory storage doesn't persist
   - Redis works across multiple workers

4. **Return Helpful Headers**

   - Let clients know their limit status
   - They can implement backoff strategies

5. **Logging**
   - Log rate limit violations
   - Monitor for abuse patterns

## Exemptions

### Exempt Specific Endpoints

```python
@app.route("/health")
@limiter.exempt
def health():
    return {"status": "ok"}
```

### Exempt Based on Condition

```python
@limiter.request_filter
def exempt_based_on_condition():
    # Exempt internal requests
    return request.headers.get("X-Internal-Request") == "true"
```

## Docker/Production Setup

With Docker Compose, Redis is included:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    environment:
      - RATELIMIT_STORAGE_URL=redis://redis:6379
```

## Troubleshooting

### "Rate limit exceeded" during development

Reset the limit by restarting the server (when using memory storage).

### Limits not working with multiple workers

Use Redis storage instead of memory.

### Getting 429 behind a proxy

Ensure your proxy forwards the correct client IP:

```python
# Check X-Forwarded-For header
def get_client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)
```
