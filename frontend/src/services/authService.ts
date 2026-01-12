import type { User, LoginResponse } from '../types/auth';
import { apiV1, ApiError, ApiErrorTypes } from '../utils/api';
import { isDev } from '../utils/env';
import { isBrowserExtensionError, handleBrowserExtensionError } from '../utils/browserExtensionHandler';

export class AuthService {
  // Get current user information
  static async getCurrentUser(): Promise<User> {
    try {
      return await apiV1.get<User>('/auth/me');
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        ApiErrorTypes.UNKNOWN_ERROR,
        'Failed to get user information'
      );
    }
  }

  // Login user
  static async login(email: string, password: string): Promise<LoginResponse> {
    try {
      return await apiV1.post('/auth/login', { email, password });
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Handle browser extension errors
      if (isBrowserExtensionError(error)) {
        try {
          return await handleBrowserExtensionError(
            error,
            () => apiV1.post('/auth/login', { email, password })
          );
        } catch (retryError: any) {
          throw new ApiError(
            ApiErrorTypes.UNKNOWN_ERROR,
            retryError.message || 'Login failed'
          );
        }
      }
      
      throw error;
    }
  }

  // Signup user
  static async signup(email: string, password: string, name: string): Promise<LoginResponse> {
    try {
      return await apiV1.post('/auth/register', { email, password, name });
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Handle browser extension errors
      if (isBrowserExtensionError(error)) {
        try {
          return await handleBrowserExtensionError(
            error,
            () => apiV1.post('/auth/register', { email, password, name })
          );
        } catch (retryError: any) {
          throw new ApiError(
            ApiErrorTypes.UNKNOWN_ERROR,
            retryError.message || 'Registration failed'
          );
        }
      }
      
      throw error;
    }
  }

  // Logout user
  static async logout(): Promise<void> {
    try {
      await apiV1.post('/auth/logout');
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        ApiErrorTypes.UNKNOWN_ERROR,
        'Logout failed'
      );
    }
  }

  // Verify if user is authenticated by checking token validity
  static async verifyToken(): Promise<boolean> {
    try {
      await this.getCurrentUser();
      return true;
    } catch {
      return false;
    }
  }

  // Google OAuth code exchange
  static async googleCodeExchange(code: string, codeVerifier: string): Promise<LoginResponse> {
    try {
      const redirectUri = `${window.location.origin}/auth/callback`;
      
      // Log request for debugging
      if (isDev()) {
        console.log('Google OAuth exchange request:', {
          code: code ? 'present' : 'missing',
          code_verifier: codeVerifier ? 'present' : 'missing',
          redirect_uri: redirectUri
        });
      }
      
      return await apiV1.post('/auth/google/exchange', {
        code,
        code_verifier: codeVerifier,
        redirect_uri: redirectUri
      });
      
    } catch (error) {
      if (error instanceof ApiError) {
        // Provide more detailed error messages for specific cases
        if (error.message.includes('invalid_grant')) {
          throw new ApiError(
            error.type,
            'Authentication expired. Please try signing in again.',
            error.statusCode
          );
        } else if (error.message.includes('redirect_uri')) {
          throw new ApiError(
            error.type,
            'Redirect URI mismatch. Please check your OAuth configuration.',
            error.statusCode
          );
        }
        throw error;
      }
      
      // Handle browser extension errors
      if (isBrowserExtensionError(error)) {
        try {
          const redirectUri = `${window.location.origin}/auth/callback`;
          return await handleBrowserExtensionError(
            error,
            () => apiV1.post('/auth/google/exchange', {
              code,
              code_verifier: codeVerifier,
              redirect_uri: redirectUri
            })
          );
        } catch (retryError: any) {
          throw new ApiError(
            ApiErrorTypes.UNKNOWN_ERROR,
            retryError.message || 'Google OAuth failed'
          );
        }
      }
      
      throw error;
    }
  }

  // Sync user data with backend (for Supabase Auth integration)
  static async syncUser(): Promise<any> {
    try {
      return await apiV1.post('/auth/sync-user');
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        ApiErrorTypes.UNKNOWN_ERROR,
        'User sync failed'
      );
    }
  }
}