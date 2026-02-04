/**
 * Types Index
 *
 * Central export for all type definitions.
 * Import from '@/types' for cleaner imports.
 */

// Auth Types
export type { User, LoginResponse, AuthState } from './auth';

// API Types
export type {
  PaginationParams,
  PaginationMeta,
  PaginatedResponse,
  CatLocation,
  GalleryImage,
  UploadRequest,
  UploadResponse,
  CatDetectionResult,
  SearchParams,
  ProfileUpdateRequest,
  ProfileResponse,
  ApiErrorType,
} from './api';

export { ApiErrorTypes } from './api';

// Toast Types
export type { ToastType } from './toast';
