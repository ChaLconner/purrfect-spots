// Imported from api.ts to avoid duplication
import type { CatDetectionResult } from '../types/upload';

interface SpotAnalysisResult {
  [key: string]: unknown;
}

interface CombinedAnalysisResult {
  [key: string]: unknown;
}

import { apiV1, uploadFile } from '../utils/api';

interface QueuedVisionJob {
  status: 'queued';
  job_id: string;
  operation: 'spot-analysis' | 'combined';
  created_at: string;
}

interface VisionJobStatus {
  status: 'queued' | 'processing' | 'completed' | 'failed';
  job_id: string;
  result?: Record<string, unknown> | null;
  error?: string | null;
}

function isQueuedVisionJob(value: unknown): value is QueuedVisionJob {
  return Boolean(
    value &&
      typeof value === 'object' &&
      (value as { status?: unknown }).status === 'queued' &&
      typeof (value as { job_id?: unknown }).job_id === 'string'
  );
}

class CatDetectionService {
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
    const response = await uploadFile<SpotAnalysisResult | QueuedVisionJob>('/api/v1/detect/spot-analysis', file);
    return (await this.resolveVisionJob(response)) as SpotAnalysisResult;
  }

  async combinedAnalysis(file: File): Promise<CombinedAnalysisResult> {
    const response = await uploadFile<CombinedAnalysisResult | QueuedVisionJob>('/api/v1/detect/combined', file);
    return (await this.resolveVisionJob(response)) as CombinedAnalysisResult;
  }

  private async resolveVisionJob(response: SpotAnalysisResult | CombinedAnalysisResult | QueuedVisionJob): Promise<Record<string, unknown>> {
    if (!isQueuedVisionJob(response)) return response;

    for (let attempt = 0; attempt < 120; attempt++) {
      const status = await apiV1.get<VisionJobStatus>(`/detect/jobs/${response.job_id}`);
      if (status.status === 'completed' && status.result) return status.result;
      if (status.status === 'failed') {
        throw new Error(status.error || 'Vision analysis failed');
      }
      await new Promise<void>((resolve) => setTimeout(resolve, 500));
    }
    throw new Error('Vision analysis timed out while waiting for the worker');
  }
}

// Export singleton instance
export const catDetectionService = new CatDetectionService();
