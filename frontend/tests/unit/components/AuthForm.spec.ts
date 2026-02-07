import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import AuthForm from '@/components/AuthForm.vue';
import { useRouter } from 'vue-router';
import { ref } from 'vue';
import { useAuthForm } from '@/composables/useAuthForm';
import { useAuthStore } from '@/store/authStore';

// Mock useRouter
vi.mock('vue-router', () => ({
  useRouter: vi.fn(),
}));

// Mock useAuthStore
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    isUserReady: false,
    verifySession: vi.fn(),
  })),
}));

// Mock useAuthForm composable
vi.mock('@/composables/useAuthForm', () => ({
  useAuthForm: vi.fn(),
}));

// Mock child components
const GhibliBackgroundStub = { template: '<div class="ghibli-bg-stub"></div>' };
const PasswordStrengthMeterStub = { template: '<div class="pwd-meter-stub"></div>' };

describe('AuthForm.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ push: vi.fn() });
    
    // Default mock implementation
    vi.mocked(useAuthForm).mockReturnValue({
      isLogin: ref(true),
      isLoading: ref(false),
      showPassword: ref(false),
      form: { email: '', password: '', name: '' },
      toggleMode: vi.fn(),
      handleSubmit: vi.fn(),
      handleGoogleLogin: vi.fn(),
      errors: {},
      isFormValid: ref(true)
    } as any);

    // Default mock for AuthStore
    vi.mocked(useAuthStore).mockReturnValue({
      isUserReady: false,
      verifySession: vi.fn(),
    } as any);
  });

  it('should render login form by default', () => {
    const wrapper = mount(AuthForm, {
      props: { initialMode: 'login' },
      global: {
        stubs: {
          GhibliBackground: GhibliBackgroundStub,
          PasswordStrengthMeter: PasswordStrengthMeterStub
        }
      }
    });

    expect(wrapper.find('h1').text()).toBe('Welcome Back!');
    expect(wrapper.find('input[type="email"]').exists()).toBe(true);
    expect(wrapper.find('input#name').exists()).toBe(false);
    expect(wrapper.find('.submit-btn').text()).toContain('Sign In');
  });

  it('should render register form when initialMode is register', () => {
     vi.mocked(useAuthForm).mockReturnValue({
      isLogin: ref(false),
      isLoading: ref(false),
      showPassword: ref(false),
      form: { email: '', password: '', name: '' },
      toggleMode: vi.fn(),
      handleSubmit: vi.fn(),
      handleGoogleLogin: vi.fn(),
      errors: {},
      isFormValid: ref(true)
    } as any);

    const wrapper = mount(AuthForm, {
      props: { initialMode: 'register' },
      global: {
        stubs: {
          GhibliBackground: GhibliBackgroundStub,
          PasswordStrengthMeter: PasswordStrengthMeterStub
        }
      }
    });

    expect(wrapper.find('h1').text()).toBe('Join Us!');
    expect(wrapper.find('input#name').exists()).toBe(true);
    expect(wrapper.find('.submit-btn').text()).toContain('Create Account');
  });

  it('should sync internal mode when initialMode prop changes', async () => {
    const isLoginRef = ref(true);
    // Capture ref to assertion
    vi.mocked(useAuthForm).mockReturnValue({
      isLogin: isLoginRef,
      isLoading: ref(false),
      showPassword: ref(false),
      form: { email: '', password: '', name: '' },
      toggleMode: vi.fn(),
      handleSubmit: vi.fn(),
      handleGoogleLogin: vi.fn(),
      errors: {},
      isFormValid: ref(true)
    } as any);

    const wrapper = mount(AuthForm, {
      props: { initialMode: 'login' },
      global: { stubs: { GhibliBackground: GhibliBackgroundStub, PasswordStrengthMeter: PasswordStrengthMeterStub } }
    });

    await wrapper.setProps({ initialMode: 'register' });
    expect(isLoginRef.value).toBe(false);

    await wrapper.setProps({ initialMode: 'login' });
    expect(isLoginRef.value).toBe(true);
  });

  it('should redirect if user is already logged in on mount', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isUserReady: true,
      verifySession: vi.fn(),
    } as any);

    const mockRouterPush = vi.fn();
    (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ push: mockRouterPush });

    mount(AuthForm, {
      props: { initialMode: 'login' },
      global: { stubs: { GhibliBackground: GhibliBackgroundStub, PasswordStrengthMeter: PasswordStrengthMeterStub } }
    });

    expect(mockRouterPush).toHaveBeenCalledWith('/upload');
  });

  it('should redirect to custom path if redirectAfterAuth is set', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isUserReady: true,
    } as any);

    const mockRouterPush = vi.fn();
    (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ push: mockRouterPush });
    
    globalThis.sessionStorage.setItem('redirectAfterAuth', '/gallery');
 
    mount(AuthForm, {
      global: { stubs: { GhibliBackground: GhibliBackgroundStub, PasswordStrengthMeter: PasswordStrengthMeterStub } }
    });

    expect(mockRouterPush).toHaveBeenCalledWith('/gallery');
    globalThis.sessionStorage.removeItem('redirectAfterAuth');
  });

  it('should toggle password visibility', async () => {
    const showPassword = ref(false);
    vi.mocked(useAuthForm).mockReturnValue({
      isLogin: ref(true),
      isLoading: ref(false),
      showPassword,
      form: { email: '', password: '', name: '' },
      handleSubmit: vi.fn(),
    } as any);

    const wrapper = mount(AuthForm, {
      global: { stubs: { GhibliBackground: GhibliBackgroundStub, PasswordStrengthMeter: PasswordStrengthMeterStub } }
    });

    const toggleBtn = wrapper.find('.password-toggle-btn');
    await toggleBtn.trigger('click');
    expect(showPassword.value).toBe(true);
    
    await toggleBtn.trigger('click');
    expect(showPassword.value).toBe(false);
  });

  it('should handle form submission', async () => {
    const handleSubmit = vi.fn();
    vi.mocked(useAuthForm).mockReturnValue({
      isLogin: ref(true),
      isLoading: ref(false),
      showPassword: ref(false),
      form: { email: 'test@example.com', password: 'password', name: '' },
      handleSubmit,
    } as any);

    const wrapper = mount(AuthForm, {
      global: { stubs: { GhibliBackground: GhibliBackgroundStub, PasswordStrengthMeter: PasswordStrengthMeterStub } }
    });

    await wrapper.find('form').trigger('submit');
    expect(handleSubmit).toHaveBeenCalled();
  });

  it('should handle Google login', async () => {
    const handleGoogleLogin = vi.fn();
    vi.mocked(useAuthForm).mockReturnValue({
      isLogin: ref(true),
      isLoading: ref(false),
      showPassword: ref(false),
      form: { email: '', password: '', name: '' },
      handleGoogleLogin,
    } as any);

    const wrapper = mount(AuthForm, {
      global: { stubs: { GhibliBackground: GhibliBackgroundStub, PasswordStrengthMeter: PasswordStrengthMeterStub } }
    });

    await wrapper.find('.google-btn').trigger('click');
    expect(handleGoogleLogin).toHaveBeenCalled();
  });
});
