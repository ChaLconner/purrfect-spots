# API Changelog

All notable changes to the Purrfect Spots API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.1.0] - 2026-01-14

### Added
- **HTTPS Redirect Middleware** - Automatic HTTP to HTTPS redirect in production
- **HSTS Header** - Strict-Transport-Security with 1 year max-age
- **Comprehensive Health Checks** - New `/health/*` endpoints:
  - `GET /health/live` - Liveness probe for orchestrators
  - `GET /health/ready` - Readiness probe checking all dependencies
  - `GET /health/dependencies` - Detailed dependency status
  - `GET /health/metrics` - Basic application metrics
- **Custom Exception Hierarchy** - Standardized error handling with:
  - `ValidationError` (422)
  - `AuthenticationError` (401)
  - `AuthorizationError` (403)
  - `RateLimitError` (429)
  - `NotFoundError` (404)
  - `ConflictError` (409)
  - `ExternalServiceError` (502)
  - `FileProcessingError` (400)
  - `CatDetectionError` (400)
- **CI/CD Pipeline** - GitHub Actions workflow with:
  - Backend tests with coverage
  - Frontend tests and type checking
  - Security scanning with Trivy
  - Automated Vercel deployments
- **Docker Support** - Production-ready Dockerfiles for backend and frontend
- **Frontend Sentry Integration** - Error monitoring for Vue.js application
- **Permissions-Policy Header** - Browser feature restrictions

### Changed
- **Security Headers Enhanced** - Updated CSP to allow Google OAuth and Sentry
- **X-XSS-Protection Header** - Added legacy XSS protection
- **ErrorBoundary Component** - Now reports errors to Sentry

### Security
- HTTPS enforcement in production
- HSTS preload support
- Enhanced CSP with frame-ancestors restriction

---

## [3.0.0] - 2025-12-15

### Added
- **API Versioning** - All endpoints now under `/api/v1/` prefix
- **Sentry Integration** - Error monitoring for backend
- **Structured Logging** - JSON logs in production, colored in development
- **Performance Logging** - `@log_performance` decorator for timing
- **Redis Rate Limiting** - Distributed rate limiting with Redis support

### Changed
- **Default Response Class** - Using `ORJSONResponse` for faster JSON serialization

### Removed
- **Legacy Routes** - Non-versioned routes removed
  - `/auth/*` → `/api/v1/auth/*`
  - `/upload/*` → `/api/v1/upload/*`
  - `/gallery/*` → `/api/v1/gallery/*`
  - `/profile/*` → `/api/v1/profile/*`

### Migration Guide
Update all API calls to use the `/api/v1/` prefix:
```javascript
// Before (v2.x)
fetch('/auth/login', ...)

// After (v3.x)
fetch('/api/v1/auth/login', ...)
```

---

## [2.1.0] - 2025-11-20

### Added
- **Refresh Token Support** - Long-lived refresh tokens with separate secret
- **Password Reset Flow** - Email-based password reset
- **Profile Bio** - Users can now add a biography

### Changed
- **JWT Expiration** - Access tokens now expire in 1 hour (was 24 hours)
- **Password Requirements** - Minimum 8 characters with at least one number

### Security
- Separate `JWT_REFRESH_SECRET` required in production
- Rate limiting on password reset endpoints

---

## [2.0.0] - 2025-10-15

### Added
- **Google OAuth PKCE** - Secure OAuth flow with PKCE verification
- **Magic Bytes Validation** - File type verification using magic numbers
- **Input Sanitization** - XSS prevention with bleach library
- **Security Logging** - Audit trail for security events

### Changed
- **File Upload** - Now requires cat detection confirmation
- **CORS Configuration** - Stricter origin validation

### Security
- Content-Security-Policy header
- X-Frame-Options: DENY
- Referrer-Policy header
- Input sanitization for all text fields

---

## [1.2.0] - 2025-09-01

### Added
- **Tags Support** - Photos can now have multiple tags
- **Tag Search** - Filter photos by tags
- **Popular Tags** - API endpoint for trending tags

### Changed
- **Gallery Pagination** - Server-side pagination (20 items default)

---

## [1.1.0] - 2025-08-15

### Added
- **Cat Detection** - Google Vision API integration
- **Location Search** - Search photos by location name

### Fixed
- Gallery loading performance issues

---

## [1.0.0] - 2025-07-01

### Added
- Initial release
- User authentication (email/password)
- Google OAuth login
- Photo upload with location
- Gallery view
- Map view with markers
- Basic profile management

---

## API Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET/PUT/PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input/validation |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | External service error |
| 503 | Service Unavailable | Maintenance/overload |
