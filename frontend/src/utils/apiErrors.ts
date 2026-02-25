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
