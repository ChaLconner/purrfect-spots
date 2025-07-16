# /me Endpoint Documentation

## Overview
The `/auth/me` endpoint has been added to retrieve current user information using JWT authentication.

## Endpoint Details

### GET /auth/me
Returns the current authenticated user's information.

**Authentication Required:** Yes (JWT Bearer token)

**Request:**
```http
GET /auth/me
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "user_id_here",
  "email": "user@example.com",
  "name": "User Name",
  "password_hash": "hashed_password",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "google_id": null,
  "picture": null
}
```

**Error Responses:**

401 Unauthorized:
```json
{
  "detail": "Token expired"
}
```

```json
{
  "detail": "Invalid token"
}
```

```json
{
  "detail": "Invalid token payload"
}
```

404 Not Found:
```json
{
  "detail": "User not found"
}
```

## Implementation Details

### Location:
- Added to: `routes/auth_manual.py`
- Uses: `middleware.auth_middleware.get_current_user`

### Authentication Flow:
1. Client sends JWT token in Authorization header
2. Middleware decodes and validates the token
3. User ID extracted from token payload (`sub` field)
4. User data retrieved from database
5. User object returned directly

### Code:
```python
@router.get("/me")
async def get_user(current_user = Depends(get_current_user)):
    """
    Get current user information (simple version)
    """
    return current_user
```

## Usage Examples

### JavaScript/TypeScript:
```javascript
const token = localStorage.getItem('access_token');
const response = await fetch('/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const user = await response.json();
```

### Python Requests:
```python
import requests

token = "your_jwt_token_here"
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/auth/me", headers=headers)
user = response.json()
```

### cURL:
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer your_jwt_token_here"
```

## Differences from Existing /me Endpoint

### New Simple Version (auth_manual.py):
- Returns raw user data from database
- Simpler implementation
- Direct database object response

### Existing Version (auth_google.py):
- Returns formatted UserResponse model
- More structured response
- Designed for Google OAuth users

## Security Considerations

- JWT token must be valid and not expired
- Token must contain valid user ID in `sub` field
- User must exist in database
- Token secret must match server configuration

## Testing

Run the test script to verify the endpoint:
```bash
python test_me_endpoint.py
```

See usage examples:
```bash
python example_me_endpoint.py
```
