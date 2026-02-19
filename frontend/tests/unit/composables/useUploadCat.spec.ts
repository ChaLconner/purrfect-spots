
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useUploadCat } from '@/composables/useUploadCat';
import * as api from '@/utils/api';
import * as imageUtils from '@/utils/imageUtils';
// env import removed

// Mock dependencies
vi.mock('@/utils/api', () => ({
  uploadFile: vi.fn(),
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    type: string;
    constructor(type: string, message: string) {
      super(message);
      this.type = type;
    }
  },
  ApiErrorTypes: {
    NETWORK_ERROR: 'NETWORK_ERROR',
    AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
  },
}));

vi.mock('@/utils/imageUtils', () => ({
  optimizeImage: vi.fn(),
  validateImageFile: vi.fn(),
  getImageDimensions: vi.fn(),
}));

vi.mock('@/utils/env', () => ({
  isDev: vi.fn().mockReturnValue(false), // Default to false to avoid console logs in tests
  getEnvVar: vi.fn().mockReturnValue('1080'),
}));

describe('useUploadCat', () => {
  let mockFile: File;
  let mockLocationData: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    mockLocationData = {
      lat: '123.456',
      lng: '78.90',
      location_name: 'Test Spot',
    };
  });

  it('should initialize with default state', () => {
    const { isUploading, error, uploadProgress } = useUploadCat();
    expect(isUploading.value).toBe(false);
    expect(error.value).toBe(null);
    expect(uploadProgress.value).toBe(0);
  });

  it('should fail validation if file is invalid', async () => {
    vi.spyOn(imageUtils, 'validateImageFile').mockReturnValue({ valid: false, error: 'Invalid file' });
    
    const { uploadCatPhoto, error } = useUploadCat();
    const result = await uploadCatPhoto(mockFile, mockLocationData);

    expect(result).toBeNull();
    expect(error.value).toBe('Invalid file');
    expect(imageUtils.validateImageFile).toHaveBeenCalledWith(mockFile);
  });

  it('should successfully upload a valid file', async () => {
    vi.spyOn(imageUtils, 'validateImageFile').mockReturnValue({ valid: true });
    vi.spyOn(imageUtils, 'getImageDimensions').mockResolvedValue({ width: 100, height: 100 });
    vi.spyOn(imageUtils, 'optimizeImage').mockResolvedValue(mockFile);
    vi.spyOn(api, 'uploadFile').mockResolvedValue({ id: '123', url: 'http://test.com/img.jpg' });

    const { uploadCatPhoto, isUploading, error } = useUploadCat();
    
    // Check loading state during upload
    const uploadPromise = uploadCatPhoto(mockFile, mockLocationData);
    expect(isUploading.value).toBe(true);
    
    const result = await uploadPromise;

    expect(isUploading.value).toBe(false);
    expect(error.value).toBeNull();
    expect(result).toEqual({ id: '123', url: 'http://test.com/img.jpg' });
    expect(api.uploadFile).toHaveBeenCalled();
  });

  it('should handle API errors', async () => {
    vi.spyOn(imageUtils, 'validateImageFile').mockReturnValue({ valid: true });
    vi.spyOn(imageUtils, 'getImageDimensions').mockResolvedValue({ width: 100, height: 100 });
    vi.spyOn(imageUtils, 'optimizeImage').mockResolvedValue(mockFile);
    
    // Mock API error
    const mockError = new api.ApiError(api.ApiErrorTypes.SERVER_ERROR, 'Server error');
    vi.spyOn(api, 'uploadFile').mockRejectedValue(mockError);

    const { uploadCatPhoto, error } = useUploadCat();
    const result = await uploadCatPhoto(mockFile, mockLocationData);

    expect(result).toBeNull();
    expect(error.value).toBe('Server error. Please try again later');
  });

  it('should update progress', async () => {
    vi.spyOn(imageUtils, 'validateImageFile').mockReturnValue({ valid: true });
    vi.spyOn(imageUtils, 'getImageDimensions').mockResolvedValue({ width: 100, height: 100 });
    vi.spyOn(imageUtils, 'optimizeImage').mockResolvedValue(mockFile);
    
    vi.spyOn(api, 'uploadFile').mockImplementation(async (_url, _file, _data, onProgress) => {
      if (onProgress) {
        onProgress({ 
          lengthComputable: true, 
          loaded: 50, 
          total: 100, 
          bytes: 50,
          rate: 100,
          estimated: 0,
          upload: true 
        } as any);
      }
      return { success: true };
    });

    const { uploadCatPhoto, uploadProgress } = useUploadCat();
    await uploadCatPhoto(mockFile, mockLocationData);

    expect(uploadProgress.value).toBe(50);
  });

  it('should reset state', () => {
    const { isUploading, error, uploadProgress, resetState } = useUploadCat();
    
    isUploading.value = true;
    error.value = 'Some error';
    uploadProgress.value = 50;

    resetState();

    expect(isUploading.value).toBe(false);
    expect(error.value).toBe(null);
    expect(uploadProgress.value).toBe(0);
  });

  it('should fetch quota status', async () => {
    const mockQuota = { used: 1, limit: 5, remaining: 4, is_pro: false };
    // @ts-ignore
    vi.spyOn(api.api, 'get').mockResolvedValue(mockQuota);

    const { getUploadQuota } = useUploadCat();
    const result = await getUploadQuota();

    expect(api.api.get).toHaveBeenCalledWith('/api/v1/upload/quota');
    expect(result).toEqual(mockQuota);
  });
});
