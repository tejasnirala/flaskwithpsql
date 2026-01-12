# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### Do NOT

-   ❌ Open a public GitHub issue
-   ❌ Discuss the vulnerability publicly
-   ❌ Share details on social media

### Do

1. **Email the maintainers** directly at: [your-email@example.com]

2. **Include in your report**:

    - Description of the vulnerability
    - Steps to reproduce
    - Potential impact
    - Suggested fix (if any)

3. **Allow time** for response (typically within 48 hours)

### What to Expect

1. **Acknowledgment**: We'll acknowledge receipt within 48 hours
2. **Assessment**: We'll assess the severity and impact
3. **Fix**: We'll work on a fix and coordinate disclosure
4. **Credit**: We'll credit you in the release notes (if desired)

## Security Best Practices

This project follows these security practices:

### Authentication

-   ✅ JWT tokens with short expiration (15 min access, 30 day refresh)
-   ✅ Token blacklisting for logout
-   ✅ Secure password hashing (PBKDF2)

### API Protection

-   ✅ Rate limiting on all endpoints
-   ✅ Stricter limits on authentication endpoints
-   ✅ Input validation with Pydantic

### Data Protection

-   ✅ Soft deletion (data recovery possible)
-   ✅ Sensitive data masking in logs
-   ✅ No password exposure in responses

### Code Quality

-   ✅ Pre-commit hooks with security scans (Bandit)
-   ✅ Dependency vulnerability scanning
-   ✅ Type checking (mypy)

## Security Headers

The following headers are recommended for production:

```python
# Recommended security headers
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

Consider using Flask-Talisman for automatic security headers.

## Dependencies

We regularly update dependencies to address security vulnerabilities:

```bash
# Check for vulnerable packages
pip install safety
safety check

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Thank You

Thank you for helping keep this project and its users safe!
