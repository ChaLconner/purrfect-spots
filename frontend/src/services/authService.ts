import type { User, LoginResponse } from '../types/auth';
import { apiV1, ApiError } from '../utils/api';
import { isDev } from '../utils/env';

export class AuthService {
  // Get current user information
  static async getCurrentUser(): Promise<User> {
    return await apiV1.get<User>('/auth/me');
  }

  // Login user
  static async login(email: string, password: string): Promise<LoginResponse> {
    return await apiV1.post('/auth/login', { email, password });
  }

  // Signup user
  static async signup(email: string, password: string, name: string): Promise<LoginResponse> {
    return await apiV1.post('/auth/register', { email, password, name });
  }

  // Verify OTP code
  static async verifyOtp(email: string, otp: string): Promise<LoginResponse> {
    return await apiV1.post('/auth/verify-otp', { email, otp });
  }

  // Resend OTP code
  static async resendOtp(email: string): Promise<{ message: string; expires_at: string }> {
    return await apiV1.post('/auth/resend-otp', { email });
  }

  // Logout user
  static async logout(): Promise<void> {
    await apiV1.post('/auth/logout');
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
      const redirectUri = `${globalThis.location.origin}/auth/callback`;

      // Log request for debugging
      if (isDev()) {
        // eslint-disable-next-line no-console
        console.log('Google OAuth exchange request:', {
          code: code ? 'present' : 'missing',
          code_verifier: codeVerifier ? 'present' : 'missing',
          redirect_uri: redirectUri,
        });
      }

      return await apiV1.post('/auth/google/exchange', {
        code,
        code_verifier: codeVerifier,
        redirect_uri: redirectUri,
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

      // Browser extension errors are handled by API interceptor
      throw error;
    }
  }

  // Sync user data with backend (for Supabase Auth integration)
  static async syncUser(): Promise<User> {
    return await apiV1.post('/auth/sync-user');
  }
}
