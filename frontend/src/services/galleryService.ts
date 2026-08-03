import type { CatLocation, PaginatedResponse, SearchParams, PaginationParams } from '../types/api';
import { apiV1 } from '../utils/api';

type GalleryRequestOptions = {
  signal?: AbortSignal;
};

export class GalleryService {
  /**
   * Get paginated gallery images
   */
  static async getImages(
    params: PaginationParams = {},
    options: GalleryRequestOptions = {}
  ): Promise<PaginatedResponse<CatLocation>> {
    const config = options.signal ? { params, signal: options.signal } : { params };
    return await apiV1.get<PaginatedResponse<CatLocation>>('/gallery', config);
  }

  /**
   * Get legacy location markers (bounded fallback for map)
   */
  static async getLocations(): Promise<CatLocation[]> {
    const data = await apiV1.get<CatLocation[] | { images: CatLocation[] }>('/gallery/locations', {
      params: { limit: 500 },
    });
    if (Array.isArray(data)) {
      return data;
    }
    return data.images || [];
  }

  /**
   * Get locations within a geographic viewport
   */
  static async getViewportLocations(bounds: {
    north: number;
    south: number;
    east: number;
    west: number;
    limit?: number;
  }, options: GalleryRequestOptions = {}): Promise<CatLocation[]> {
    const config = options.signal ? { params: bounds, signal: options.signal } : { params: bounds };
    const data = await apiV1.get<CatLocation[] | { images: CatLocation[] }>('/gallery/viewport', config);
    if (Array.isArray(data)) {
      return data;
    }
    return data.images || [];
  }

  /**
   * Search for cat locations
   */
  static async search(
    params: SearchParams,
    options: GalleryRequestOptions = {}
  ): Promise<{ results: CatLocation[]; total: number; limit?: number; offset?: number }> {
    const apiParams = {
      q: params.query,
      tags: params.tags?.join(','),
      limit: params.limit,
      offset: params.offset,
      page: params.page,
    };
    const config = options.signal ? { params: apiParams, signal: options.signal } : { params: apiParams };
    return await apiV1.get<{
      results: CatLocation[];
      total: number;
      limit?: number;
      offset?: number;
    }>('/gallery/search', {
      ...config,
    });
  }

  /**
   * Get a specific photo by ID
   */
  static async getPhotoById(id: string): Promise<CatLocation> {
    return await apiV1.get<CatLocation>(`/gallery/${id}`);
  }

  /**
   * Get popular tags
   */
  static async getPopularTags(limit = 20): Promise<{ tags: { tag: string; count: number }[] }> {
    return await apiV1.get<{ tags: { tag: string; count: number }[] }>('/gallery/popular-tags', {
      params: { limit },
    });
  }

  /**
   * Delete a photo by ID
   */
  static async deletePhoto(id: string): Promise<void> {
    await apiV1.delete(`/gallery/${id}`);
  }
}
