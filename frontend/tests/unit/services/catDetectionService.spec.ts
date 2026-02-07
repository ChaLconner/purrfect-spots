import { describe, it, expect, vi, beforeEach } from 'vitest';
import { catDetectionService } from '@/services/catDetectionService';
import { uploadFile } from '@/utils/api';

vi.mock('@/utils/api', () => ({
  uploadFile: vi.fn(),
}));

describe('CatDetectionService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('detectCats should call uploadFile with /api/v1/detect/cats', async () => {
    const file = new File([''], 'cat.jpg', { type: 'image/jpeg' });
    vi.mocked(uploadFile).mockResolvedValue({ is_cat: true } as any);

    const res = await catDetectionService.detectCats(file);
    expect(uploadFile).toHaveBeenCalledWith('/api/v1/detect/cats', file);
    expect(res).toEqual({ is_cat: true });
  });

  it('analyzeSpot should call uploadFile with /api/v1/detect/spot-analysis', async () => {
    const file = new File([''], 'spot.jpg', { type: 'image/jpeg' });
    vi.mocked(uploadFile).mockResolvedValue({ location_type: 'indoor' } as any);

    const res = await catDetectionService.analyzeSpot(file);
    expect(uploadFile).toHaveBeenCalledWith('/api/v1/detect/spot-analysis', file);
    expect(res).toEqual({ location_type: 'indoor' });
  });

  it('combinedAnalysis should call uploadFile with /api/v1/detect/combined', async () => {
    const file = new File([''], 'combined.jpg', { type: 'image/jpeg' });
    vi.mocked(uploadFile).mockResolvedValue({ is_cat: true, location_type: 'indoor' } as any);

    const res = await catDetectionService.combinedAnalysis(file);
    expect(uploadFile).toHaveBeenCalledWith('/api/v1/detect/combined', file);
    expect(res).toEqual({ is_cat: true, location_type: 'indoor' });
  });
});
