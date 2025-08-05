import type { User } from '../types/auth';
import { getAuthHeader } from '../store/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
    try {
      console.log('🔄 Attempting to login user:', email);
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      console.log('📡 Login response status:', response.status);

      if (!response.ok) {
        const error = await response.json();
        console.error('❌ Login failed:', error);
        throw new Error(error.detail || 'เข้าสู่ระบบล้มเหลว');
      }

      const result = await response.json();
      console.log('✅ Login successful');
      return result;
      
    } catch (error: any) {
      console.error('🔥 Login error:', error);
      
      // Handle browser extension errors
      if (error.message && error.message.includes('message channel closed')) {
        console.warn('🔧 Browser extension conflict detected in login, retrying...');
        
        try {
          // Retry the request
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
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
          console.error('🔥 Login retry failed:', retryError);
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
      console.log('🔄 Attempting to register user:', email);
      
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      });

      console.log('📡 Registration response status:', response.status);

      if (!response.ok) {
        const error = await response.json();
        console.error('❌ Registration failed:', error);
        throw new Error(error.detail || 'สมัครสมาชิกล้มเหลว');
      }

      const result = await response.json();
      console.log('✅ Registration successful');
      return result;
      
    } catch (error: any) {
      console.error('🔥 Signup error:', error);
      
      // Handle browser extension errors
      if (error.message && error.message.includes('message channel closed')) {
        console.warn('🔧 Browser extension conflict detected, retrying...');
        
        try {
          // Retry the request
          const response = await fetch(`${API_BASE_URL}/auth/register`, {
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
          console.error('🔥 Retry failed:', retryError);
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
    try {
      console.log('🔄 Exchanging Google OAuth code...');
      
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

      console.log('📡 OAuth exchange response status:', response.status);

      if (!response.ok) {
        const error = await response.json();
        console.error('❌ OAuth exchange failed:', error);
        throw new Error(error.detail || 'Google OAuth failed');
      }

      const result = await response.json();
      console.log('✅ OAuth exchange successful');
      return result;
      
    } catch (error: any) {
      console.error('🔥 OAuth exchange error:', error);
      
      // Handle browser extension errors
      if (error.message && error.message.includes('message channel closed')) {
        console.warn('🔧 Browser extension conflict detected in OAuth, retrying...');
        
        try {
          // Retry the request
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
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Google OAuth failed');
          }

          return response.json();
        } catch (retryError: any) {
          console.error('🔥 OAuth retry failed:', retryError);
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
