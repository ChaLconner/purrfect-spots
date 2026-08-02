import type { components } from '../generated/api';

export type CatLocation = components['schemas']['CatLocation'];
export type PaginationMeta = components['schemas']['PaginationMeta'];

export interface PaginationParams {
  limit?: number;
  offset?: number;
  page?: number;
}

export interface PaginatedResponse<T> {
  images: T[];
  pagination: PaginationMeta;
}

export interface SearchParams extends PaginationParams {
  query: string;
  tags?: string[];
}
