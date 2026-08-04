/**
 * API configuration and utilities with centralized error handling and interceptors
 *
 * API Versioning:
 * - All new endpoints should use /api/v1/ prefix
 * - Legacy endpoints (without prefix) are maintained for backward compatibility
 */

import axios from 'axios';
import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosError,
  AxiosProgressEvent,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from 'axios';
import { isBrowserExtensionError, handleBrowserExtensionError } from './browserExtensionHandler';
import { getEnvVar } from './env';
import { getCsrfToken } from './csrf';
import type { PaginationParams } from '../types/api';
import {
  createOfflineIdempotencyKey,
  enqueueMutation,
  isAllowedMutation,
  registerOfflineReplayHandler,
  OfflineQueueError,
  type OfflineMutation,
} from './offlineQueue';

import { ApiError, ApiErrorTypes, formatApiErrorMessage } from './apiErrors';
export { ApiError, ApiErrorTypes, formatApiErrorMessage };
export type { OfflineQueuedResponse } from './offlineQueue';

// ========== State & Callbacks (Break Circular Dependencies) ==========
// In-memory access token (not exposed to window/global)
let currentAccessToken: string | null = null;
let refreshTokenCallback: (() => Promise<boolean>) | null = null;
let logoutCallback: (() => void) | null = null;

export const setAccessToken = (token: string | null): void => {
  currentAccessToken = token;
};

export const setAuthCallbacks = (refreshFn: () => Promise<boolean>, logoutFn: () => void): void => {
  refreshTokenCallback = refreshFn;
  logoutCallback = logoutFn;
};

// ========== API Configuration ==========
const API_VERSION = 'v1';
const API_PREFIX = `/api/${API_VERSION}`;

// Endpoints that should never trigger the 401 refresh interceptor
const AUTH_ENDPOINTS = ['/auth/refresh-token', '/auth/login', '/auth/register', '/auth/logout'];

// ========== Pagination Types ==========
// ========== Helpers ==========
const SAME_ORIGIN_API_BASE_URL = '';

const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '0.0.0.0']);

const isApiPath = (pathname: string): boolean => {
  return pathname === '/api' || pathname.startsWith('/api/');
};

const normalizeRequestUrl = (configuredUrl: string): string => {
  const trimmedUrl = configuredUrl.trim();
  if (!trimmedUrl || typeof window === 'undefined') {
    return trimmedUrl;
  }

  try {
    const parsedUrl = new URL(trimmedUrl, window.location.origin);
    const targetIsLoopback = LOOPBACK_HOSTS.has(parsedUrl.hostname);

    if (targetIsLoopback && isApiPath(parsedUrl.pathname)) {
      return `${parsedUrl.pathname}${parsedUrl.search}${parsedUrl.hash}`;
    }
  } catch {
    // Keep non-URL strings such as relative paths untouched.
  }

  return trimmedUrl;
};

const normalizeApiBaseUrl = (configuredBaseUrl: string): string => {
  const trimmedBaseUrl = configuredBaseUrl.trim();
  if (!trimmedBaseUrl) {
    return SAME_ORIGIN_API_BASE_URL;
  }

  // `apiV1` already prefixes `/api/v1`, so same-origin `/api` or `/api/v1`
  // base URLs would duplicate the path.
  if (
    trimmedBaseUrl === '/api' ||
    trimmedBaseUrl === '/api/' ||
    trimmedBaseUrl === '/api/v1' ||
    trimmedBaseUrl === '/api/v1/'
  ) {
    return SAME_ORIGIN_API_BASE_URL;
  }

  if (typeof window === 'undefined') {
    return trimmedBaseUrl.endsWith('/') ? trimmedBaseUrl.slice(0, -1) : trimmedBaseUrl;
  }

  try {
    const parsedUrl = new URL(trimmedBaseUrl, window.location.origin);
    const targetIsLoopback = LOOPBACK_HOSTS.has(parsedUrl.hostname);
    const targetIsApiPath = isApiPath(parsedUrl.pathname);

    // Loopback API URLs break CSP/cookie behavior once the frontend is served
    // from another origin. Normalize them to the same-origin `/api` proxy.
    if (targetIsLoopback && targetIsApiPath) {
      return SAME_ORIGIN_API_BASE_URL;
    }
  } catch {
    // Ignore malformed URLs and fall back to the raw configured value.
  }

  return trimmedBaseUrl.endsWith('/') ? trimmedBaseUrl.slice(0, -1) : trimmedBaseUrl;
};

export const getApiBaseUrl = (): string => {
  const envUrl = getEnvVar('VITE_API_BASE_URL');
  if (envUrl) {
    return normalizeApiBaseUrl(envUrl);
  }

  // Prefer the frontend's same-origin `/api` rewrite in every environment.
  // In development, Vite proxies `/api` to the local backend; in production,
  // Vercel/nginx rewrites keep requests same-origin and avoid extra CORS cost.
  return SAME_ORIGIN_API_BASE_URL;
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
    (config): InternalAxiosRequestConfig => {
      if (typeof config.baseURL === 'string') {
        config.baseURL = normalizeApiBaseUrl(config.baseURL);
      }

      if (typeof config.url === 'string') {
        config.url = normalizeRequestUrl(config.url);
      }

      // 1. Add Auth Token
      if (currentAccessToken) {
        config.headers.Authorization = `Bearer ${currentAccessToken}`;
      }

      // 2. Add CSRF Token for state-changing requests
      // This is essential for preventing CSRF attacks
      const method = config.method?.toUpperCase();
      const safeMethods = ['GET', 'HEAD', 'OPTIONS'];
      if (method && !safeMethods.includes(method)) {
        config.headers['X-Requested-With'] = 'XMLHttpRequest';
        const csrfToken = getCsrfToken();
        if (csrfToken) {
          config.headers['X-CSRF-Token'] = csrfToken;
        }
      }

      return config;
    },
    (error): Promise<never> => Promise.reject(error)
  );

  // Response interceptor
  instance.interceptors.response.use(
    (response): AxiosResponse => {
      const contentType = response.headers['content-type'];
      if (typeof contentType === 'string' && !contentType.includes('application/json')) {
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
    async (error: AxiosError): Promise<unknown> => {
      if (isBrowserExtensionError(error)) {
        return handleBrowserExtensionError(error, () => {
          if (!error.config) {
            throw error;
          }
          return instance.request(error.config);
        });
      }

      // Cancellation is caller-controlled flow, not a network failure. Keep
      // Axios' cancellation error intact so request retries can stop too.
      if (axios.isCancel(error)) {
        throw error;
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
          throw new ApiError(
            ApiErrorTypes.AUTHORIZATION_ERROR,
            'You do not have permission to access this information',
            status,
            error
          );
        },
        422: () => {
          const validationMessage = (data as { detail?: string })?.detail || 'Invalid data';
          throw new ApiError(ApiErrorTypes.VALIDATION_ERROR, validationMessage, status, error);
        },
        429: () => {
          const retryAfter = error.response?.headers?.['retry-after'];
          const seconds = retryAfter ? parseInt(String(retryAfter), 10) : 60;
          const msg = `Rate limit exceeded. Please wait ${seconds} seconds before retrying.`;
          throw new ApiError(ApiErrorTypes.SERVER_ERROR, msg, status, error);
        },
      };

      if (status === 401) {
        // Don't try to refresh if the failing request IS the refresh-token call (or other auth endpoints)
        const rawUrl = error.config?.url || '';
        const cleanUrl = rawUrl.split('?')[0].toLowerCase();
        const isAuthEndpoint = AUTH_ENDPOINTS.some((ep) => {
          const lowerEp = ep.toLowerCase();
          return cleanUrl === lowerEp || cleanUrl.endsWith(lowerEp) || cleanUrl.endsWith(`/api/v1${lowerEp}`);
        });

        if (!isAuthEndpoint) {
          return handleUnauthorizedError(error, status);
        }
        // For auth endpoints that fail with 401, just throw directly
        throw new ApiError(
          ApiErrorTypes.AUTHENTICATION_ERROR,
          'Authentication failed.',
          status,
          error
        );
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

export interface ApiRequestConfig extends AxiosRequestConfig {
  /** Explicit opt-in for the allow-listed social/notification offline queue. */
  queueWhenOffline?: boolean;
}

interface RetryableRequestConfig extends ApiRequestConfig {
  _retry?: boolean;
  __is_refreshing?: boolean;
}

let isRefreshingToken = false;
let refreshPromise: Promise<boolean> | null = null;

// Handle 401 errors (Token Expiry)
async function handleUnauthorizedError(error: AxiosError, status: number): Promise<unknown> {
  const originalRequest = error.config as RetryableRequestConfig;
  if (!originalRequest) throw error;

  // Avoid infinite loops
  if (originalRequest._retry || originalRequest.__is_refreshing) {
    console.warn('[API Interceptor] Infinite retry loop detected for:', originalRequest.url);
    if (logoutCallback) logoutCallback();
    throw error;
  }

  originalRequest._retry = true;
  originalRequest.__is_refreshing = true;

  try {
    if (refreshTokenCallback) {
      if (!isRefreshingToken) {
        isRefreshingToken = true;
        refreshPromise = refreshTokenCallback().finally(() => {
          isRefreshingToken = false;
          refreshPromise = null;
        });
      }
      const refreshed = await refreshPromise;
      if (refreshed) {
        // Retry original request with new token
        if (currentAccessToken && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${currentAccessToken}`;
        }
        return apiInstance(originalRequest);
      }
    }

    // Refresh failed or no callback
    if (logoutCallback) logoutCallback();
    throw new ApiError(
      ApiErrorTypes.AUTHENTICATION_ERROR,
      'Session expired. Please login again.',
      status,
      error
    );
  } catch (refreshError) {
    if (logoutCallback) logoutCallback();
    throw refreshError;
  }
}

export const apiInstance = createApiInstance();

// ========== Retry Configuration ==========
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableStatuses: number[];
}

export interface UploadFileOptions {
  signal?: AbortSignal;
  idempotencyKey?: string;
  retryConfig?: Partial<RetryConfig>;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 2,
  baseDelayMs: 500,
  maxDelayMs: 10000,
  retryableStatuses: [408, 429, 502, 503, 504],
};

const inFlightGetRequests = new Map<string, Promise<unknown>>();

function getRequestDedupeKey(endpoint: string, options: ApiRequestConfig): string | null {
  if ((options.method ?? 'GET').toString().toUpperCase() !== 'GET' || options.signal) return null;
  try {
    return JSON.stringify([endpoint, options.params ?? null, currentAccessToken]);
  } catch {
    return null;
  }
}

function calculateBackoffDelay(attempt: number, config: RetryConfig): number {
  const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
  // nosec typescript:S2245 - Math.random() is intentional for retry jitter timing
  // PRNG is acceptable for network retry delays; cryptographic randomness not required
  const jitter = Math.random() * 0.3 * exponentialDelay; // NOSONAR typescript:S2245 - PRNG acceptable for network retry jitter; not security-sensitive
  return Math.min(exponentialDelay + jitter, config.maxDelayMs);
}

function isRetryableError(error: unknown, config: RetryConfig): boolean {
  // Check for network errors (no response)
  const isNetworkError =
    (error instanceof ApiError && error.type === ApiErrorTypes.NETWORK_ERROR) ||
    ((error as AxiosError).request && !(error as AxiosError).response);

  // SECURITY: In production, do not retry network errors as they are likely CORS blocks
  // Retrying them causes "infinite loop" symptoms and overwhelms the browser/server
  if (import.meta.env.PROD && isNetworkError) {
    console.warn('[API] Permanent network error or CORS block detected. Skipping retry.');
    return false;
  }

  if (error instanceof ApiError && error.type === ApiErrorTypes.NETWORK_ERROR) return true;
  if (error instanceof ApiError && error.statusCode)
    return config.retryableStatuses.includes(error.statusCode);

  const response = (error as AxiosError).response;
  if (response?.status) return config.retryableStatuses.includes(response.status);

  return isNetworkError; // Only retry if it was exactly a network error (and not in PROD)
}

function createAbortError(): Error {
  const error = new Error('The request was aborted');
  error.name = 'AbortError';
  return error;
}

export function isRequestAborted(error: unknown): boolean {
  if (axios.isCancel(error)) return true;
  if (error instanceof ApiError) return isRequestAborted(error.originalError);
  if (error instanceof Error && error.name === 'AbortError') return true;
  if (typeof error === 'object' && error !== null && 'code' in error) {
    return (error as { code?: unknown }).code === 'ERR_CANCELED';
  }
  return false;
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  if (!signal) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  if (signal.aborted) {
    return Promise.reject(createAbortError());
  }

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      signal.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    const onAbort = (): void => {
      clearTimeout(timer);
      signal.removeEventListener('abort', onAbort);
      reject(createAbortError());
    };
    signal.addEventListener('abort', onAbort, { once: true });
  });
}

function getHeaderValue(headers: ApiRequestConfig['headers'], name: string): string | undefined {
  if (!headers) return undefined;
  if (typeof (headers as { get?: (headerName: string) => unknown }).get === 'function') {
    const value = (headers as { get: (headerName: string) => unknown }).get(name);
    return typeof value === 'string' ? value : undefined;
  }
  const record = headers as Record<string, unknown>;
  const value = record[name] ?? record[name.toLowerCase()];
  return typeof value === 'string' ? value : undefined;
}

function shouldQueueNetworkFailure(error: unknown): boolean {
  return error instanceof ApiError && error.type === ApiErrorTypes.NETWORK_ERROR;
}

function isOfflineQueueEnabled(endpoint: string, options: ApiRequestConfig): boolean {
  return Boolean(
    options.queueWhenOffline &&
      isAllowedMutation((options.method ?? 'GET').toString(), endpoint) &&
      typeof window !== 'undefined'
  );
}

function getQueueIdempotencyKey(options: ApiRequestConfig, queueEnabled: boolean): string | undefined {
  return queueEnabled
    ? getHeaderValue(options.headers, 'Idempotency-Key') || createOfflineIdempotencyKey()
    : undefined;
}

function buildRequestOptions(options: ApiRequestConfig, queueIdempotencyKey: string | undefined): ApiRequestConfig {
  if (!queueIdempotencyKey) return options;
  return {
    ...options,
    headers: {
      ...(options.headers as Record<string, string> | undefined),
      'Idempotency-Key': queueIdempotencyKey,
    },
  };
}

async function enqueueOfflineMutation<T>(
  endpoint: string,
  requestOptions: ApiRequestConfig,
  idempotencyKey: string
): Promise<T> {
  const method = requestOptions.method?.toString().toUpperCase();
  if (method !== 'POST' && method !== 'PUT') {
    throw new OfflineQueueError('Offline queue requires a POST or PUT mutation');
  }
  return (await enqueueMutation({
    method,
    endpoint,
    data: requestOptions.data,
    idempotencyKey,
  })) as T;
}

async function performRequestAttempt<T>(
  endpoint: string,
  requestOptions: ApiRequestConfig,
  queueEnabled: boolean,
  queueIdempotencyKey: string | undefined
): Promise<T> {
  if (queueEnabled && typeof navigator !== 'undefined' && !navigator.onLine) {
    if (!queueIdempotencyKey) throw new OfflineQueueError('Offline queue idempotency key is missing');
    return enqueueOfflineMutation<T>(endpoint, requestOptions, queueIdempotencyKey);
  }
  if (requestOptions.signal?.aborted) throw createAbortError();
  const response = await apiInstance.request<T>({
    url: endpoint,
    ...requestOptions,
  });
  return response.data;
}

function isNonRetryableRequestError(error: unknown, requestOptions: ApiRequestConfig): boolean {
  if (error instanceof OfflineQueueError) return true;
  if (requestOptions.signal?.aborted || isRequestAborted(error)) return true;
  return (
    error instanceof ApiError &&
    [
      ApiErrorTypes.AUTHENTICATION_ERROR,
      ApiErrorTypes.AUTHORIZATION_ERROR,
      ApiErrorTypes.VALIDATION_ERROR,
    ].includes(error.type)
  );
}

function throwRequestError(error: unknown): never {
  if (error instanceof ApiError) throw error;
  throw new ApiError(
    ApiErrorTypes.UNKNOWN_ERROR,
    (error as Error).message || 'An unknown error occurred',
    undefined,
    error
  );
}

const requestWithRetry = async <T = unknown>(
  endpoint: string,
  options: ApiRequestConfig = {},
  retryConfig: Partial<RetryConfig> = {}
): Promise<T> => {
  // Never retry auth endpoints - they have their own refresh/retry logic
  const isAuthEndpoint = AUTH_ENDPOINTS.some((ep) => endpoint.includes(ep));
  const config = isAuthEndpoint
    ? { ...DEFAULT_RETRY_CONFIG, ...retryConfig, maxRetries: 0 }
    : { ...DEFAULT_RETRY_CONFIG, ...retryConfig };
  const queueEnabled = isOfflineQueueEnabled(endpoint, options);
  const queueIdempotencyKey = getQueueIdempotencyKey(options, queueEnabled);
  const requestOptions = buildRequestOptions(options, queueIdempotencyKey);
  let lastError: unknown;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await performRequestAttempt(endpoint, requestOptions, queueEnabled, queueIdempotencyKey);
    } catch (error) {
      lastError = error;

      if (isNonRetryableRequestError(error, requestOptions)) throw error;

      const isLastAttempt = attempt === config.maxRetries;
      const shouldRetry = !isLastAttempt && isRetryableError(error, config);

      if (shouldRetry) {
        const delay = calculateBackoffDelay(attempt, config);
        // Log removed
        await sleep(delay, requestOptions.signal);
        continue;
      }

      if (queueEnabled && shouldQueueNetworkFailure(error)) {
        if (!queueIdempotencyKey) throw new OfflineQueueError('Offline queue idempotency key is missing');
        return enqueueOfflineMutation<T>(endpoint, requestOptions, queueIdempotencyKey);
      }

      throwRequestError(error);
    }
  }
  throw lastError;
};

// Replay gets a fresh Authorization/CSRF header from the Axios request
// interceptor. Tokens are never stored in IndexedDB/localStorage.
registerOfflineReplayHandler(async (mutation: OfflineMutation) => {
  const response = await apiInstance.request({
    url: mutation.endpoint,
    method: mutation.method,
    data: mutation.data,
    headers: { 'Idempotency-Key': mutation.idempotencyKey },
  });
  return response.data;
});

export const apiRequest = async <T = unknown>(
  endpoint: string,
  options: ApiRequestConfig = {},
  retryConfig: Partial<RetryConfig> = {}
): Promise<T> => {
  const dedupeKey = getRequestDedupeKey(endpoint, options);
  if (!dedupeKey) {
    return requestWithRetry<T>(endpoint, options, retryConfig);
  }

  const existing = inFlightGetRequests.get(dedupeKey);
  if (existing) return existing as Promise<T>;

  const request = requestWithRetry<T>(endpoint, options, retryConfig);
  inFlightGetRequests.set(dedupeKey, request);
  try {
    return await request;
  } finally {
    if (inFlightGetRequests.get(dedupeKey) === request) {
      inFlightGetRequests.delete(dedupeKey);
    }
  }
};

export const api = {
  get: <T = unknown>(endpoint: string, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(endpoint, { method: 'GET', ...config }),

  post: <T = unknown>(endpoint: string, data?: unknown, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(endpoint, { method: 'POST', data, ...config }),

  put: <T = unknown>(endpoint: string, data?: unknown, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(endpoint, { method: 'PUT', data, ...config }),

  patch: <T = unknown>(endpoint: string, data?: unknown, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(endpoint, { method: 'PATCH', data, ...config }),

  delete: <T = unknown>(endpoint: string, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(endpoint, { method: 'DELETE', ...config }),
};

export const uploadFile = async <T = unknown>(
  endpoint: string,
  file: File,
  additionalData?: Record<string, unknown>,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void,
  options: UploadFileOptions = {}
): Promise<T> => {
  const formData = new FormData();
  formData.append('file', file);

  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      if (value === undefined) return;
      if (typeof value === 'object' && value !== null) {
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, String(value));
      }
    });
  }

  return apiRequest<T>(
    endpoint,
    {
      method: 'POST',
      data: formData,
      onUploadProgress,
      signal: options.signal,
      headers: options.idempotencyKey
        ? { 'Idempotency-Key': options.idempotencyKey }
        : undefined,
    },
    options.retryConfig ?? { maxRetries: 0 }
  );
};

export const apiV1 = {
  get: <T = unknown>(endpoint: string, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'GET', ...config }),

  post: <T = unknown>(endpoint: string, data?: unknown, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'POST', data, ...config }),

  put: <T = unknown>(endpoint: string, data?: unknown, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'PUT', data, ...config }),

  patch: <T = unknown>(endpoint: string, data?: unknown, config?: ApiRequestConfig): Promise<T> =>
    apiRequest<T>(`${API_PREFIX}${endpoint}`, { method: 'PATCH', data, ...config }),

  delete: <T = unknown>(endpoint: string, config?: ApiRequestConfig): Promise<T> =>
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
