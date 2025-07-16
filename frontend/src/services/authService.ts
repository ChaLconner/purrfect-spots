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
}
