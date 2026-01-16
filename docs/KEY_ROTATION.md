# Key Rotation Procedures

Regular rotation of cryptographic keys is essential for maintaining system security. This document outlines the procedures for rotating keys in the Purrfect Spots application.

## 1. JWT Secrets

### Frequency
- **Access Token Secret (`JWT_SECRET`)**: Rotate every 3-6 months.
- **Refresh Token Secret (`JWT_REFRESH_SECRET`)**: Rotate every 6-12 months.
- **Immediate Rotation**: Rotate immediately if a security breach is suspected.

### Procedure
1. **Generate New Secret**: Generate a cryptographically strong random string (at least 64 characters).
   ```bash
   openssl rand -hex 64
   ```
2. **Update Environment Variables**:
   - Update `JWT_SECRET` or `JWT_REFRESH_SECRET` in your `.env` file or cloud configuration variables.
   
3. **Restart Services**: Restart the backend application to load the new keys.

### Impact of Rotation
- **Access Token Secret**: All currently active access tokens will immediately become invalid. Users will need to use their refresh token to get a new access token (automatic in frontend) or log in again.
- **Refresh Token Secret**: All valid refresh tokens will become invalid. **All users will be logged out** and must log in again.

## 2. API Keys (Google Maps, Vision)

### Frequency
- Rotate if a key is suspected to be leaked or on a yearly basis.

### Procedure
1. **Generate New Key**: Create a new API key in the Google Cloud Console.
2. **Update Environment Variables**: Update `VITE_GOOGLE_MAPS_API_KEY` or backend key paths.
3. **Delete Old Key**: specific wait period (e.g., 24 hours) to verify no service disruption before deleting the old key.

## 3. Service Account Keys (Google Vision, Firebase)

### Frequency
- Every 90 days (standard recommendation).

### Procedure
1. Generate new JSON key file in Google Cloud Console.
2. Upload new key file to the server.
3. Update `GOOGLE_VISION_KEY_PATH` to point to the new file.
4. Restart backend.

## 4. Database Credentials

### Frequency
- Every 6 months.

### Procedure
1. Create a new database user/password in Supabase.
2. Update `SUPABASE_KEY` or `DATABASE_URL`.
3. Verify connection.
4. Revoke old credentials.
