# Authentication Routes Structure

## Overview
The authentication system has been refactored into separate modules for better organization and maintainability.

## New Structure

### Files Created:
```
backend/
├── routes/
│   ├── __init__.py
│   ├── auth_manual.py    # Email/Password authentication
│   └── auth_google.py    # Google OAuth authentication
├── main.py              # Updated with new imports
└── test_routes_structure.py  # Test script
```

### Route Modules:

#### 1. `routes/auth_manual.py`
Contains email/password authentication endpoints:
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login

#### 2. `routes/auth_google.py`
Contains Google OAuth authentication endpoints:
- `POST /auth/google` - Google token authentication
- `POST /auth/google/exchange` - Google code exchange
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout user

### Updated `main.py`
```python
from routes import auth_manual, auth_google  # <-- นำเข้า route ใหม่

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client():
    return supabase

# รวม route ทั้งหมด
app.include_router(auth_manual.router)
app.include_router(auth_google.router)
```

## API Endpoints

### Manual Authentication (`/auth`)
- `POST /auth/signup` - Register with email/password
- `POST /auth/login` - Login with email/password

### Google OAuth (`/auth`)
- `POST /auth/google` - Login with Google ID token
- `POST /auth/google/exchange` - Exchange Google auth code
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

## Request/Response Examples

### Manual Signup
```json
POST /auth/signup
{
    "email": "user@example.com",
    "password": "securepassword123",
    "name": "John Doe"
}
```

### Manual Login
```json
POST /auth/login
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

### Response Format
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "name": "John Doe",
        "created_at": "2025-01-01T00:00:00Z"
    }
}
```

## Benefits of This Structure

1. **Separation of Concerns**: Manual and Google auth are in separate modules
2. **Maintainability**: Easier to modify or extend each auth method
3. **Clarity**: Clear distinction between authentication methods
4. **Scalability**: Easy to add new authentication methods

## Testing
Run the test script to verify the structure:
```bash
python test_routes_structure.py
```

## Migration Notes
- Old `auth/routes.py` can be removed after verifying the new structure works
- Both authentication methods share the same `/auth` prefix
- All existing API endpoints remain the same (backward compatible)
