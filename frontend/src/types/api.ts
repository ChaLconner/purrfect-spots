/**
 * API Types
 * 
 * Centralized type definitions for API-related interfaces.
 */

// ========== Pagination Types ==========
export interface PaginationParams {
  limit?: number;
  offset?: number;
  page?: number;
}

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  page: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  images: T[];
  pagination: PaginationMeta;
}

// ========== Error Types ==========
export const ApiErrorTypes = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const;

export type ApiErrorType = typeof ApiErrorTypes[keyof typeof ApiErrorTypes];

// ========== Cat/Gallery Types ==========
/**
 * Cat Location - matches backend schemas/location.py
 * This is the single source of truth for CatLocation type.
 */
export interface CatLocation {
  id: string;
  user_id?: string;
  location_name: string | null;  // nullable in backend
  description: string | null;     // nullable in backend
  latitude: number;
  longitude: number;
  image_url: string;
  tags: string[];                 // always present, default []
  uploaded_at?: string;
  created_at?: string;
}

export interface GalleryImage extends CatLocation {
  filename?: string;
}

// ========== Upload Types ==========
export interface UploadRequest {
  file: File;
  lat: number;
  lng: number;
  location_name: string;
  description?: string;
  tags?: string[];
}

export interface UploadResponse {
  success: boolean;
  message: string;
  photo: {
    id: string;
    location_name: string;
    location: {
      latitude: number;
      longitude: number;
    };
    image_url: string;
    uploaded_at: string;
  };
  cat_detection: CatDetectionResult;
  uploaded_by: string;
}

// ========== Cat Detection Types ==========
export interface CatDetectionResult {
  has_cats: boolean;
  cat_count: number;
  confidence: number;
  labels?: string[];
  cat_labels?: Array<{
    description: string;
    score: number;
  }>;
  cat_objects?: Array<{
    name: string;
    score: number;
    bounding_box?: {
      normalized_vertices: Array<{ x: number; y: number }>;
    } | null;
  }>;
  image_quality?: string;
  reasoning?: string;
}

// ========== Search Types ==========
export interface SearchParams {
  query?: string;
  tags?: string[];
  limit?: number;
}

// ========== Profile Types ==========
export interface ProfileUpdateRequest {
  name?: string;
  bio?: string;
  picture?: string;
}

export interface ProfileResponse {
  id: string;
  email: string;
  name: string;
  picture?: string;
  bio?: string;
  created_at: string;
  photos_count?: number;
}
