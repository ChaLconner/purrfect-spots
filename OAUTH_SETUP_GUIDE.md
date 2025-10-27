# Google OAuth Setup Guide

This guide explains how to properly configure Google OAuth for the Purrfect Spots application.

## Overview

The application uses Google OAuth 2.0 with PKCE (Proof Key for Code Exchange) for secure authentication. The flow involves:

1. Frontend generates a PKCE code verifier and challenge
2. User is redirected to Google for authentication
3. Google redirects back with an authorization code
4. Backend exchanges the code for tokens using the code verifier
5. Backend creates a JWT token for the user session

## Configuration Requirements

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Google OAuth2 API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Name: Purrfect Spots (or your preferred name)

### 2. Authorized Redirect URIs

You must add the following redirect URIs to your Google OAuth credentials:

**For Development:**
```
http://localhost:5173/auth/callback
```

**For Production:**
```
https://your-frontend-domain.vercel.app/auth/callback
```

⚠️ **Important:** The redirect URI must exactly match what the application sends to Google, including the protocol (http/https) and port number.

### 3. Environment Variables

#### Backend (.env)
```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# CORS Configuration (must include your frontend URL)
CORS_ORIGINS=http://localhost:5173,https://your-frontend-domain.vercel.app
```

#### Frontend (.env)
```bash
# Google OAuth Configuration
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# API Configuration
VITE_API_BASE_URL=http://localhost:8000  # or your production backend URL
```

## Common Issues and Solutions

### Issue: "invalid_grant" Error

**Cause:** This typically occurs when:
1. The redirect URI doesn't match what's configured in Google Cloud Console
2. The authorization code has expired (codes expire after 10 minutes)
3. The code has already been used (codes are single-use)

**Solution:**
1. Verify the redirect URI in Google Cloud Console matches exactly
2. Ensure the frontend and backend are using the same redirect URI
3. Check that the CORS_ORIGINS environment variable includes your frontend URL

### Issue: "redirect_uri_mismatch" Error

**Cause:** The redirect URI sent to Google doesn't match any authorized redirect URIs.

**Solution:**
1. Add the exact redirect URI to your Google OAuth credentials
2. Check for typos, missing ports, or protocol mismatches (http vs https)

### Issue: "code_verifier" Missing

**Cause:** The PKCE flow requires a code verifier to be stored in session storage.

**Solution:**
1. Ensure the frontend generates and stores the code verifier before redirecting
2. Check that session storage is available and not being cleared

## Testing the OAuth Flow

1. Start the backend server (`python main.py` or `uvicorn main:app --reload`)
2. Start the frontend development server (`npm run dev`)
3. Navigate to the login page
4. Click "Sign in with Google"
5. Complete the Google authentication
6. Verify you're redirected back to the application and logged in

## Debugging Tips

1. Check the browser console for error messages
2. Verify the redirect URI in the network requests
3. Ensure all environment variables are properly set
4. Check that the Google OAuth credentials are active and not expired

## Security Considerations

1. Never expose the Google Client Secret in frontend code
2. Use HTTPS in production
3. Regularly rotate your OAuth credentials
4. Restrict your OAuth keys to specific domains when possible
5. Monitor your OAuth usage for suspicious activity