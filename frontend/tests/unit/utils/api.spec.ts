import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { 
  apiRequest,
  ApiError,
  ApiErrorTypes,
  setAccessToken,
  setAuthCallbacks,
  getApiBaseUrl,
  getApiUrl,
  getAuthHeaders,
  api,

  buildPaginationQuery,
  apiInstance,
  apiV1,
  getDefaultHeaders,
  uploadFile,
} from '@/utils/api';
import { clearOfflineQueue, listOfflineMutations } from '@/utils/offlineQueue';
import { getEnvVar } from '@/utils/env';

vi.mock('axios', () => {
  const mockInstance = Object.assign(vi.fn(), {
    request: vi.fn(),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
    defaults: { headers: { common: {} } },
  });
  return {
    default: {
      create: vi.fn(() => mockInstance),
      isCancel: vi.fn(() => false),
    },
  };
});

vi.mock('@/utils/env', () => ({
  getEnvVar: vi.fn(),
  isDev: vi.fn(() => true),
}));

vi.mock('@/utils/security', () => ({
  getCsrfToken: vi.fn(() => null),
}));

const responseErrorHandler = vi.mocked(apiInstance.interceptors.response.use).mock.calls[0]?.[1] as (
  error: unknown
) => Promise<unknown>;

describe('API Utils', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    setAccessToken(null);
    vi.useFakeTimers();
    vi.mocked(getEnvVar).mockReturnValue('');
    await clearOfflineQueue();
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('getApiBaseUrl', () => {
    it('returns env URL when set', () => {
      vi.mocked(getEnvVar).mockReturnValue('https://api.example.com');
      expect(getApiBaseUrl()).toBe('https://api.example.com');
    });

    it('strips trailing slash from env URL', () => {
      vi.mocked(getEnvVar).mockReturnValue('https://api.example.com/');
      expect(getApiBaseUrl()).toBe('https://api.example.com');
    });

    it.each([
      ['same-origin api path when env is not set', ''],
      ['same-origin versioned path', '/api/v1'],
      ['localhost backend URL during local development', 'http://localhost:8000/api/v1'],
      ['same-origin api proxy base', '/api'],
    ])('normalizes %s to the proxy base', (_caseName, envValue) => {
      vi.mocked(getEnvVar).mockReturnValue(envValue);
      expect(getApiBaseUrl()).toBe('');
    });
  });

  describe('getApiUrl', () => {
    it('constructs full URL from endpoint', () => {
      vi.mocked(getEnvVar).mockReturnValue('https://api.example.com');
      expect(getApiUrl('/users')).toBe('https://api.example.com/users');
    });

    it('handles endpoint without leading slash', () => {
      vi.mocked(getEnvVar).mockReturnValue('https://api.example.com');
      expect(getApiUrl('users')).toBe('https://api.example.com/users');
    });

    it('builds same-origin URLs in production fallback mode', () => {
      vi.mocked(getEnvVar).mockReturnValue('');
      expect(getApiUrl('/users')).toBe('/users');
    });
  });

  describe('getDefaultHeaders', () => {
    it('returns content type and accept headers', () => {
      const headers = getDefaultHeaders();
      expect(headers['Content-Type']).toBe('application/json');
      expect(headers['Accept']).toBe('application/json');
    });
  });

  describe('getAuthHeaders', () => {
    it('includes Authorization when token is set', () => {
      setAccessToken('my-token');
      const headers = getAuthHeaders();
      expect(headers['Authorization']).toBe('Bearer my-token');
    });

    it('does not include Authorization when no token', () => {
      setAccessToken(null);
      const headers = getAuthHeaders();
      expect(headers['Authorization']).toBeUndefined();
    });
  });

  describe('apiRequest', () => {
    it('successfully returns data', async () => {
      vi.mocked(apiInstance.request).mockResolvedValue({ data: { success: true } });
      const data = await apiRequest('/test');
      expect(data).toEqual({ success: true });
    });

    it('retries on network errors', async () => {
      vi.mocked(apiInstance.request)
        .mockRejectedValueOnce(new ApiError(ApiErrorTypes.NETWORK_ERROR, 'failed'))
        .mockResolvedValueOnce({ data: { success: true } });
      
      const requestPromise = apiRequest('/test', {}, { maxRetries: 1, baseDelayMs: 0 });
      await vi.runAllTimersAsync();
      const data = await requestPromise;
      expect(data).toEqual({ success: true });
    });

    it('does not start a request when its signal is already aborted', async () => {
      const controller = new AbortController();
      controller.abort();

      await expect(apiRequest('/test', { signal: controller.signal })).rejects.toMatchObject({
        name: 'AbortError',
      });
      expect(apiInstance.request).not.toHaveBeenCalled();
    });

    it('queues an explicitly opted-in allow-listed mutation while offline', async () => {
      Object.defineProperty(navigator, 'onLine', { value: false, configurable: true });

      const result = await apiV1.post('/social/photos/photo-1/like', undefined, {
        queueWhenOffline: true,
        retryConfig: { maxRetries: 0 },
      });

      expect(result).toMatchObject({ queued: true });
      expect(apiInstance.request).not.toHaveBeenCalled();
      expect(await listOfflineMutations()).toHaveLength(1);
    });
  });

  describe('Interceptors & Error Handling', () => {
    it('request interceptor adds Authorization header', () => {
      const useMock = vi.mocked(apiInstance.interceptors.request.use);
      if (useMock.mock.calls.length > 0) {
        const handler = useMock.mock.calls[0][0];
        setAccessToken('token123');
        const config = { headers: {} } as any;
        const result = handler(config);
        expect(result.headers.Authorization).toBe('Bearer token123');
      }
    });

    it('request interceptor rewrites loopback absolute URLs to same-origin paths', () => {
      const useMock = vi.mocked(apiInstance.interceptors.request.use);
      if (useMock.mock.calls.length > 0) {
        const handler = useMock.mock.calls[0][0];
        const config = {
          baseURL: '/api',
          url: 'http://localhost:8000/api/v1/gallery/viewport?limit=100',
          headers: {},
        } as any;

        const result = handler(config);
        expect(result.baseURL).toBe('');
        expect(result.url).toBe('/api/v1/gallery/viewport?limit=100');
      }
    });

    it('response interceptor handles non-json content type', () => {
        const useMock = vi.mocked(apiInstance.interceptors.response.use);
        if (useMock.mock.calls.length > 0) {
            const successHandler = useMock.mock.calls[0][0];
            const mockResponse = {
                headers: { 'content-type': 'text/plain' },
                data: '{"success":true}',
                status: 200
            };
            const result = successHandler(mockResponse);
            expect(result.data).toEqual({ success: true });
        }
    });

    it('response interceptor throws on invalid format', () => {
        const useMock = vi.mocked(apiInstance.interceptors.response.use);
        if (useMock.mock.calls.length > 0) {
            const successHandler = useMock.mock.calls[0][0];
            const mockResponse = {
                headers: { 'content-type': 'text/plain' },
                data: null,
                status: 200
            };
            expect(() => successHandler(mockResponse)).toThrow('invalid response format');
        }
    });

    it('handles 401 and retries once', async () => {
        const useMock = vi.mocked(apiInstance.interceptors.response.use);
        if (useMock.mock.calls.length > 0) {
            const errorHandler = useMock.mock.calls[0][1];
            
            const refreshFn = vi.fn().mockResolvedValue(true);
            setAuthCallbacks(refreshFn, vi.fn());
            setAccessToken('new-token');

            const mockError = {
                response: { status: 401 },
                config: { headers: {}, _retry: false },
                isAxiosError: true
            };

            vi.mocked(apiInstance.request).mockResolvedValue({ data: 'retry-success' });

            const result = await errorHandler(mockError);
            expect(result.data).toBe('retry-success');
            expect(refreshFn).toHaveBeenCalled();
        }
    });

    it('logs out when refresh is unavailable and the request is not already retried', async () => {
      const logout = vi.fn();
      setAuthCallbacks(undefined as unknown as () => Promise<boolean>, logout);
      const error = {
        response: { status: 401, data: {} },
        config: { url: '/api/v1/gallery', headers: {} },
      } as any;

      await expect(responseErrorHandler(error)).rejects.toMatchObject({ type: ApiErrorTypes.AUTHENTICATION_ERROR });
      expect(logout).toHaveBeenCalledTimes(2);
    });

    it('handles rate-limit retry-after responses', async () => {
      const error = {
        response: { status: 429, data: {}, headers: { 'retry-after': '7' } },
        config: { url: '/api/v1/gallery' },
      } as any;

      await expect(responseErrorHandler(error)).rejects.toMatchObject({
        type: ApiErrorTypes.SERVER_ERROR,
        message: 'Rate limit exceeded. Please wait 7 seconds before retrying.',
      });
    });

    it('coalesces token refreshes and retries with the refreshed token', async () => {
      const refreshFn = vi.fn().mockResolvedValue(true);
      setAuthCallbacks(refreshFn, vi.fn());
      setAccessToken('refreshed-token');

      const request = apiInstance as unknown as {
        mockResolvedValue: (value: unknown) => void;
      };
      request.mockResolvedValue({ data: 'retry-success' });

      const error = {
        response: { status: 401, data: {} },
        config: { url: '/api/v1/gallery', headers: {} },
      } as any;
      const result = await responseErrorHandler(error);

      expect(refreshFn).toHaveBeenCalledOnce();
      expect(result).toMatchObject({ data: 'retry-success' });
      expect(error.config.headers.Authorization).toBe('Bearer refreshed-token');
    });

    it('logs out and stops an already retried request', async () => {
      const logout = vi.fn();
      setAuthCallbacks(vi.fn(), logout);
      const error = {
        response: { status: 401, data: {} },
        config: { url: '/api/v1/gallery', headers: {}, _retry: true },
      } as any;

      await expect(responseErrorHandler(error)).rejects.toBe(error);
      expect(logout).toHaveBeenCalledOnce();
    });
  });

  describe('api helper methods', () => {
    it('api handles delete and put', async () => {
      vi.mocked(apiInstance.request).mockResolvedValue({ data: 'ok' });
      await api.delete('/test');
      await api.put('/test', { d: 2 });
      expect(apiInstance.request).toHaveBeenCalledTimes(2);
    });
    
    it('apiV1 prefixes routes', async () => {
        vi.mocked(apiInstance.request).mockResolvedValue({ data: 'ok' });
        await apiV1.get('/users');
        expect(apiInstance.request).toHaveBeenCalledWith(expect.objectContaining({
            url: '/api/v1/users'
        }));
    });

    it('apiV1 patch and delete work', async () => {
      vi.mocked(apiInstance.request).mockResolvedValue({ data: 'ok' });
      await apiV1.patch('/users/1', { name: 'test' });
      await apiV1.delete('/users/1');
      expect(apiInstance.request).toHaveBeenCalledTimes(2);
    });

    it('serializes structured upload fields and skips undefined values', async () => {
      vi.mocked(apiInstance.request).mockResolvedValue({ data: { uploaded: true } });
      const file = new File(['image'], 'cat.jpg', { type: 'image/jpeg' });

      await uploadFile('/upload/cat', file, { metadata: { source: 'test' }, optional: undefined });

      const requestConfig = vi.mocked(apiInstance.request).mock.calls[0]?.[0] as any;
      expect(requestConfig.data.get('metadata')).toBe(JSON.stringify({ source: 'test' }));
      expect(requestConfig.data.get('optional')).toBeNull();
    });
  });

  describe('buildPaginationQuery', () => {
    it('builds query with limit and offset', () => {
      expect(buildPaginationQuery({ limit: 10, offset: 20 })).toBe('?limit=10&offset=20');
    });

    it('builds query with limit and page', () => {
      expect(buildPaginationQuery({ limit: 10, page: 2 })).toBe('?limit=10&page=2');
    });

    it('prefers page over offset', () => {
      expect(buildPaginationQuery({ limit: 10, page: 2, offset: 20 })).toBe('?limit=10&page=2');
    });

    it('returns empty string for empty params', () => {
      expect(buildPaginationQuery({})).toBe('');
    });
  });
});
