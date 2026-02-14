/**
 * Centralized error messages for the application.
 */
export const AuthErrorMessages = {
  SESSION_EXPIRED: 'Authentication expired. Please try signing in again.',
  REDIRECT_URI_MISMATCH: 'Redirect URI mismatch. Please check your OAuth configuration.',
  GOOGLE_LOGIN_FAILED: 'Google login failed. Please try again.',
  UNKNOWN_ERROR: 'An unknown error occurred.',
} as const;
