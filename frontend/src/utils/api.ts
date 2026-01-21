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
import { isDev, getEnvVar } from './env';
import { useAuthStore } from '../store/authStore';

// In-memory access token (not exposed to window/global)
let currentAccessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  currentAccessToken = token;
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

// API Error Types
export const ApiErrorTypes = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const;

export type ApiErrorType = typeof ApiErrorTypes[keyof typeof ApiErrorTypes];

// API Error Class
export class ApiError extends Error {
  type: ApiErrorType;
  statusCode?: number;
  originalError?: unknown;

  constructor(
    type: ApiErrorType,
    message: string,
    statusCode?: number,
    originalError?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.statusCode = statusCode;
    this.originalError = originalError;
  }
}

// Get API base URL from environment variable
export const getApiBaseUrl = (): string => {
  const envUrl = getEnvVar('VITE_API_BASE_URL');
  
  if (envUrl) {
    return envUrl;
  }
  
  // Auto-detect environment
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  
  if (isLocalhost) {
    // Local development - use localhost backend
    return 'http://localhost:8000';
  } 
  
  // Production fallback
  console.warn('VITE_API_BASE_URL not set in production. Defaulting to relative path');
  return '';
};

// Create API URL with endpoint
export const getApiUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  // Remove leading slash from endpoint if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${baseUrl}/${cleanEndpoint}`;
};

// Default headers for API requests
export const getDefaultHeaders = (): Record<string, string> => {
  return {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
};

// Get headers with authentication
export const getAuthHeaders = (): Record<string, string> => {
  const headers = getDefaultHeaders();
  
  if (currentAccessToken) {
    headers['Authorization'] = `Bearer ${currentAccessToken}`;
  }
  
  return headers;
};


// Create axios instance with default configuration
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 30000, // 30 seconds timeout
    headers: getDefaultHeaders(),
    withCredentials: true, // Enable cookies for cross-site requests
  });

  // Request interceptor to add auth token
  instance.interceptors.request.use(
    (config) => {
      // Add auth token if available (from memory)
      if (currentAccessToken) {
        config.headers.Authorization = `Bearer ${currentAccessToken}`;
      }

      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for centralized error handling
  instance.interceptors.response.use(
    (response) => {
      // Check if response is actually JSON
      const contentType = response.headers['content-type'];
      if (contentType && !contentType.includes('application/json')) {
        // Handle non-JSON responses
        if (isDev()) {
          // eslint-disable-next-line no-console
          console.warn('Received non-JSON response:', contentType, response.data);
        }
        
        // Try to parse as JSON anyway in case Content-Type header is wrong
        if (typeof response.data === 'string') {
          try {
            response.data = JSON.parse(response.data);
          } catch {
            // If it's not JSON, create a proper error response
            throw new ApiError(
              ApiErrorTypes.UNKNOWN_ERROR,
              `Invalid response format from server. Expected JSON but received ${contentType}`,
              response.status,
              new Error(`Non-JSON response: ${response.data}`)
            );
          }
        }
        
        // If response data is not an object (likely HTML), throw an error
        if (typeof response.data !== 'object' || response.data === null) {
          throw new ApiError(
            ApiErrorTypes.SERVER_ERROR,
            'Server returned invalid response format. Please try again.',
            response.status,
            new Error(`Invalid response data type: ${typeof response.data}`)
          );
        }
      }
      
      return response;
    },
    async (error: AxiosError) => {
      // Handle browser extension errors first
      if (isBrowserExtensionError(error)) {
        // Retry the request once for browser extension errors
        return handleBrowserExtensionError(
          error,
          () => apiInstance.request(error.config!)
        );
      }

      // Handle different types of errors
      if (!error.response) {
        // Network error
        throw new ApiError(
          ApiErrorTypes.NETWORK_ERROR,
          'Cannot connect to server. Please check your internet connection',
          undefined,
          error
        );
      }

      const { status, data } = error.response;
      
      // Handle specific HTTP status codes
      switch (status) {
          // Authentication error - 401
          case 401: {
          const originalRequest = error.config;
          const isRefreshRequest = originalRequest?.url?.includes('/auth/refresh-token');
          
          // If it's a refresh token request that failed, we are properly logged out
          if (isRefreshRequest) {
             const auth = useAuthStore();
             auth.clearAuth();
             throw new ApiError(
              ApiErrorTypes.AUTHENTICATION_ERROR,
              'Session expired',
              status,
              error
            );
          }

          // If it's a normal request, try to refresh the token
          if (status === 401 && originalRequest && !(originalRequest as AxiosRequestConfig & { _retry?: boolean })._retry) {
            (originalRequest as AxiosRequestConfig & { _retry?: boolean })._retry = true;
            
            try {
              const auth = useAuthStore();
              const refreshed = await auth.refreshToken();
              
              if (refreshed && auth.token) {
                // Update authorization header with new token
                originalRequest.headers['Authorization'] = `Bearer ${auth.token}`;
                // Retry original request
                return apiInstance(originalRequest);
              }
            } catch (refreshError) {
              // Refresh failed - proceed to logout
              if (isDev()) {
                console.warn('Silent refresh failed:', refreshError);
              }
            }
            
            // If we get here, refresh failed or return false
            const auth = useAuthStore();
            auth.clearAuth();
            throw new ApiError(
              ApiErrorTypes.AUTHENTICATION_ERROR,
              'Login session expired. Please log in again',
              status,
              error
            );
          }
           
          // Fallback if retry logic was bypassed (shouldn't happen often)
          if (!isRefreshRequest) {
            const auth = useAuthStore();
            auth.clearAuth();
            throw new ApiError(
              ApiErrorTypes.AUTHENTICATION_ERROR,
              'Login session expired. Please log in again',
              status,
              error
            );
          }
          
          // For refresh-token requests (redundant fallback but keeps types safe)
          throw new ApiError(
            ApiErrorTypes.AUTHENTICATION_ERROR,
            'No active session',
            status,
            error
          );
        }
          
        case 403:
          // Authorization error
          throw new ApiError(
            ApiErrorTypes.AUTHORIZATION_ERROR,
            'You do not have permission to access this information',
            status,
            error
          );
          
        case 422:
          // Validation error
          const validationMessage = (data as { detail?: string })?.detail || 'Invalid data';
          throw new ApiError(
            ApiErrorTypes.VALIDATION_ERROR,
            validationMessage,
            status,
            error
          );
          
        case 500:
        case 502:
        case 503:
        case 504:
          // Server error
          throw new ApiError(
            ApiErrorTypes.SERVER_ERROR,
            'Server error. Please try again later',
            status,
            error
          );
          
        default:
          // Unknown error - check if response is HTML (common error page)
          const contentType = error.response.headers['content-type'];
          if (contentType && contentType.includes('text/html')) {
          if (isDev()) {
            console.error('Server returned HTML instead of JSON:', {
              status,
              contentType,
              url: error.config?.url,
              data: error.response.data
            });
          }
            
            throw new ApiError(
              ApiErrorTypes.SERVER_ERROR,
              'Server returned HTML error page instead of JSON. Please try again.',
              status,
              error
            );
          }
          
          // Also check for non-object responses that might indicate HTML
          if (typeof error.response.data === 'string' && error.response.data.includes('<html')) {
            if (isDev()) {
              console.error('Server returned HTML content:', {
                status,
                contentType,
                url: error.config?.url,
                dataPreview: error.response.data.substring(0, 200)
              });
            }
            
            throw new ApiError(
              ApiErrorTypes.SERVER_ERROR,
              'Server returned HTML content instead of JSON. Please try again.',
              status,
              error
            );
          }
          
          const errorMessage = (data as { detail?: string })?.detail || (data as { message?: string })?.message || (error as Error).message || 'An unknown error occurred';
          throw new ApiError(
            ApiErrorTypes.UNKNOWN_ERROR,
            errorMessage,
            status,
            error
          );
      }
    }
  );

  return instance;
};

// Create and export the API instance
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
  retryableStatuses: [408, 429, 502, 503, 504], // Request Timeout, Too Many Requests, Bad Gateway, Service Unavailable, Gateway Timeout
};

/**
 * Calculate delay with exponential backoff and jitter
 */
function calculateBackoffDelay(attempt: number, config: RetryConfig): number {
  const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
  const jitter = Math.random() * 0.3 * exponentialDelay; // Add up to 30% jitter
  return Math.min(exponentialDelay + jitter, config.maxDelayMs);
}

/**
 * Check if an error is retryable
 */
function isRetryableError(error: unknown, config: RetryConfig): boolean {
  // Network errors are always retryable
  if (error instanceof ApiError && error.type === ApiErrorTypes.NETWORK_ERROR) {
    return true;
  }
  
  // Check for retryable HTTP status codes
  if (error instanceof ApiError && error.statusCode) {
    return config.retryableStatuses.includes(error.statusCode);
  }
  
  // Check for axios errors with response status
  if (error.response?.status) {
    return config.retryableStatuses.includes(error.response.status);
  }
  
  // Network errors from axios (no response)
  if (error.request && !error.response) {
    return true;
  }
  
  return false;
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Enhanced API request functions using axios with retry logic
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
      
      // Don't retry auth errors or validation errors
      if (error instanceof ApiError) {
        if (error.type === ApiErrorTypes.AUTHENTICATION_ERROR ||
            error.type === ApiErrorTypes.AUTHORIZATION_ERROR ||
            error.type === ApiErrorTypes.VALIDATION_ERROR) {
          throw error;
        }
      }
      
      // Check if we should retry
      const isLastAttempt = attempt === config.maxRetries;
      const shouldRetry = !isLastAttempt && isRetryableError(error, config);
      
      if (shouldRetry) {
        const delay = calculateBackoffDelay(attempt, config);
        if (isDev()) {
          // eslint-disable-next-line no-console
          console.log(`[API Retry] Attempt ${attempt + 1}/${config.maxRetries + 1} failed, retrying in ${delay}ms...`, endpoint);
        }
        await sleep(delay);
        continue;
      }
      
      // Re-throw ApiError as is, or wrap other errors
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(
        ApiErrorTypes.UNKNOWN_ERROR,
        (error as Error).message || 'An unknown error occurred',
        undefined,
        error
      );
    }
  }
  
  // This should not be reached, but just in case
  throw lastError;
};


// Authenticated API request
export const authenticatedApiRequest = async <T = unknown>(
  endpoint: string,
  options: AxiosRequestConfig = {}
): Promise<T> => {
  return apiRequest<T>(endpoint, options);
};

// Convenience methods for common HTTP operations
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

// File upload helper
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
      if (typeof value === 'object') {
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

// ========== Versioned API (v1) ==========
/**
 * Versioned API object with /api/v1 prefix
 * Use this for all new code
 */
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

// ========== Pagination Utilities ==========
/**
 * Build pagination query string
 */
export function buildPaginationQuery(params: PaginationParams): string {
  const queryParams = new URLSearchParams();
  
  if (params.limit !== undefined) {
    queryParams.set('limit', params.limit.toString());
  }
  
  if (params.page !== undefined) {
    queryParams.set('page', params.page.toString());
  } else if (params.offset !== undefined) {
    queryParams.set('offset', params.offset.toString());
  }
  
  const query = queryParams.toString();
  return query ? `?${query}` : '';
}

/**
 * Fetch paginated gallery data
 */
export async function fetchPaginatedGallery<T>(
  params: PaginationParams = {}
): Promise<PaginatedResponse<T>> {
  const query = buildPaginationQuery(params);
  return apiV1.get<PaginatedResponse<T>>(`/gallery${query}`);
}

// Legacy functions are already exported individually above