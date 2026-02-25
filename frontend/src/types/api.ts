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
// Single source of truth lives in utils/apiErrors.ts to avoid circular dependency
export { ApiError, ApiErrorTypes, type ApiErrorType } from '../utils/apiErrors';

// ========== Cat/Gallery Types ==========
/**
 * Cat Location - matches backend schemas/location.py
 * This is the single source of truth for CatLocation type.
 */
export interface CatLocation {
  id: string;
  user_id?: string;
  location_name: string | null; // nullable in backend
  description: string | null; // nullable in backend
  latitude: number;
  longitude: number;
  image_url: string;
  tags: string[]; // always present, default []
  uploaded_at: string;
  likes_count: number;
  comments_count: number;
  liked: boolean; // Track if current user liked this photo
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
export interface CatDetected {
  description: string;
  breed_guess: string;
  position: string;
  size: string;
}

export interface CatDetectionResult {
  has_cats: boolean;
  cat_count: number;
  confidence: number;
  cats_detected: CatDetected[];
  image_quality?: string;
  suitable_for_cat_spot: boolean;
  reasoning?: string;
  note?: string;
  requires_server_verification?: boolean;
  client_error?: boolean;
}

export interface SpotAnalysisResult {
  suitability_score: number;
  safety_factors: {
    safe_from_traffic: boolean;
    has_shelter: boolean;
    food_source_nearby: boolean;
    water_access: boolean;
    escape_routes: boolean;
  };
  environment_type: string;
  pros: string[];
  cons: string[];
  recommendations: string[];
  best_times: string[];
}

export interface CombinedAnalysisResult {
  cat_detection: CatDetectionResult;
  spot_analysis: SpotAnalysisResult;
  overall_recommendation: {
    suitable_for_cat_spot: boolean;
    confidence: number;
    summary: string;
  };
  metadata: {
    filename: string;
    file_size: number;
    analyzed_by: string;
  };
}

// ========== Search Types ==========
export interface SearchParams {
  query?: string;
  tags?: string[];
  limit?: number;
  offset?: number;
  page?: number;
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
