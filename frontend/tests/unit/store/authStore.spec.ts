import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAuthStore } from '@/store/authStore';

// Mock dependencies
const mockApiPost = vi.fn();
const mockSetAccessToken = vi.fn();
const mockSetAuthCallbacks = vi.fn();

vi.mock('@/utils/api', () => ({
  apiV1: {
    post: (...args: any[]) => mockApiPost(...args),
  },
  setAccessToken: (...args: any[]) => mockSetAccessToken(...args),
  setAuthCallbacks: (...args: any[]) => mockSetAuthCallbacks(...args),
  ApiError: class extends Error {
      statusCode: number;
      constructor(message: string, statusCode: number) {
          super(message);
          this.statusCode = statusCode;
      }
  }
}));

vi.mock('@/services/profileService', () => ({
  ProfileService: {
    getProfile: vi.fn(),
  },
}));

const mockChannel = {
  on: vi.fn().mockReturnThis(),
  subscribe: vi.fn().mockReturnThis(),
  topic: 'realtime:user_balance_1'
};

vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn(() => mockChannel),
    removeChannel: vi.fn(),
  },
}));

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    
    // Setup localStorage mock
    const storageMock = (() => {
      let store: Record<string, string> = {};
      return {
        getItem: vi.fn((key: string) => store[key] || null),
        setItem: vi.fn((key: string, value: string) => {
          store[key] = value.toString();
        }),
        removeItem: vi.fn((key: string) => {
          delete store[key];
        }),
        clear: vi.fn(() => {
          store = {};
        }),
        key: vi.fn(),
        length: 0
      };
    })();

    Object.defineProperty(globalThis, 'localStorage', {
      value: storageMock,
      writable: true
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('initializes with default state', () => {
    const store = useAuthStore();
    expect(store.user).toBeNull();
    expect(store.token).toBeNull();
    expect(store.isAuthenticated).toBe(false);
  });

  it('setAuth updates state and localStorage', async () => {
    const store = useAuthStore();
    const loginResponse = {
      access_token: 'fake-token',
      token_type: 'bearer',
      user: { 
        id: '1', 
        email: 'test@example.com', 
        name: 'Test User',
        created_at: new Date().toISOString()
      },
    };

    await store.setAuth(loginResponse);

    expect(store.user).toMatchObject(loginResponse.user);
    expect(store.user?.permissions).toEqual([]);
    expect(store.token).toBe('fake-token');
    expect(store.isAuthenticated).toBe(true);
    expect(localStorage.getItem('user_data')).toBeTruthy();
    expect(mockSetAccessToken).toHaveBeenCalledWith('fake-token');
  });

  it('logout clears state and calls API', async () => {
    const store = useAuthStore();
    store.token = 'fake-token';
    store.isAuthenticated = true;

    await store.logout();

    expect(mockApiPost).toHaveBeenCalledWith('/auth/logout');
    expect(store.user).toBeNull();
    expect(store.token).toBeNull();
    expect(store.isAuthenticated).toBe(false);
    expect(mockSetAccessToken).toHaveBeenCalledWith(null);
  });

  it('initializeAuth restores user from localStorage and tries refresh', async () => {
    const user = { id: '1', email: 'stored@example.com', name: 'Stored User' };
    localStorage.setItem('user_data', JSON.stringify(user));
    mockApiPost.mockResolvedValueOnce({ access_token: 'new-token', user });

    const store = useAuthStore();
    await store.initializeAuth();

    expect(store.user).toMatchObject(user);
    expect(store.user?.permissions).toEqual([]);
    expect(store.isAuthenticated).toBe(true);
    expect(store.isInitialized).toBe(true);
    expect(store.token).toBe('new-token');
    expect(mockApiPost).toHaveBeenCalledWith('/auth/refresh-token');
  });

  it('initializeAuth waits for refresh when no cached user exists', async () => {
    const freshUser = { id: '1', email: 'fresh@example.com', name: 'Fresh User' };
    mockApiPost.mockResolvedValueOnce({ access_token: 'fresh-token', user: freshUser });

    const store = useAuthStore();
    await store.initializeAuth();

    expect(store.isInitialized).toBe(true);
    expect(store.isAuthenticated).toBe(true);
    expect(store.token).toBe('fresh-token');
    expect(store.user).toMatchObject(freshUser);
    expect(store.user?.permissions).toEqual([]);
  });

  it('verifySession returns true if authenticated and profile fetch succeeds', async () => {
    const { ProfileService } = await import('@/services/profileService');
    vi.mocked(ProfileService.getProfile).mockResolvedValue({ id: '1' } as any);
    
    const store = useAuthStore();
    store.isAuthenticated = true;
    
    const result = await store.verifySession();
    expect(result).toBe(true);
    expect(ProfileService.getProfile).toHaveBeenCalled();
  });

  it('verifySession tries refreshToken if profile fetch fails', async () => {
    const { ProfileService } = await import('@/services/profileService');
    vi.mocked(ProfileService.getProfile).mockRejectedValue(new Error('Auth failed'));
    mockApiPost.mockResolvedValueOnce({ access_token: 'new-token' });
    
    const store = useAuthStore();
    store.isAuthenticated = true;
    
    const result = await store.verifySession();
    expect(result).toBe(true);
    expect(mockApiPost).toHaveBeenCalledWith('/auth/refresh-token');
  });

  it('refreshToken handles parallel calls', async () => {
    mockApiPost.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ access_token: 'token' }), 50)));
    const store = useAuthStore();
    
    const [res1, res2] = await Promise.all([store.refreshToken(), store.refreshToken()]);
    
    expect(res1).toBe(true);
    expect(res2).toBe(true);
    expect(mockApiPost).toHaveBeenCalledTimes(1);
  });

  it('refreshToken handles errors with justLoggedIn check', async () => {
    vi.useFakeTimers();
    const now = Date.now();
    vi.setSystemTime(now);
    
    mockApiPost.mockRejectedValue(new Error('Fail'));
    const store = useAuthStore();
    store.isAuthenticated = true;
    store.lastLoginTime = now;
    
    // Within 5 seconds
    const res = await store.refreshToken();
    expect(res).toBe(false);
    expect(store.isAuthenticated).toBe(true);
    
    // After 6 seconds
    vi.setSystemTime(now + 6000);
    const res2 = await store.refreshToken();
    expect(res2).toBe(false);
    expect(store.isAuthenticated).toBe(false);
  });

  it('refreshToken clears cached auth when backend returns no access token', async () => {
    mockApiPost.mockResolvedValueOnce({ access_token: null, token_type: null, message: 'No active session' });

    const store = useAuthStore();
    store.isAuthenticated = true;
    store.user = { id: '1', email: 'stored@example.com', name: 'Stored User' } as any;

    const result = await store.refreshToken();

    expect(result).toBe(false);
    expect(store.isAuthenticated).toBe(false);
    expect(store.user).toBeNull();
    expect(store.token).toBeNull();
  });

  it('updateUser updates state and localStorage', () => {
    const store = useAuthStore();
    store.user = { id: '1', email: 'a@a.com', name: 'Old' } as any;
    
    store.updateUser({ name: 'New' });
    
    expect(store.user?.name).toBe('New');
    expect(JSON.parse(localStorage.getItem('user_data')!).name).toBe('New');
  });

  it('getAuthHeader returns correct header', () => {
    const store = useAuthStore();
    expect(store.getAuthHeader()).toEqual({});
    
    store.token = 'my-token';
    expect(store.getAuthHeader()).toEqual({ Authorization: 'Bearer my-token' });
  });

  it('getters return expected values', () => {
    const store = useAuthStore();
    store.user = { id: '1', email: 'test@example.com', name: 'John', picture: 'pic.jpg' } as any;
    store.isAuthenticated = true;

    expect(store.hasCompleteProfile).toBe(true);
    expect(store.isUserReady).toBe(true);
    expect(store.userDisplayName).toBe('John');
    expect(store.userAvatar).toBe('pic.jpg');

    store.user!.name = '';
    expect(store.userDisplayName).toBe('test@example.com');
    
    store.user!.picture = '';
    expect(store.userAvatar).toBe('/default-avatar.svg');
  });

  it('treats legacy admin permission aliases as admin access', async () => {
    mockApiPost.mockResolvedValueOnce({
      access_token: 'legacy-admin-token',
      user: {
        id: '1',
        email: 'admin@example.com',
        name: 'Legacy Admin',
        created_at: new Date().toISOString(),
        permissions: ['admin_access'],
      },
    });

    const store = useAuthStore();
    await store.refreshToken();

    expect(store.hasPermission('access:admin')).toBe(true);
    expect(store.isAdmin).toBe(true);

    const cachedUser = JSON.parse(localStorage.getItem('user_data') || '{}');
    expect(cachedUser.permissions).toContain('access:admin');
  });

  it('treats any recognized admin permission as admin shell access', async () => {
    mockApiPost.mockResolvedValueOnce({
      access_token: 'moderation-token',
      user: {
        id: '2',
        email: 'mod@example.com',
        name: 'Moderator',
        created_at: new Date().toISOString(),
        permissions: ['reports:read'],
        role: 'user',
      },
    });

    const store = useAuthStore();
    await store.refreshToken();

    expect(store.hasPermission('reports:read')).toBe(true);
    expect(store.isAdmin).toBe(true);
  });
});
