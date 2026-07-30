import { ref, type Ref } from 'vue';
import { validateImageFile } from '../utils/imageUtils';
import { api, ApiError, ApiErrorTypes, uploadFile } from '../utils/api';
import type { UploadResponse } from '../types/upload';

type UploadPhase = 'idle' | 'uploading' | 'processing';

export function useUploadCat(): {
  isUploading: Ref<boolean>;
  error: Ref<string | null>;
  uploadProgress: Ref<number>;
  uploadPhase: Ref<UploadPhase>;
  uploadCatPhoto: (
    file: File,
    locationData: {
      lat: string;
      lng: string;
      location_name: string;
      description?: string;
      tags?: string[];
      location_blurred?: boolean;
    },
    catDetectionData?: Record<string, unknown>
  ) => Promise<UploadResponse | null>;
  getUploadQuota: () => Promise<{
    used: number;
    limit: number;
    remaining: number;
    is_pro: boolean;
    resets_at: string | null;
    reset_type: string | null;
  } | null>;
  resetState: () => void;
} {
  const isUploading = ref(false);
  const error = ref<string | null>(null);
  const uploadProgress = ref(0);
  const uploadPhase = ref<UploadPhase>('idle');

  // Get current quota status
  const getUploadQuota = async (): Promise<{
    used: number;
    limit: number;
    remaining: number;
    is_pro: boolean;
    resets_at: string | null;
    reset_type: string | null;
  } | null> => {
    try {
      const response = await api.get<{
        used: number;
        limit: number;
        remaining: number;
        is_pro: boolean;
        resets_at: string | null;
        reset_type: string | null;
      }>('/api/v1/upload/quota');
      return response;
    } catch (err) {
      if (!(err instanceof ApiError && err.type === ApiErrorTypes.AUTHENTICATION_ERROR)) {
        console.error('Failed to fetch quota:', err);
      }
      return null;
    }
  };

  // Upload cat photo with optimization
  const uploadCatPhoto = async (
    file: File,
    locationData: {
      lat: string;
      lng: string;
      location_name: string;
      description?: string;
      tags?: string[];
      location_blurred?: boolean;
    },
    catDetectionData?: Record<string, unknown>
  ): Promise<UploadResponse | null> => {
    isUploading.value = true;
    error.value = null;
    uploadProgress.value = 0;
    uploadPhase.value = 'uploading';

    try {
      // Validate image file
      const validation = validateImageFile(file);
      if (!validation.valid) {
        error.value = validation.error || null;
        return null;
      }

      // Prepare additional data
      const additionalData = {
        ...locationData,
        tags: locationData.tags ? JSON.stringify(locationData.tags) : undefined,
        verification_token:
          typeof catDetectionData?.verification_token === 'string'
            ? catDetectionData.verification_token
            : undefined,
      };

      // Upload file with progress tracking
      const idempotencyKey =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const result = await uploadFile<UploadResponse>(
        '/api/v1/upload/cat',
        file,
        additionalData,
        (progressEvent) => {
          if (progressEvent.lengthComputable && progressEvent.total) {
            uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            if (uploadProgress.value >= 100) uploadPhase.value = 'processing';
          }
        },
        { idempotencyKey, retryConfig: { maxRetries: 0 } }
      );

      return result;
    } catch (err) {
      // Error logged to state, console log suppressed

      // Handle API errors specifically
      if (err instanceof ApiError) {
        let errorMessage: string;

        switch (err.type) {
          case ApiErrorTypes.NETWORK_ERROR:
            errorMessage = 'Cannot connect to server. Please check your internet connection';
            break;
          case ApiErrorTypes.AUTHENTICATION_ERROR:
            errorMessage = 'Login session expired. Please log in again';
            break;
          case ApiErrorTypes.VALIDATION_ERROR:
            errorMessage = err.message;
            break;
          case ApiErrorTypes.SERVER_ERROR:
            errorMessage = 'Server error. Please try again later';
            break;
          default:
            errorMessage = err.message || 'An unknown error occurred';
        }

        error.value = errorMessage;
      } else {
        error.value = (err as Error).message || 'An error occurred during image upload';
      }

      return null;
    } finally {
      isUploading.value = false;
      uploadPhase.value = 'idle';
    }
  };

  // Reset state
  const resetState = (): void => {
    isUploading.value = false;
    error.value = null;
    uploadProgress.value = 0;
    uploadPhase.value = 'idle';
  };

  return {
    isUploading,
    error,
    uploadProgress,
    uploadPhase,
    uploadCatPhoto,
    getUploadQuota,
    resetState,
  };
}
