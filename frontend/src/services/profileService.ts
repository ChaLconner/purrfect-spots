import type { User } from '../types/auth';
import { getAuthHeader } from '../store/auth';
import { createApiUrl } from '../config/api';

export interface ProfileUpdateData {
  name?: string;
  bio?: string;
  picture?: string;
}

export class ProfileService {
  // Get current user profile
  static async getProfile(): Promise<User> {
    const authHeader = getAuthHeader();
    
    // Check if token exists before making request
    if (!authHeader.Authorization) {
      throw new Error('No authentication token found. Please log in again.');
    }
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(createApiUrl('/api/profile'), {
      method: 'GET',
      headers,
    });

    if (response.status === 401) {
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

    if (!response.ok) {
      throw new Error('Failed to get profile');
    }

    return response.json();
  }

  // Update user profile
  static async updateProfile(data: ProfileUpdateData): Promise<User> {
    const authHeader = getAuthHeader();
    
    // Check if token exists before making request
    if (!authHeader.Authorization) {
      throw new Error('No authentication token found. Please log in again.');
    }
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(createApiUrl('/api/profile'), {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });

    if (response.status === 401) {
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

    if (!response.ok) {
      throw new Error('Failed to update profile');
    }

    const result = await response.json();
    return result.user;
  }

  // Get user uploads
  static async getUserUploads(): Promise<any[]> {
    const authHeader = getAuthHeader();
    
    // Check if token exists before making request
    if (!authHeader.Authorization) {
      throw new Error('No authentication token found. Please log in again.');
    }
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(createApiUrl('/api/profile/uploads'), {
      method: 'GET',
      headers,
    });

    if (response.status === 401) {
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

    if (!response.ok) {
      throw new Error('Failed to get user uploads');
    }

    const result = await response.json();
    return result.uploads || [];
  }
}
