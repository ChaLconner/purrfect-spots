import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAuthForm } from '@/composables/useAuthForm';
import { useAuthStore } from '@/store/authStore';
import { AuthService } from '@/services/authService';
import { showSuccess, showError } from '@/store/toast';
import { useRouter } from 'vue-router';
import { setActivePinia, createPinia } from 'pinia';
import { defineComponent } from 'vue';
import { mount } from '@vue/test-utils';

// Mock dependencies
vi.mock('@/services/authService');
vi.mock('@/store/toast');
vi.mock('vue-router', () => ({
  useRouter: vi.fn(),
}));
vi.mock('@/utils/env', () => ({
  getEnvVar: vi.fn((key) => 'mock-env-value'),
  isDev: vi.fn(() => true),
}));
vi.mock('@/utils/oauth', () => ({
  getGoogleAuthUrl: vi.fn().mockResolvedValue({ url: 'http://google.com/auth', codeVerifier: 'xyz' }),
}));

describe('useAuthForm', () => {
  let mockRouter: { push: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    setActivePinia(createPinia());
    mockRouter = { push: vi.fn() };
    (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
    
    // Mock localStorage
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
        length: 0,
      };
    })();

    Object.defineProperty(globalThis, 'localStorage', {
      value: storageMock,
      writable: true,
      configurable: true,
    });

    vi.clearAllMocks();
  });

  const createTestComponent = (initialMode: 'login' | 'register' = 'login') => defineComponent({
    setup() {
      return useAuthForm(initialMode);
    },
    render() {
      return null;
    },
  });

  describe('Initial State', () => {
    it('should initialize correctly for login mode', () => {
      const wrapper = mount(createTestComponent('login'));
      const vm = wrapper.vm;

      expect(vm.isLogin).toBe(true);
      expect(vm.form).toEqual({ email: '', password: '', name: '' });
      expect(vm.isLoading).toBe(false);
    });

    it('should initialize correctly for register mode', () => {
      const wrapper = mount(createTestComponent('register'));
      const vm = wrapper.vm;

      expect(vm.isLogin).toBe(false);
    });
  });

  describe('Validation', () => {
    it('should validate required fields', async () => {
      const wrapper = mount(createTestComponent('login'));
      const vm = wrapper.vm as any;
      
      await vm.handleSubmit();
      expect(vm.formErrors.email).toBe('Email is required');
      expect(vm.formErrors.password).toBe('Password is required');
      expect(AuthService.login).not.toHaveBeenCalled();
    });

    it('should validate password length for registration', async () => {
      const wrapper = mount(createTestComponent('register'));
      const vm = wrapper.vm as any;
      
      vm.form.name = 'Test User';
      vm.form.email = 'test@example.com';
      vm.form.password = 'short';
      
      await vm.handleSubmit();
      expect(vm.formErrors.password).toBe('Password must be at least 8 characters');
    });
  });

  describe('Submit Logic', () => {
    it('should handle successful login', async () => {
      const wrapper = mount(createTestComponent('login'));
      const vm = wrapper.vm;

      vm.form.email = 'test@example.com';
      vm.form.password = 'password123';
      
      const mockAuthData = { 
        user: { name: 'Test User' }, 
        access_token: 'token' 
      };
      (AuthService.login as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(mockAuthData);

      await vm.handleSubmit();

      expect(useAuthStore().user).toEqual(mockAuthData.user);
      expect(showSuccess).toHaveBeenCalled();
      expect(mockRouter.push).toHaveBeenCalledWith('/upload');
    });

    it('should handle successful registration', async () => {
      const wrapper = mount(createTestComponent('register'));
      const vm = wrapper.vm;

      vm.form.name = 'New User';
      vm.form.email = 'new@example.com';
      vm.form.password = 'password123';
      
      const mockAuthData = { 
        user: { name: 'New User' }, 
        access_token: 'token' 
      };
      (AuthService.signup as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(mockAuthData);

      await vm.handleSubmit();

      expect(useAuthStore().user).toEqual(mockAuthData.user);
      expect(showSuccess).toHaveBeenCalled();
      expect(mockRouter.push).toHaveBeenCalledWith('/upload');
    });

    it('should handle API errors', async () => {
      const wrapper = mount(createTestComponent('login'));
      const vm = wrapper.vm;

      vm.form.email = 'test@example.com';
      vm.form.password = 'password123';
      
      (AuthService.login as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Invalid credentials'));

      await vm.handleSubmit();

      expect(showError).toHaveBeenCalledWith('Invalid credentials', 'Authentication Failed');
      expect(vm.isLoading).toBe(false);
    });
  });

  describe('Google Login', () => {
    it('should initiate Google login', async () => {
      // Mock window.location.href
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { href: '', origin: 'http://localhost:3000' } as any;

      const wrapper = mount(createTestComponent('login'));
      const vm = wrapper.vm;

      await vm.handleGoogleLogin();

      expect(window.location.href).toBe('http://google.com/auth'); // from mock
      
      // Restore
      window.location = originalLocation;
    });
  });
});
