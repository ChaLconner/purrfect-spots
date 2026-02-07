import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthService } from '@/services/authService';
import { apiV1, ApiError, ApiErrorTypes } from '@/utils/api';

vi.mock('@/utils/api', () => ({
  apiV1: {
    get: vi.fn(),
    post: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    type: string;
    statusCode?: number;
    constructor(type: string, message: string, statusCode?: number) {
      super(message);
      this.type = type;
      this.statusCode = statusCode;
    }
  },
  ApiErrorTypes: {
    AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
  }
}));

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getCurrentUser should call /auth/me', async () => {
    const mockUser = { id: '1', email: 'test@example.com' };
    vi.mocked(apiV1.get).mockResolvedValue(mockUser);

    const user = await AuthService.getCurrentUser();
    expect(apiV1.get).toHaveBeenCalledWith('/auth/me');
    expect(user).toEqual(mockUser);
  });

  it('login should call /auth/login with credentials', async () => {
    const mockResponse = { user: { id: '1' }, access_token: 'token' };
    vi.mocked(apiV1.post).mockResolvedValue(mockResponse);

    const res = await AuthService.login('test@example.com', 'password');
    expect(apiV1.post).toHaveBeenCalledWith('/auth/login', { email: 'test@example.com', password: 'password' });
    expect(res).toEqual(mockResponse);
  });

  it('signup should call /auth/register', async () => {
    vi.mocked(apiV1.post).mockResolvedValue({});
    await AuthService.signup('test@example.com', 'password', 'Test User');
    expect(apiV1.post).toHaveBeenCalledWith('/auth/register', { email: 'test@example.com', password: 'password', name: 'Test User' });
  });

  it('verifyOtp should call /auth/verify-otp', async () => {
    vi.mocked(apiV1.post).mockResolvedValue({});
    await AuthService.verifyOtp('test@example.com', '123456');
    expect(apiV1.post).toHaveBeenCalledWith('/auth/verify-otp', { email: 'test@example.com', otp: '123456' });
  });

  it('resendOtp should call /auth/resend-otp', async () => {
    vi.mocked(apiV1.post).mockResolvedValue({});
    await AuthService.resendOtp('test@example.com');
    expect(apiV1.post).toHaveBeenCalledWith('/auth/resend-otp', { email: 'test@example.com' });
  });

  it('logout should call /auth/logout', async () => {
    vi.mocked(apiV1.post).mockResolvedValue({});
    await AuthService.logout();
    expect(apiV1.post).toHaveBeenCalledWith('/auth/logout');
  });

  describe('verifyToken', () => {
    it('should return true if getCurrentUser succeeds', async () => {
      vi.mocked(apiV1.get).mockResolvedValue({ id: '1' });
      const result = await AuthService.verifyToken();
      expect(result).toBe(true);
    });

    it('should return false if getCurrentUser fails', async () => {
      vi.mocked(apiV1.get).mockRejectedValue(new Error('Unauthorized'));
      const result = await AuthService.verifyToken();
      expect(result).toBe(false);
    });
  });

  describe('googleCodeExchange', () => {
    it('should call /auth/google/exchange with correct payload', async () => {
      vi.mocked(apiV1.post).mockResolvedValue({ user: { id: '1' } });
      const res = await AuthService.googleCodeExchange('code', 'verifier');
      expect(apiV1.post).toHaveBeenCalledWith('/auth/google/exchange', expect.objectContaining({
        code: 'code',
        code_verifier: 'verifier',
      }));
      expect(res).toEqual({ user: { id: '1' } });
    });

    it('should throw enhanced error for invalid_grant', async () => {
      const error = new ApiError(ApiErrorTypes.AUTHENTICATION_ERROR, 'invalid_grant', 400);
      vi.mocked(apiV1.post).mockRejectedValue(error);

      await expect(AuthService.googleCodeExchange('code', 'verifier'))
        .rejects.toThrow('Authentication expired. Please try signing in again.');
    });

    it('should throw enhanced error for redirect_uri mismatch', async () => {
      const error = new ApiError(ApiErrorTypes.AUTHENTICATION_ERROR, 'redirect_uri_mismatch', 400);
      vi.mocked(apiV1.post).mockRejectedValue(error);

      await expect(AuthService.googleCodeExchange('code', 'verifier'))
        .rejects.toThrow('Redirect URI mismatch. Please check your OAuth configuration.');
    });

    it('should rethrow other ApiErrors', async () => {
      const error = new ApiError(ApiErrorTypes.SERVER_ERROR, 'Something else', 500);
      vi.mocked(apiV1.post).mockRejectedValue(error);

      await expect(AuthService.googleCodeExchange('code', 'verifier'))
        .rejects.toThrow('Something else');
    });
  });

  it('syncUser should call /auth/sync-user', async () => {
    vi.mocked(apiV1.post).mockResolvedValue({ id: '1' });
    await AuthService.syncUser();
    expect(apiV1.post).toHaveBeenCalledWith('/auth/sync-user');
  });
});
