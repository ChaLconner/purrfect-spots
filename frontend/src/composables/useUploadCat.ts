import { ref } from 'vue';
import { uploadFile, ApiError, ApiErrorTypes } from '../utils/api';
import { optimizeImage, validateImageFile, getImageDimensions } from '../utils/imageUtils';
import { isDev, getEnvVar } from '../utils/env';

export function useUploadCat() {
  const isUploading = ref(false);
  const error = ref<string | null>(null);
  const uploadProgress = ref(0);

  // Upload cat photo with optimization
  const uploadCatPhoto = async (
    file: File,
    locationData: {
      lat: string;
      lng: string;
      location_name: string;
      description?: string;
      tags?: string[];
    },
    catDetectionData?: any
  ) => {
    try {
      isUploading.value = true;
      error.value = null;
      uploadProgress.value = 0;

      // Validate image file
      const validation = validateImageFile(file);
      if (!validation.valid) {
        error.value = validation.error;
        return null;
      }

      // Get image dimensions
      const dimensions = await getImageDimensions(file);
      if (isDev()) {
        console.log('Original image dimensions:', dimensions);
      }

      // Optimize image before upload
      const optimizedFile = await optimizeImage(file, {
        maxWidth: parseInt(getEnvVar('VITE_MAX_IMAGE_WIDTH') || '1920'),
        maxHeight: parseInt(getEnvVar('VITE_MAX_IMAGE_HEIGHT') || '1080'),
        quality: parseInt(getEnvVar('VITE_IMAGE_QUALITY') || '85'),
        format: 'jpeg',
      });

      console.log('Optimized file size:', (optimizedFile.size / 1024 / 1024).toFixed(2), 'MB');

      // Prepare additional data
      const additionalData = {
        ...locationData,
        tags: locationData.tags ? JSON.stringify(locationData.tags) : undefined,
        cat_detection_data: catDetectionData ? JSON.stringify(catDetectionData) : undefined,
        original_filename: file.name,
        original_size: file.size,
        optimized_size: optimizedFile.size,
        original_dimensions: JSON.stringify(dimensions),
      };

      // Upload file with progress tracking
      const result = await uploadFile('/api/v1/upload/cat', optimizedFile, additionalData, (progressEvent) => {
        if (progressEvent.lengthComputable) {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      });

      return result;
    } catch (err) {
      if (isDev()) {
        console.error('Upload error:', err);
      }
      
      // Handle API errors specifically
      if (err instanceof ApiError) {
        let errorMessage = '';
        
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
        error.value = err.message || 'An error occurred during image upload';
      }
      
      return null;
    } finally {
      isUploading.value = false;
    }
  };

  // Reset state
  const resetState = () => {
    isUploading.value = false;
    error.value = null;
    uploadProgress.value = 0;
  };

  return {
    isUploading,
    error,
    uploadProgress,
    uploadCatPhoto,
    resetState,
  };
}