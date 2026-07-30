// Imported from api.ts to avoid duplication
import type { CatDetectionResult } from '../types/upload';

interface SpotAnalysisResult {
  [key: string]: unknown;
}

interface CombinedAnalysisResult {
  [key: string]: unknown;
}

import { uploadFile } from '../utils/api';

export class CatDetectionService {
  async detectCats(file: File, signal?: AbortSignal): Promise<CatDetectionResult> {
    return await uploadFile<CatDetectionResult>(
      '/api/v1/detect/cats',
      file,
      undefined,
      undefined,
      { signal, retryConfig: { maxRetries: 0 } }
    );
  }

  async analyzeSpot(file: File): Promise<SpotAnalysisResult> {
    return await uploadFile<SpotAnalysisResult>('/api/v1/detect/spot-analysis', file);
  }

  async combinedAnalysis(file: File): Promise<CombinedAnalysisResult> {
    return await uploadFile<CombinedAnalysisResult>('/api/v1/detect/combined', file);
  }
}

// Export singleton instance
export const catDetectionService = new CatDetectionService();
