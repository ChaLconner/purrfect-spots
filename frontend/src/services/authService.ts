import type { User } from '../types/auth';
import { getAuthHeader } from '../store/auth';
import { createApiUrl } from '../config/api';

export class AuthService {
  // Get current user information
  static async getCurrentUser(): Promise<User> {
    const authHeader = getAuthHeader();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(createApiUrl('/auth/me'), {
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
    try {
      const response = await fetch(createApiUrl('/auth/login'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'เข้าสู่ระบบล้มเหลว');
      }

      const result = await response.json();
      return result;
      
    } catch (error: any) {
      // Handle browser extension errors
      if (error.message && error.message.includes('message channel closed')) {
        try {
          // Retry the request
          const response = await fetch(createApiUrl('/auth/login'), {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'เข้าสู่ระบบล้มเหลว');
          }

          return response.json();
        } catch (retryError: any) {
          throw new Error(retryError.message || 'เข้าสู่ระบบล้มเหลว');
        }
      }
      
      // Handle network errors
      if (error.message === 'Failed to fetch') {
        throw new Error('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต');
      }
      
      throw error;
    }
  }

  // Signup user
  static async signup(email: string, password: string, name: string): Promise<any> {
    try {
      const response = await fetch(createApiUrl('/auth/register'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'สมัครสมาชิกล้มเหลว');
      }

      const result = await response.json();
      return result;
      
    } catch (error: any) {
      // Handle browser extension errors
      if (error.message && error.message.includes('message channel closed')) {
        try {
          // Retry the request
          const response = await fetch(createApiUrl('/auth/register'), {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password, name }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'สมัครสมาชิกล้มเหลว');
          }

          return response.json();
        } catch (retryError: any) {
          throw new Error(retryError.message || 'สมัครสมาชิกล้มเหลว');
        }
      }
      
      // Handle network errors
      if (error.message === 'Failed to fetch') {
        throw new Error('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต');
      }
      
      throw error;
    }
  }

  // Logout user
  static async logout(): Promise<void> {
    const authHeader = getAuthHeader();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(createApiUrl('/auth/logout'), {
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
    try {
      const response = await fetch(createApiUrl('/auth/google/exchange'), {
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

      const result = await response.json();
      return result;
      
    } catch (error: any) {
      // Handle browser extension errors
      if (error.message && error.message.includes('message channel closed')) {
        try {
          // Retry the request
          const response = await fetch(createApiUrl('/auth/google/exchange'), {
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
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Google OAuth failed');
          }

          return response.json();
        } catch (retryError: any) {
          throw new Error(retryError.message || 'Google OAuth failed');
        }
      }
      
      // Handle network errors
      if (error.message === 'Failed to fetch') {
        throw new Error('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต');
      }
      
      throw error;
    }
  }

  // Sync user data with backend (สำหรับ Supabase Auth integration)
  static async syncUser(): Promise<any> {
    const authHeader = getAuthHeader();
    
    if (!authHeader.Authorization) {
      throw new Error('No authentication token available');
    }

    const response = await fetch(createApiUrl('/auth/sync-user'), {
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
