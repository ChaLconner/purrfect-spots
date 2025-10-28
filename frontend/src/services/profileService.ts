import type { User } from '../types/auth';
import { api, ApiError, ApiErrorTypes } from '../utils/api';

export interface ProfileUpdateData {
  name?: string;
  bio?: string;
  picture?: string;
}

export class ProfileService {
  // Get current user profile
  static async getProfile(): Promise<User> {
    try {
      return await api.get<User>('/profile');
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
        // Clear expired tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('user');
        
        // Update auth store
        const { clearAuth } = await import('../store/auth');
        clearAuth();
        
        throw new Error('Authentication expired. Please log in again.');
      }
      throw error;
    }
  }

  // Update user profile
  static async updateProfile(data: ProfileUpdateData): Promise<User> {
    try {
      const result = await api.put<{user: User}>('/profile', data);
      return result.user;
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
        // Clear expired tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('user');
        
        // Update auth store
        const { clearAuth } = await import('../store/auth');
        clearAuth();
        
        throw new Error('Authentication expired. Please log in again.');
      }
      throw error;
    }
  }

  // Get user uploads
  static async getUserUploads(): Promise<any[]> {
    try {
      const result = await api.get<{uploads: any[]}>('/profile/uploads');
      return result.uploads || [];
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
        // Clear expired tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('user');
        
        // Update auth store
        const { clearAuth } = await import('../store/auth');
        clearAuth();
        
        throw new Error('Authentication expired. Please log in again.');
      }
      throw error;
    }
  }
}
