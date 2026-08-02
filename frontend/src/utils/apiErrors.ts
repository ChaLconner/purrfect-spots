/**
 * API Error Types and Classes
 *
 * Moved to a dedicated file to break circular dependencies
 * and provide a clean source for error definitions.
 */

export const ApiErrorTypes = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

export type ApiErrorType = (typeof ApiErrorTypes)[keyof typeof ApiErrorTypes];

export class ApiError extends Error {
  type: ApiErrorType;
  statusCode?: number;
  originalError?: unknown;

  constructor(type: ApiErrorType, message: string, statusCode?: number, originalError?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.statusCode = statusCode;
    this.originalError = originalError;
  }
}

export const AuthErrorMessages = {
  SESSION_EXPIRED: 'Authentication expired. Please try signing in again.',
  REDIRECT_URI_MISMATCH: 'Redirect URI mismatch. Please check your OAuth configuration.',
  GOOGLE_LOGIN_FAILED: 'Google login failed. Please try again.',
  UNKNOWN_ERROR: 'An unknown error occurred.',
} as const;

export function formatApiErrorMessage(err: unknown, fallbackMessage = 'An unknown error occurred'): string {
  if (err instanceof ApiError) {
    switch (err.type) {
      case ApiErrorTypes.NETWORK_ERROR:
        return 'Cannot connect to server. Please check your internet connection';
      case ApiErrorTypes.AUTHENTICATION_ERROR:
        return 'Login session expired. Please log in again';
      case ApiErrorTypes.VALIDATION_ERROR:
        return err.message;
      case ApiErrorTypes.SERVER_ERROR:
        return 'Server error. Please try again later';
      default:
        return err.message || fallbackMessage;
    }
  }
  return (err as Error)?.message || fallbackMessage;
}
export function formatFormErrorMessage(
  err: unknown,
  fallbackMessage: string,
  statusCodeMessage: string
): string {
  const message = formatApiErrorMessage(err, fallbackMessage);
  return message.includes('status code') ? statusCodeMessage : message;
}
