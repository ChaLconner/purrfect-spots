# Authentication Form Component

## Overview
The `AuthForm.vue` component provides a dual-mode authentication interface for both user login and registration with email/password authentication.

## Features
- **Dual Mode**: Switch between login and signup modes
- **Email/Password Authentication**: Traditional form-based authentication
- **Form Validation**: Built-in email and password validation
- **Loading States**: Shows loading indicators during authentication
- **Error Handling**: Displays error messages from the API
- **Responsive Design**: Works on both desktop and mobile
- **Thai Language Support**: UI text in Thai language

## Component Structure

### Files Created:
```
frontend/src/
├── components/
│   └── AuthForm.vue          # Main authentication form component
├── views/
│   └── AuthView.vue          # View wrapper for the auth form
└── router/
    └── index.ts              # Updated with auth route
```

### Dependencies Added:
- `axios` - For HTTP requests to the authentication API

## Usage

### 1. Direct Component Usage
```vue
<template>
  <AuthForm />
</template>

<script setup lang="ts">
import AuthForm from '../components/AuthForm.vue';
</script>
```

### 2. Route Access
Navigate to `/auth` to access the authentication form.

### 3. Navigation Integration
The component is integrated into the NavBar with a "สมัครสมาชิก" (Register) button.

## API Integration

### Endpoints Used:
- `POST /auth/login` - User login
- `POST /auth/signup` - User registration

### Request Format:

#### Login:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Signup:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

### Response Format:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

## State Management

### LocalStorage Keys:
- `access_token` - JWT authentication token
- `user` - User data object

### Auth Store Integration:
The component is compatible with the existing auth store and supports both:
- New token keys: `access_token`, `user`
- Legacy token keys: `auth_token`, `user_data`

## Component Props & Events

### Internal State:
- `isLogin` - Boolean to toggle between login/signup modes
- `isLoading` - Loading state during API calls
- `errorMessage` - Error message display
- `form` - Reactive form data (email, password, name)

### Methods:
- `toggleMode()` - Switch between login and signup modes
- `handleSubmit()` - Process form submission and authentication

## Styling

### CSS Classes:
- `.input` - Form input styling
- `.btn` - Button styling with hover effects
- `.btn:disabled` - Disabled button styling

### Design Features:
- Rounded corners and shadows
- Responsive layout
- Blue color scheme for primary actions
- Error message styling in red

## Error Handling

### Error Types:
- **API Errors**: Displays server error messages
- **Network Errors**: Shows generic error message
- **Validation Errors**: Built-in HTML5 validation

### Error Messages:
- Thai language error messages
- Clear user feedback
- Automatic error clearing on form changes

## Integration with Existing System

### Compatibility:
- Works alongside existing Google OAuth authentication
- Shares the same auth store and user management
- Compatible with existing middleware and route guards

### Navigation Flow:
1. User clicks "สมัครสมาชิก" in NavBar
2. Navigates to `/auth` route
3. Can toggle between login/signup modes
4. On successful authentication, redirects to home page
5. Token and user data saved to localStorage
6. Auth store updated with new authentication state

## Testing

### Build Test:
```bash
npm run build
```

### Manual Testing:
1. Navigate to `/auth`
2. Test signup with new user credentials
3. Test login with existing credentials
4. Verify token storage in localStorage
5. Check auth state in NavBar

## Security Considerations

### Token Storage:
- Tokens stored in localStorage
- Automatic token cleanup on logout
- Compatible with existing auth middleware

### API Security:
- HTTPS recommended for production
- JWT tokens with expiration
- Server-side validation of all requests

## Future Enhancements

### Possible Improvements:
1. **Password Strength Indicator**
2. **Email Verification**
3. **Forgot Password Feature**
4. **Social Login Integration**
5. **Remember Me Option**
6. **Multi-language Support**

## Backend Integration

### Required Backend Endpoints:
- Ensure backend authentication routes are running
- Database migration for password authentication
- CORS configuration for frontend domain

### Environment Variables:
- Backend API URL configured in component
- Default: `http://localhost:8000`
