import type { User } from '../types/auth';
import { getAuthHeader } from '../store/auth';

const API_BASE_URL = 'http://localhost:8000';

export interface ProfileUpdateData {
  name?: string;
  bio?: string;
  picture?: string;
}

export class ProfileService {
  // Get current user profile
  static async getProfile(): Promise<User> {
    const authHeader = getAuthHeader();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(`${API_BASE_URL}/api/profile`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to get profile');
    }

    return response.json();
  }

  // Update user profile
  static async updateProfile(data: ProfileUpdateData): Promise<User> {
    const authHeader = getAuthHeader();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(`${API_BASE_URL}/api/profile`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to update profile');
    }

    const result = await response.json();
    return result.user;
  }

  // Get user uploads
  static async getUserUploads(): Promise<any[]> {
    const authHeader = getAuthHeader();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeader,
    };

    const response = await fetch(`${API_BASE_URL}/api/profile/uploads`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to get user uploads');
    }

    const result = await response.json();
    return result.uploads;
  }
}
