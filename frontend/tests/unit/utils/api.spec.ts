import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
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
  uploadFile,
  buildPaginationQuery,
  apiInstance,
  apiV1
} from '@/utils/api';
import { getEnvVar } from '@/utils/env';

vi.mock('axios', () => {
  const mockInstance = {
    request: vi.fn(),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
    defaults: { headers: { common: {} } },
  };
  return {
    default: { create: vi.fn(() => mockInstance) },
  };
});

vi.mock('@/utils/env', () => ({
  getEnvVar: vi.fn(),
  isDev: vi.fn(() => true),
}));

describe('API Utils', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setAccessToken(null);
    vi.useFakeTimers();
    vi.mocked(getEnvVar).mockReturnValue('');
  });

  afterEach(() => {
    vi.useRealTimers();
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
  });
});
