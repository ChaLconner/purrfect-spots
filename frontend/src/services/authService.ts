import type { User } from '../types/auth';
import { getAuthHeader } from '../store/auth';

const API_BASE_URL = 'http://localhost:8000';

export class AuthService {
  // Get current user information
  static async getCurrentUser(): Promise<User> {
    const authHeader = getAuthHeader();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to get user information');
    }

    return response.json();
  }

  // Login user
  static async login(email: string, password: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    return response.json();
  }

  // Signup user
  static async signup(email: string, password: string, name: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, name }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    return response.json();
  }

  // Logout user
  static async logout(): Promise<void> {
    const authHeader = getAuthHeader();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      throw new Error('Logout failed');
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
  static async googleCodeExchange(code: string, codeVerifier: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/google/exchange`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code,
        code_verifier: codeVerifier,
        redirect_uri: `${window.location.origin}/auth/callback`
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Google OAuth failed');
    }

    return response.json();
  }

  // Sync user data with backend (สำหรับ Supabase Auth integration)
  static async syncUser(): Promise<any> {
    const authHeader = getAuthHeader();
    
    if (!authHeader.Authorization) {
      throw new Error('No authentication token available');
    }

    const response = await fetch(`${API_BASE_URL}/auth/sync-user`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'User sync failed');
    }

    return response.json();
  }
}
