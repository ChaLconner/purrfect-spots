import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AuthCallback from '@/components/AuthCallback.vue';

const mockPush = vi.fn();
const mockRoute = {
  query: {} as Record<string, string>,
};
const mockSetAuth = vi.fn().mockResolvedValue(undefined);
const mockSessionExchange = vi.fn();
const validAccessToken = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature';
const validRefreshToken = 'eyJhbGciOiJIUzI1NiJ9.eyJ0eXBlIjoicmVmcmVzaCJ9.signature';

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

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    setAuth: mockSetAuth,
  }),
}));

vi.mock('@/store/toast', () => ({
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
});
