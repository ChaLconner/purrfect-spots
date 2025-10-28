/**
 * API configuration and utilities with centralized error handling and interceptors
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { clearAuth } from '../store/auth';
import { getEnvVar } from './env';
import { isBrowserExtensionError, handleBrowserExtensionError } from './browserExtensionHandler';

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
  originalError?: any;

  constructor(
    type: ApiErrorType,
    message: string,
    statusCode?: number,
    originalError?: any
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
  const isVercel = window.location.hostname.includes('vercel.app');
  
  if (isLocalhost) {
    // Local development - use localhost backend
    return 'http://localhost:8000';
  } else if (isVercel) {
    // Vercel deployment - use relative path for same-origin requests
    // This will automatically route to the backend through vercel.json routes
    return '/api';
  } else {
    // Fallback for other environments
    return 'https://purrfect-spots-backend.vercel.app';
  }
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
  // Try both token keys for compatibility
  const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');
  const headers = getDefaultHeaders();
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

// Create axios instance with default configuration
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 30000, // 30 seconds timeout
    headers: getDefaultHeaders(),
  });

  // Request interceptor to add auth token
  instance.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      // Request logging removed for cleaner console
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for centralized error handling
  instance.interceptors.response.use(
    (response) => {
      // Response logging removed for cleaner console
      
      return response;
    },
    (error: AxiosError) => {
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
        case 401:
          // Authentication error - clear auth data and redirect to login
          clearAuth();
          throw new ApiError(
            ApiErrorTypes.AUTHENTICATION_ERROR,
            'Login session expired. Please log in again',
            status,
            error
          );
          
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
          const validationMessage = (data as any)?.detail || 'Invalid data';
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
          // Unknown error
          const errorMessage = (data as any)?.detail || (data as any)?.message || (error as Error).message || 'An unknown error occurred';
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

// Enhanced API request functions using axios
export const apiRequest = async <T = any>(
  endpoint: string,
  options: AxiosRequestConfig = {}
): Promise<T> => {
  try {
    const response = await apiInstance.request<T>({
      url: endpoint,
      ...options,
    });
    
    return response.data;
  } catch (error) {
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
};

// Authenticated API request
export const authenticatedApiRequest = async <T = any>(
  endpoint: string,
  options: AxiosRequestConfig = {}
): Promise<T> => {
  return apiRequest<T>(endpoint, options);
};

// Convenience methods for common HTTP operations
export const api = {
  get: <T = any>(endpoint: string, config?: AxiosRequestConfig) => 
    apiRequest<T>(endpoint, { method: 'GET', ...config }),
    
  post: <T = any>(endpoint: string, data?: any, config?: AxiosRequestConfig) => 
    apiRequest<T>(endpoint, { method: 'POST', data, ...config }),
    
  put: <T = any>(endpoint: string, data?: any, config?: AxiosRequestConfig) => 
    apiRequest<T>(endpoint, { method: 'PUT', data, ...config }),
    
  patch: <T = any>(endpoint: string, data?: any, config?: AxiosRequestConfig) => 
    apiRequest<T>(endpoint, { method: 'PATCH', data, ...config }),
    
  delete: <T = any>(endpoint: string, config?: AxiosRequestConfig) => 
    apiRequest<T>(endpoint, { method: 'DELETE', ...config }),
};

// File upload helper
export const uploadFile = async <T = any>(
  endpoint: string,
  file: File,
  additionalData?: Record<string, any>,
  onUploadProgress?: (progressEvent: any) => void
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

// Legacy functions are already exported individually above