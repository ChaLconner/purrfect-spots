import type { CatLocation, PaginatedResponse, SearchParams, PaginationParams } from '../types/api';
import { apiV1 } from '../utils/api';

export class GalleryService {
  /**
   * Get paginated gallery images
   */
  static async getImages(params: PaginationParams = {}): Promise<PaginatedResponse<CatLocation>> {
    return await apiV1.get<PaginatedResponse<CatLocation>>('/gallery', { params });
  }

  /**
   * Get all location markers (for map)
   */
  static async getLocations(): Promise<CatLocation[]> {
    const data = await apiV1.get<CatLocation[] | { images: CatLocation[] }>('/gallery/locations');
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
    limit?: number 
  }): Promise<CatLocation[]> {
    const data = await apiV1.get<CatLocation[] | { images: CatLocation[] }>('/gallery/viewport', { 
      params: bounds 
    });
    if (Array.isArray(data)) {
      return data;
    }
    return data.images || [];
  }

  /**
   * Search for cat locations
   */
  static async search(params: SearchParams): Promise<{ results: CatLocation[]; total: number }> {
    const apiParams = {
      q: params.query,
      tags: params.tags?.join(','),
      limit: params.limit
    };
    return await apiV1.get<{ results: CatLocation[]; total: number }>('/gallery/search', { 
      params: apiParams 
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
      params: { limit } 
    });
  }
}
