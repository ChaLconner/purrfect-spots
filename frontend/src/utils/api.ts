/**
 * API configuration and utilities with centralized error handling and interceptors
 *
 * API Versioning:
 * - All new endpoints should use /api/v1/ prefix
 * - Legacy endpoints (without prefix) are maintained for backward compatibility
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosError, AxiosProgressEvent } from 'axios';
import { isBrowserExtensionError, handleBrowserExtensionError } from './browserExtensionHandler';
import { getEnvVar } from './env';

// ========== API Error Types & Classes (Defined Early) ==========
export const ApiErrorTypes = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

export type ApiErrorType = (typeof ApiErrorTypes)[keyof typeof ApiErrorTypes];

export class ApiError extends Error {
  type: ApiErrorType;
  statusCode?: number;
  originalError?: unknown;

  constructor(type: ApiErrorType, message: string, statusCode?: number, originalError?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.statusCode = statusCode;
    this.originalError = originalError;
  }
}

// ========== State & Callbacks (Break Circular Dependencies) ==========
// In-memory access token (not exposed to window/global)
let currentAccessToken: string | null = null;
let refreshTokenCallback: (() => Promise<boolean>) | null = null;
let logoutCallback: (() => void) | null = null;

export const setAccessToken = (token: string | null) => {
  currentAccessToken = token;
};

export const setAuthCallbacks = (refreshFn: () => Promise<boolean>, logoutFn: () => void) => {
  refreshTokenCallback = refreshFn;
  logoutCallback = logoutFn;
};

// ========== API Configuration ==========
export const API_VERSION = 'v1';
export const API_PREFIX = `/api/${API_VERSION}`;

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

// ========== Helpers ==========
export const getApiBaseUrl = (): string => {
  const envUrl = getEnvVar('VITE_API_BASE_URL');

  if (envUrl) {
    return envUrl;
  }

  const isLocalhost =
    globalThis.location.hostname === 'localhost' || globalThis.location.hostname === '127.0.0.1';

  if (isLocalhost) {
    return 'http://localhost:8000';
  }

  if (!envUrl) {
    // Info logs removed for production safety
  }

  return envUrl || '';
};

export const getApiUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${baseUrl}/${cleanEndpoint}`;
};

export const getDefaultHeaders = (): Record<string, string> => {
  return {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
};

export const getAuthHeaders = (): Record<string, string> => {
  const headers = getDefaultHeaders();
  if (currentAccessToken) {
    headers['Authorization'] = `Bearer ${currentAccessToken}`;
  }
  return headers;
};

// ========== Axios Instance Creation ==========
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 30000,
    headers: getDefaultHeaders(),
    withCredentials: true,
  });

  // Request interceptor to add auth token
  instance.interceptors.request.use(
    (config) => {
      if (currentAccessToken) {
        config.headers.Authorization = `Bearer ${currentAccessToken}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor
  instance.interceptors.response.use(
    (response) => {
      const contentType = response.headers['content-type'];
      if (contentType && !contentType.includes('application/json')) {
        // Warn removed
        if (typeof response.data === 'string') {
          try {
            response.data = JSON.parse(response.data);
          } catch {
            // ignore
          }
        }
        if (typeof response.data !== 'object' || response.data === null) {
          // Only throw if we strictly expect object and got something else that isn't parseable
          // But for now, let's allow it unless it causes issues, or throw specific error?
          // Original code threw error here.
          throw new ApiError(
            ApiErrorTypes.SERVER_ERROR,
            'Server returned invalid response format.',
            response.status,
            new Error(`Invalid response data type: ${typeof response.data}`)
          );
        }
      }
      return response;
    },
    async (error: AxiosError) => {
      if (isBrowserExtensionError(error)) {
        return handleBrowserExtensionError(error, () => instance.request(error.config!));
      }

      if (!error.response) {
        throw new ApiError(
          ApiErrorTypes.NETWORK_ERROR,
          'Cannot connect to server. Please check your internet connection',
          undefined,
          error
        );
      }

      const { status, data } = error.response;

      const handlers: Record<number, () => never> = {
        403: () => {
          throw new ApiError(ApiErrorTypes.AUTHORIZATION_ERROR, 'You do not have permission to access this information', status, error);
        },
        422: () => {
          const validationMessage = (data as { detail?: string })?.detail || 'Invalid data';
          throw new ApiError(ApiErrorTypes.VALIDATION_ERROR, validationMessage, status, error);
        }
      };

      if (status === 401) {
        return handleUnauthorizedError(error, status);
      }

      if (handlers[status]) return handlers[status]();

      if (status >= 500) {
        const serverDetail = (data as { detail?: string })?.detail;
        const message = serverDetail || 'Server error. Please try again later';
        throw new ApiError(ApiErrorTypes.SERVER_ERROR, message, status, error);
      }

      const errorMessage =
        (data as { detail?: string })?.detail ||
        (data as { message?: string })?.message ||
        (error as Error).message ||
        'An unknown error occurred';
      throw new ApiError(ApiErrorTypes.UNKNOWN_ERROR, errorMessage, status, error);
    }
  );

  return instance;
};

// Handle 401 errors (Token Expiry)
async function handleUnauthorizedError(error: AxiosError, status: number) {
  const originalRequest = error.config;
  if (!originalRequest) return Promise.reject(error);

  // Avoid infinite loops
  if ((originalRequest as any)._retry) { // eslint-disable-line @typescript-eslint/no-explicit-any
    if (logoutCallback) logoutCallback();
    return Promise.reject(error);
  }

  (originalRequest as any)._retry = true; // eslint-disable-line @typescript-eslint/no-explicit-any

  try {
    if (refreshTokenCallback) {
      const refreshed = await refreshTokenCallback();
      if (refreshed) {
        // Retry original request with new token
        if (currentAccessToken) {
          originalRequest.headers.Authorization = `Bearer ${currentAccessToken}`;
        }
        return apiInstance(originalRequest);
      }
    }
    
    // Refresh failed or no callback
    if (logoutCallback) logoutCallback();
    throw new ApiError(ApiErrorTypes.AUTHENTICATION_ERROR, 'Session expired. Please login again.', status, error);
  } catch (refreshError) {
    if (logoutCallback) logoutCallback();
    return Promise.reject(refreshError);
  }
};

export const apiInstance = createApiInstance();

// ========== Retry Configuration ==========
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableStatuses: number[];
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
  retryableStatuses: [408, 429, 502, 503, 504],
};

function calculateBackoffDelay(attempt: number, config: RetryConfig): number {
  const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
  // nosec typescript:S2245 - Math.random() is intentional for retry jitter timing
  // PRNG is acceptable for network retry delays; cryptographic randomness not required
  const jitter = Math.random() * 0.3 * exponentialDelay;
  return Math.min(exponentialDelay + jitter, config.maxDelayMs);
}

function isRetryableError(error: unknown, config: RetryConfig): boolean {
  if (error instanceof ApiError && error.type === ApiErrorTypes.NETWORK_ERROR) return true;
  if (error instanceof ApiError && error.statusCode)
    return config.retryableStatuses.includes(error.statusCode);
  if ((error as AxiosError).response?.status)
    return config.retryableStatuses.includes((error as AxiosError).response!.status);
  if ((error as AxiosError).request && !(error as AxiosError).response) return true;
  return false;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export const apiRequest = async <T = unknown>(
  endpoint: string,
  options: AxiosRequestConfig = {},
  retryConfig: Partial<RetryConfig> = {}
): Promise<T> => {
  const config = { ...DEFAULT_RETRY_CONFIG, ...retryConfig };
  let lastError: unknown;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const response = await apiInstance.request<T>({
        url: endpoint,
        ...options,
      });
      return response.data;
    } catch (error) {
      lastError = error;

      if (
        error instanceof ApiError &&
        (error.type === ApiErrorTypes.AUTHENTICATION_ERROR ||
          error.type === ApiErrorTypes.AUTHORIZATION_ERROR ||
          error.type === ApiErrorTypes.VALIDATION_ERROR)
      ) {
        throw error;
      }

      const isLastAttempt = attempt === config.maxRetries;
      const shouldRetry = !isLastAttempt && isRetryableError(error, config);

      if (shouldRetry) {
        const delay = calculateBackoffDelay(attempt, config);
        // Log removed
        await sleep(delay);
        continue;
      }

      if (error instanceof ApiError) throw error;
      throw new ApiError(
        ApiErrorTypes.UNKNOWN_ERROR,
        (error as Error).message || 'An unknown error occurred',
        undefined,
        error
      );
    }
  }
  throw lastError;
};

export const authenticatedApiRequest = async <T = unknown>(
  endpoint: string,
  options: AxiosRequestConfig = {}
): Promise<T> => {
  return apiRequest<T>(endpoint, options);
};

export const api = {
  get: <T = unknown>(endpoint: string, config?: AxiosRequestConfig) =>
    apiRequest<T>(endpoint, { method: 'GET', ...config }),

  post: <T = unknown>(endpoint: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiRequest<T>(endpoint, { method: 'POST', data, ...config }),

  put: <T = unknown>(endpoint: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiRequest<T>(endpoint, { method: 'PUT', data, ...config }),

  patch: <T = unknown>(endpoint: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiRequest<T>(endpoint, { method: 'PATCH', data, ...config }),

  delete: <T = unknown>(endpoint: string, config?: AxiosRequestConfig) =>
    apiRequest<T>(endpoint, { method: 'DELETE', ...config }),
};

export const uploadFile = async <T = unknown>(
  endpoint: string,
  file: File,
  additionalData?: Record<string, unknown>,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
): Promise<T> => {
  const formData = new FormData();
  formData.append('file', file);

  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      if (typeof value === 'object' && value !== null) {
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, String(value));
      }
    });
  }

  return apiRequest<T>(endpoint, {
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress,
  });
};

export const apiV1 = {
  get: <T = unknown>(endpoint: string, config?: AxiosRequestConfig) =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'GET', ...config }),

  post: <T = unknown>(endpoint: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'POST', data, ...config }),

  put: <T = unknown>(endpoint: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'PUT', data, ...config }),

  patch: <T = unknown>(endpoint: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'PATCH', data, ...config }),

  delete: <T = unknown>(endpoint: string, config?: AxiosRequestConfig) =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'DELETE', ...config }),
};

export function buildPaginationQuery(params: PaginationParams): string {
  const queryParams = new URLSearchParams();
  if (params.limit !== undefined) queryParams.set('limit', params.limit.toString());
  if (params.page !== undefined) {
    queryParams.set('page', params.page.toString());
  } else if (params.offset !== undefined) {
    queryParams.set('offset', params.offset.toString());
  }
  const query = queryParams.toString();
  return query ? `?${query}` : '';
}

export async function fetchPaginatedGallery<T>(
  params: PaginationParams = {}
): Promise<PaginatedResponse<T>> {
  const query = buildPaginationQuery(params);
  return apiV1.get<PaginatedResponse<T>>(`/gallery${query}`);
}
