
export interface CatDetectionResult {
  has_cats: boolean;
  cat_count: number;
  confidence: number;
  cats_detected: Array<{
    description: string;
    breed_guess: string;
    position: string;
    size: string;
  }>;
  image_quality: string;
  suitable_for_cat_spot: boolean;
  reasoning: string;
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

import { uploadFile, ApiError, ApiErrorTypes } from '../utils/api';
import { isDev } from '../utils/env';

export class CatDetectionService {
  async detectCats(file: File): Promise<CatDetectionResult> {
    try {
      return await uploadFile<CatDetectionResult>('/api/v1/detect/cats', file);
    } catch (error) {
      if (error instanceof ApiError) {
        if (isDev()) {
          console.error('❌ Cat detection failed:', error.message);
        }
        throw error;
      }
      
      if (isDev()) {
        console.error('🔥 Cat detection error:', error);
      }
      throw new ApiError(
        ApiErrorTypes.UNKNOWN_ERROR,
        `Cat detection failed: ${error.message || 'Unknown error'}`
      );
    }
  }

  async analyzeSpot(file: File): Promise<SpotAnalysisResult> {
    try {
      return await uploadFile<SpotAnalysisResult>('/api/v1/detect/spot-analysis', file);
    } catch (error) {
      if (error instanceof ApiError) {
        if (isDev()) {
          console.error('❌ Spot analysis failed:', error.message);
        }
        throw error;
      }
      
      if (isDev()) {
        console.error('🔥 Spot analysis error:', error);
      }
      throw new ApiError(
        ApiErrorTypes.UNKNOWN_ERROR,
        `Spot analysis failed: ${error.message || 'Unknown error'}`
      );
    }
  }

  async combinedAnalysis(file: File): Promise<CombinedAnalysisResult> {
    try {
      return await uploadFile<CombinedAnalysisResult>('/api/v1/detect/combined', file);
    } catch (error) {
      if (error instanceof ApiError) {
        if (isDev()) {
          console.error('❌ Combined analysis failed:', error.message);
        }
        throw error;
      }
      
      if (isDev()) {
        console.error('🔥 Combined analysis error:', error);
      }
      throw new ApiError(
        ApiErrorTypes.UNKNOWN_ERROR,
        `Combined analysis failed: ${error.message || 'Unknown error'}`
      );
    }
  }

  // Utility method to check if user is logged in
  isAuthenticated(): boolean {
    // Check both token keys for compatibility
    return !!(localStorage.getItem('auth_token') || localStorage.getItem('access_token'));
  }

  // Utility method to clear auth data
  clearAuth(): void {
    // Clear both token keys for compatibility
    localStorage.removeItem('auth_token');
    localStorage.removeItem('access_token');
  }
}

// Export singleton instance
export const catDetectionService = new CatDetectionService();