import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import AuthCallback from '@/views/AuthCallbackView.vue';
import { AuthService } from '@/services/authService';
import { showError, showSuccess } from '@/stores/toast';

const mockPush = vi.fn();
const mockRoute = {
  query: {} as Record<string, string>,
};
const mockSetAuth = vi.fn().mockResolvedValue(undefined);
const mockSessionExchange = vi.fn();
const validAccessToken = 'test-access-token';
const validRefreshToken = 'test-refresh-token';

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useRoute: () => mockRoute,
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    setAuth: mockSetAuth,
  }),
}));

vi.mock('@/stores/toast', () => ({
  showSuccess: vi.fn(),
  showError: vi.fn(),
}));

vi.mock('@/services/authService', () => ({
  AuthService: {
    googleCodeExchange: vi.fn(),
    syncUser: vi.fn(),
  },
}));

vi.mock('@/utils/api', () => ({
  apiV1: {
    post: (...args: unknown[]) => mockSessionExchange(...args),
  },
}));

describe('AuthCallback.vue', () => {
  const originalLocation = globalThis.location;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockSessionExchange.mockReset();
    mockRoute.query = {};
    sessionStorage.clear();

    Object.defineProperty(globalThis, 'location', {
      value: {
        hash: '',
      },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    Object.defineProperty(globalThis, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    });
  });

  it('redirects verified magic-link users to the stored safe path', async () => {
    globalThis.location.hash = `#access_token=${validAccessToken}&refresh_token=${validRefreshToken}&type=signup`;
    sessionStorage.setItem('redirectAfterAuth', '/my-reports');
    mockSessionExchange.mockResolvedValue({
      access_token: 'session-token',
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
    });

    mount(AuthCallback);
    await Promise.resolve();
    await Promise.resolve();
    vi.runAllTimers();

    expect(mockSessionExchange).toHaveBeenCalledWith('/auth/session-exchange', {
      access_token: validAccessToken,
      refresh_token: validRefreshToken,
    });
    expect(mockSetAuth).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith('/my-reports');
  });

  it('falls back to the default safe redirect when the stored path is unsafe', async () => {
    globalThis.location.hash = `#access_token=${validAccessToken}&refresh_token=${validRefreshToken}&type=signup`;
    sessionStorage.setItem('redirectAfterAuth', 'https://evil.example');
    mockSessionExchange.mockResolvedValue({
      access_token: 'session-token',
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
    });

    mount(AuthCallback);
    await Promise.resolve();
    await Promise.resolve();
    vi.runAllTimers();

    expect(mockPush).toHaveBeenCalledWith('/upload');
  });

  it('redirects recovery magic links to the password reset page', async () => {
    globalThis.location.hash = `#access_token=${validAccessToken}&refresh_token=${validRefreshToken}&type=recovery`;
    mockSessionExchange.mockResolvedValue({
      access_token: 'session-token',
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
    });

    mount(AuthCallback);
    await flushPromises();

    expect(showSuccess).toHaveBeenCalledWith('auth.callback.passwordResetVerified');
    expect(mockPush).toHaveBeenCalledWith('/reset-password');
  });

  it('exchanges Google callbacks and tolerates user-sync failures', async () => {
    mockRoute.query = { code: 'google-code' };
    sessionStorage.setItem('google_code_verifier', 'verifier');
    vi.mocked(AuthService.googleCodeExchange).mockResolvedValue({
      access_token: 'session-token',
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
    });
    vi.mocked(AuthService.syncUser).mockRejectedValue(new Error('sync unavailable'));

    mount(AuthCallback);
    await flushPromises();
    vi.runAllTimers();

    expect(AuthService.googleCodeExchange).toHaveBeenCalledWith('google-code', 'verifier');
    expect(AuthService.syncUser).toHaveBeenCalledOnce();
    expect(mockPush).toHaveBeenCalledWith('/upload');
  });

  it('reports missing Google callback credentials', async () => {
    mockRoute.query = { code: 'google-code' };

    mount(AuthCallback);
    await flushPromises();

    expect(showError).toHaveBeenCalledWith(
      'auth.callback.authDataNotFound',
      'auth.callback.loginFailedTitle'
    );
  });

  it.each([
    ['object errors', { message: 'invalid_grant' }, 'auth.callback.authExpired'],
    ['string errors', 'Failed to fetch', 'auth.callback.connectionError'],
  ])('normalizes %s from session exchange failures', async (_label, rejection, message) => {
    globalThis.location.hash = `#access_token=${validAccessToken}&refresh_token=${validRefreshToken}&type=signup`;
    mockSessionExchange.mockRejectedValue(rejection);

    mount(AuthCallback);
    await flushPromises();

    expect(showError).toHaveBeenCalledWith(message, 'auth.callback.loginFailedTitle');
  });

  it('stops retrying browser-extension failures after the configured limit', async () => {
    globalThis.location.hash = `#access_token=${validAccessToken}&refresh_token=${validRefreshToken}&type=signup`;
    mockSessionExchange.mockRejectedValue(new Error('message channel closed'));

    mount(AuthCallback);
    await vi.runAllTimersAsync();

    expect(mockSessionExchange).toHaveBeenCalledTimes(3);
    expect(showError).toHaveBeenCalledWith(
      'auth.callback.extensionError',
      'auth.callback.loginErrorTitle'
    );
  });

  it('decodes plus signs in OAuth error descriptions', async () => {
    globalThis.location.hash = '#error_description=Denied%2Bby%2Bprovider';

    mount(AuthCallback);
    await flushPromises();

    expect(showError).toHaveBeenCalledWith(
      'Denied by provider',
      'auth.callback.loginFailedTitle'
    );
  });
});
