import { describe, it, expect, vi, beforeEach } from 'vitest';
import { GalleryService } from '@/services/galleryService';
import { apiV1 } from '@/utils/api';

vi.mock('@/utils/api', () => ({
  apiV1: {
    get: vi.fn(),
  },
}));

describe('GalleryService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getImages should call /gallery with params', async () => {
    const mockRes = { images: [], pagination: {} };
    vi.mocked(apiV1.get).mockResolvedValue(mockRes as any);
    
    const res = await GalleryService.getImages({ limit: 10 });
    expect(apiV1.get).toHaveBeenCalledWith('/gallery', { params: { limit: 10 } });
    expect(res).toEqual(mockRes);
  });

  describe('getLocations', () => {
    it('should handle array response', async () => {
      vi.mocked(apiV1.get).mockResolvedValue([{ id: '1' }] as any);
      const res = await GalleryService.getLocations();
      expect(res).toEqual([{ id: '1' }]);
    });

    it('should handle object response with images field', async () => {
      vi.mocked(apiV1.get).mockResolvedValue({ images: [{ id: '2' }] } as any);
      const res = await GalleryService.getLocations();
      expect(res).toEqual([{ id: '2' }]);
    });

    it('should return empty array if no images field', async () => {
      vi.mocked(apiV1.get).mockResolvedValue({} as any);
      const res = await GalleryService.getLocations();
      expect(res).toEqual([]);
    });
  });

  describe('getViewportLocations', () => {
    const bounds = { north: 1, south: 0, east: 1, west: 0 };
    
    it('should handle array response', async () => {
      vi.mocked(apiV1.get).mockResolvedValue([{ id: '1' }] as any);
      const res = await GalleryService.getViewportLocations(bounds);
      expect(apiV1.get).toHaveBeenCalledWith('/gallery/viewport', { params: bounds });
      expect(res).toEqual([{ id: '1' }]);
    });

    it('should handle object response', async () => {
      vi.mocked(apiV1.get).mockResolvedValue({ images: [{ id: '2' }] } as any);
      const res = await GalleryService.getViewportLocations(bounds);
      expect(res).toEqual([{ id: '2' }]);
    });
  });

  it('search should map params correctly', async () => {
    vi.mocked(apiV1.get).mockResolvedValue({ results: [], total: 0 } as any);
    await GalleryService.search({ query: 'cat', tags: ['cute'], limit: 5 });
    expect(apiV1.get).toHaveBeenCalledWith('/gallery/search', {
      params: {
        q: 'cat',
        tags: 'cute',
        limit: 5
      }
    });
  });

  it('getPhotoById should call correct endpoint', async () => {
    vi.mocked(apiV1.get).mockResolvedValue({ id: '123' } as any);
    const res = await GalleryService.getPhotoById('123');
    expect(apiV1.get).toHaveBeenCalledWith('/gallery/123');
    expect(res).toEqual({ id: '123' });
  });

  it('getPopularTags should call correct endpoint with limit', async () => {
    vi.mocked(apiV1.get).mockResolvedValue({ tags: [] } as any);
    await GalleryService.getPopularTags(10);
    expect(apiV1.get).toHaveBeenCalledWith('/gallery/popular-tags', {
      params: { limit: 10 }
    });
  });
});
