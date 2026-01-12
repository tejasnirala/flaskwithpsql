# JWT Authentication Guide

## Overview

This application uses JWT (JSON Web Tokens) for stateless authentication via Flask-JWT-Extended.

## How JWT Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         LOGIN FLOW                               │
└─────────────────────────────────────────────────────────────────┘

1. Client                          2. Server
   ┌─────────┐                        ┌─────────┐
   │ POST    │  email, password       │ Validate│
   │ /login  │ ───────────────────▶   │ creds   │
   └─────────┘                        └────┬────┘
                                           │
   ┌─────────┐                        ┌────▼────┐
   │ Store   │  access_token          │ Create  │
   │ tokens  │ ◀───────────────────   │ tokens  │
   └─────────┘  refresh_token         └─────────┘


┌─────────────────────────────────────────────────────────────────┐
│                       API REQUEST FLOW                           │
└─────────────────────────────────────────────────────────────────┘

1. Client                          2. Server
   ┌─────────┐                        ┌─────────┐
   │ GET     │  Authorization:        │ Verify  │
   │ /api/me │  Bearer <token>        │ token   │
   └─────────┘ ───────────────────▶   └────┬────┘
                                           │
   ┌─────────┐                        ┌────▼────┐
   │ Handle  │  User data             │ Get user│
   │ response│ ◀───────────────────   │ from DB │
   └─────────┘                        └─────────┘
```

## Token Types

### Access Token

- **Purpose**: Used for API requests
- **Lifetime**: 15 minutes (configurable)
- **Contains**: User ID, username, email

### Refresh Token

- **Purpose**: Get new access tokens
- **Lifetime**: 30 days (configurable)
- **Usage**: When access token expires

## API Endpoints

### POST /api/auth/login

Login with email and password to get tokens.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "Bearer",
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "user@example.com"
    }
  },
  "message": "Login successful"
}
```

### POST /api/auth/logout

Revoke the current access token.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "success": true,
  "message": "Logout successful"
}
```

### POST /api/auth/refresh

Get a new access token using refresh token.

**Headers:**

```
Authorization: Bearer <refresh_token>
```

**Response:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "Bearer"
  }
}
```

### GET /api/auth/me

Get current user information.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

## Protecting Routes

### Using @jwt_required()

```python
from flask_jwt_extended import jwt_required
from app.auth import get_current_user

@app.route("/api/protected")
@jwt_required()
def protected():
    user = get_current_user()
    return {"message": f"Hello, {user.username}!"}
```

### Optional Authentication

```python
from flask_jwt_extended import jwt_required

@app.route("/api/public-or-private")
@jwt_required(optional=True)
def public_or_private():
    user = get_current_user()
    if user:
        return {"message": f"Hello, {user.username}!"}
    return {"message": "Hello, anonymous!"}
```

## Configuration

Environment variables for JWT:

```env
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key
JWT_ACCESS_TOKEN_EXPIRES=900        # 15 minutes in seconds
JWT_REFRESH_TOKEN_EXPIRES=2592000   # 30 days in seconds
```

## Token Storage (Frontend)

Recommended approaches:

### 1. Memory + HttpOnly Cookie (Most Secure)

- Access token in memory (JavaScript variable)
- Refresh token in HttpOnly cookie

### 2. localStorage (Simpler)

- Both tokens in localStorage
- Vulnerable to XSS attacks

```javascript
// Store tokens
localStorage.setItem("access_token", response.data.access_token);
localStorage.setItem("refresh_token", response.data.refresh_token);

// Use in requests
fetch("/api/protected", {
  headers: {
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  },
});
```

## Token Refresh Flow

```javascript
async function apiRequest(url, options = {}) {
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${getAccessToken()}`,
    },
  });

  // If token expired, try to refresh
  if (response.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry with new token
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${getAccessToken()}`,
        },
      });
    } else {
      // Redirect to login
      window.location.href = "/login";
    }
  }

  return response;
}
```

## Security Best Practices

1. **Use HTTPS**: Never send tokens over HTTP
2. **Short access token lifetime**: 15-30 minutes
3. **Rotate refresh tokens**: Issue new refresh on each use
4. **Blacklist on logout**: Track revoked tokens
5. **Validate on each request**: Don't cache validation

## Error Responses

| Code | Error         | Description                   |
| ---- | ------------- | ----------------------------- |
| 401  | TOKEN_EXPIRED | Access token has expired      |
| 401  | TOKEN_INVALID | Token is malformed or invalid |
| 401  | UNAUTHORIZED  | No token provided             |
| 403  | FORBIDDEN     | User lacks permission         |

## Implementation Details

### Token Claims

```python
# What's stored in the token
{
  "sub": 1,           # User ID (subject)
  "username": "john",
  "email": "john@example.com",
  "iat": 1699999999,  # Issued at
  "exp": 1700000899,  # Expires at
  "jti": "uuid-...",  # Unique token ID
  "type": "access"    # Token type
}
```

### Blacklist Storage

Currently uses in-memory set (development only):

```python
_token_blacklist = set()

def revoke_token(jti):
    _token_blacklist.add(jti)
```

For production, use Redis:

```python
import redis
redis_client = redis.Redis()

def revoke_token(jti, exp):
    redis_client.setex(f"blacklist:{jti}", exp - time.time(), "true")
```
