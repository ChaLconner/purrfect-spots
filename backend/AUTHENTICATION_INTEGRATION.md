# Authentication Integration Summary

## What was added:

### 1. Dependencies
- Added `bcrypt==4.1.2` for password hashing
- Added `email-validator==2.1.0` for email validation

### 2. AuthService Updates (`services/auth_service.py`)
- Added `hash_password()` method for password hashing
- Added `verify_password()` method for password verification
- Added `get_user_by_email()` method to find users by email
- Added `create_user()` method for creating users with email/password
- Added `authenticate_user()` method for email/password authentication
- Updated `create_access_token()` to include both `user_id` and `sub` claims

### 3. New Authentication Routes (`auth/routes.py`)
- Added `SignupRequest` model with EmailStr validation
- Added `LoginRequest` model with EmailStr validation
- Added `SimpleLoginResponse` model for consistent responses
- Added `POST /auth/signup` endpoint for user registration
- Added `POST /auth/login` endpoint for user authentication

### 4. Database Migration (`migrations/002_add_password_auth.sql`)
- Added `password_hash` column to users table
- Made `google_id` optional (nullable)
- Added unique constraint on email
- Updated database policies for password authentication

### 5. Updated User Models (`user_models/user.py`)
- Made `google_id` optional in User model
- Added `password_hash` field to User model
- Added `UserCreateWithPassword` model
- Added `UserLogin` model

## API Endpoints Available:

### Google OAuth:
- `POST /auth/google` - Login with Google ID token
- `POST /auth/google/exchange` - Exchange Google auth code for token

### Email/Password:
- `POST /auth/signup` - Register with email and password
- `POST /auth/login` - Login with email and password

### Common:
- `GET /auth/me` - Get current user information
- `POST /auth/logout` - Logout user

## Usage Examples:

### Signup:
```json
POST /auth/signup
{
    "email": "user@example.com",
    "password": "securepassword123",
    "name": "John Doe"
}
```

### Login:
```json
POST /auth/login
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

Both endpoints return:
```json
{
    "access_token": "jwt_token_here",
    "token_type": "bearer",
    "user": {
        "id": "user_id",
        "email": "user@example.com",
        "name": "John Doe",
        ...
    }
}
```
