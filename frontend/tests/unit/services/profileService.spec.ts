import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProfileService } from '@/services/profileService';
import { apiV1 } from '@/utils/api';

vi.mock('@/utils/api', () => ({
  apiV1: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('ProfileService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getProfile calls correct endpoint', async () => {
    const mockUser = { id: '123', name: 'Test User' };
    vi.mocked(apiV1.get).mockResolvedValue(mockUser);

    const result = await ProfileService.getProfile();

    expect(apiV1.get).toHaveBeenCalledWith('/profile');
    expect(result).toEqual(mockUser);
  });

  it('updateProfile calls correct endpoint and returns nested user', async () => {
    const mockUser = { id: '123', name: 'New Name' };
    vi.mocked(apiV1.put).mockResolvedValue({ user: mockUser });

    const result = await ProfileService.updateProfile({ name: 'New Name' });

    expect(apiV1.put).toHaveBeenCalledWith('/profile', { name: 'New Name' });
    expect(result).toEqual(mockUser);
  });

  it('getUserUploads returns uploads array or empty', async () => {
    const mockUploads = [{ id: 'img1' }];
    vi.mocked(apiV1.get).mockResolvedValue({ uploads: mockUploads });

    const result = await ProfileService.getUserUploads();

    expect(apiV1.get).toHaveBeenCalledWith('/profile/uploads');
    expect(result).toEqual(mockUploads);

    // Test empty fallback
    vi.mocked(apiV1.get).mockResolvedValue({});
    expect(await ProfileService.getUserUploads()).toEqual([]);
  });

  it('uploadProfilePicture sends FormData', async () => {
    vi.mocked(apiV1.post).mockResolvedValue({ picture: 'url-to-pic' });
    const file = new File([''], 'avatar.jpg', { type: 'image/jpeg' });

    const result = await ProfileService.uploadProfilePicture(file);

    expect(apiV1.post).toHaveBeenCalledWith(
      '/profile/picture',
      expect.any(FormData),
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    );
    expect(result).toBe('url-to-pic');
  });

  it('changePassword calls correct endpoint', async () => {
    await ProfileService.changePassword({ current_password: 'old', new_password: 'new' });
    expect(apiV1.put).toHaveBeenCalledWith('/profile/password', {
      current_password: 'old',
      new_password: 'new'
    });
  });

  it('updatePhoto calls correct endpoint', async () => {
    await ProfileService.updatePhoto('photo123', { description: 'Updated' });
    expect(apiV1.put).toHaveBeenCalledWith('/profile/uploads/photo123', {
      description: 'Updated'
    });
  });

  it('deletePhoto calls correct endpoint', async () => {
    await ProfileService.deletePhoto('photo123');
    expect(apiV1.delete).toHaveBeenCalledWith('/profile/uploads/photo123');
  });

  it('getPublicProfile calls correct endpoint', async () => {
    const mockUser = { id: 'user-456', name: 'Public User' };
    vi.mocked(apiV1.get).mockResolvedValue(mockUser);

    const result = await ProfileService.getPublicProfile('user-456');

    expect(apiV1.get).toHaveBeenCalledWith('/profile/public/user-456');
    expect(result).toEqual(mockUser);
  });

  it('getPublicUserUploads returns uploads array', async () => {
    const mockUploads = [{ id: 'img1', location_name: 'Location 1' }];
    vi.mocked(apiV1.get).mockResolvedValue({ uploads: mockUploads });

    const result = await ProfileService.getPublicUserUploads('user-456');

    expect(apiV1.get).toHaveBeenCalledWith('/profile/public/user-456/uploads');
    expect(result).toEqual(mockUploads);
  });

  it('getPublicUserUploads returns empty array when no uploads', async () => {
    vi.mocked(apiV1.get).mockResolvedValue({});

    const result = await ProfileService.getPublicUserUploads('user-456');

    expect(result).toEqual([]);
  });
});
