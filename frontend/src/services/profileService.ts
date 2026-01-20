/**
 * Profile Service
 * 
 * Handles all profile-related API operations including:
 * - Fetching user profile data
 * - Updating profile information
 * - Managing profile pictures
 * - Password management
 * 
 * @module ProfileService
 */
import type { User } from '../types/auth';
import type { CatLocation } from '../types/api';
import { apiV1, ApiError } from '../utils/api';

/**
 * Data structure for profile updates
 */
export interface ProfileUpdateData {
  /** User's display name */
  name?: string;
  /** User's biography/about text */
  bio?: string;
  /** URL to user's profile picture */
  picture?: string;
}

/**
 * Data structure for password change requests
 */
export interface ChangePasswordData {
  /** User's current password for verification */
  current_password: string;
  /** New password to set */
  new_password: string;
}

/**
 * Service class for managing user profile operations.
 * All methods are static and handle authentication errors automatically.
 * 
 * @example
 * ```typescript
 * // Get current user profile
 * const user = await ProfileService.getProfile();
 * 
 * // Update profile
 * const updated = await ProfileService.updateProfile({ name: 'New Name' });
 * 
 * // Upload profile picture
 * const pictureUrl = await ProfileService.uploadProfilePicture(file);
 * ```
 */
export class ProfileService {
  /**
   * Fetches the current authenticated user's profile.
   * 
   * @returns Promise resolving to the User object
   * @throws Error when authentication is expired or invalid
   * 
   * @example
   * ```typescript
   * try {
   *   const user = await ProfileService.getProfile();
   *   console.log(user.name);
   * } catch (error) {
   *   // Handle authentication error
   * }
   * ```
   */
  static async getProfile(): Promise<User> {
    try {
      return await apiV1.get<User>('/profile');
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
        // Clear expired tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('user');
        
        // Update auth store
        const { useAuthStore } = await import('../store/authStore');
        const auth = useAuthStore();
        auth.clearAuth();
        
        throw new Error('Authentication expired. Please log in again.');
      }
      throw error;
    }
  }

  // Update user profile
  static async updateProfile(data: ProfileUpdateData): Promise<User> {
    try {
      const result = await apiV1.put<{user: User}>('/profile', data);
      return result.user;
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
        // Clear expired tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('user');
        
        // Update auth store
        const { useAuthStore } = await import('../store/authStore');
        const auth = useAuthStore();
        auth.clearAuth();
        
        throw new Error('Authentication expired. Please log in again.');
      }
      throw error;
    }
  }

  // Get user uploads
  static async getUserUploads(): Promise<CatLocation[]> {
    try {
      const result = await apiV1.get<{uploads: CatLocation[]}>('/profile/uploads');
      return result.uploads || [];
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
        // Clear expired tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('user');
        
        // Update auth store
        const { useAuthStore } = await import('../store/authStore');
        const auth = useAuthStore();
        auth.clearAuth();
        
        throw new Error('Authentication expired. Please log in again.');
      }
      throw error;
  // Join uploads
    }
  }

  // Upload profile picture
  static async uploadProfilePicture(file: File): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const result = await apiV1.post<{picture: string}>('/profile/picture', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return result.picture;
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
         // Token handling...
         throw new Error('Authentication expired');
      }
      throw error;
    }
  }

  // Change password
  static async changePassword(data: ChangePasswordData): Promise<void> {
    try {
      await apiV1.put('/profile/password', data);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.statusCode === 401) {
          throw new Error('Authentication expired');
        }
        // Pass through backend validation errors (e.g. incorrect password)
        throw new Error(error.message || 'Failed to change password');
      }
      throw error;
    }
  }
}
