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
import { apiV1 } from '../utils/api';

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
    return await apiV1.get<User>('/profile');
  }

  // Update user profile
  static async updateProfile(data: ProfileUpdateData): Promise<User> {
    const result = await apiV1.put<{ user: User }>('/profile', data);
    return result.user;
  }

  // Get user uploads
  static async getUserUploads(): Promise<CatLocation[]> {
    const result = await apiV1.get<{ uploads: CatLocation[] }>('/profile/uploads');
    return result.uploads || [];
  }

  // Upload profile picture
  static async uploadProfilePicture(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);

    const result = await apiV1.post<{ picture: string }>('/profile/picture', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return result.picture;
  }

  // Change password
  static async changePassword(data: ChangePasswordData): Promise<void> {
    await apiV1.put('/profile/password', data);
  }

  // Update photo details
  static async updatePhoto(
    photoId: string,
    data: { location_name?: string; description?: string }
  ): Promise<void> {
    await apiV1.put(`/profile/uploads/${photoId}`, data);
  }

  // Delete uploaded photo
  static async deletePhoto(photoId: string): Promise<void> {
    await apiV1.delete(`/profile/uploads/${photoId}`);
  }
}
