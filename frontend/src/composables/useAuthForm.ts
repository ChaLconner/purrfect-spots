import { reactive, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/authStore';
import { AuthService } from '@/services/authService';
import { showSuccess, showError } from '@/store/toast';
import { isDev, getEnvVar } from '@/utils/env';
import { getGoogleAuthUrl } from '@/utils/oauth';

export function useAuthForm(initialMode: 'login' | 'register' = 'login') {
  const router = useRouter();
  const authStore = useAuthStore();

  const isLogin = ref(initialMode === 'login');
  const isEmailLoading = ref(false);
  const isGoogleLoading = ref(false);
  const isLoading = computed(() => isEmailLoading.value || isGoogleLoading.value);
  const showPassword = ref(false);

  const form = reactive({
    email: '',
    password: '',
    name: '',
  });

  const toggleMode = () => {
    isLogin.value = !isLogin.value;
  };

  const formErrors = reactive({
    email: '',
    password: '',
    name: '',
  });

  const clearErrors = () => {
    formErrors.email = '';
    formErrors.password = '';
    formErrors.name = '';
  };

  const validateForm = (): boolean => {
    clearErrors();
    let isValid = true;

    if (!form.email?.trim()) {
      formErrors.email = 'Email is required';
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      formErrors.email = 'Invalid email format';
      isValid = false;
    }

    if (!form.password?.trim()) {
      formErrors.password = 'Password is required';
      isValid = false;
    } else if (!isLogin.value && form.password.length < 8) {
      formErrors.password = 'Password must be at least 8 characters';
      isValid = false;
    }

    if (!isLogin.value && !form.name?.trim()) {
      formErrors.name = 'Full name is required';
      isValid = false;
    }

    return isValid;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    isEmailLoading.value = true;

    try {
      let data;
      if (isLogin.value) {
        data = await AuthService.login(form.email, form.password);
      } else {
        data = await AuthService.signup(form.email, form.password, form.name);
      }

      // Handle email verification case
      if (data.requires_verification && data.email) {
        showSuccess(
          'Please check your email for the verification code.',
          'Registration Successful'
        );
        router.push({
          name: 'VerifyEmail',
          query: { email: data.email },
        });
        return;
      }

      // Handle legacy/fallback
      if (!data.access_token && data.message) {
        showSuccess(data.message, 'Registration Successful');
        isLogin.value = true;
        return;
      }

      authStore.setAuth(data);
      showSuccess(`Welcome back, ${data.user.name || 'Traveler'}!`, 'Successful');

      const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/upload';
      sessionStorage.removeItem('redirectAfterAuth');
      router.push(redirectPath);
    } catch (err: unknown) {
      let message = err instanceof Error ? err.message : 'Something went wrong';

      // Sanitize technical errors
      if (message.includes('status code 401')) message = 'Invalid email or password';
      if (message.includes('status code')) message = 'Service unavailable. Please try again later.';

      showError(message, 'Authentication Failed');
    } finally {
      isEmailLoading.value = false;
    }
  };

  const handleGoogleLogin = async () => {
    isGoogleLoading.value = true;

    try {
      const googleClientId = getEnvVar('VITE_GOOGLE_CLIENT_ID');

      if (!googleClientId) {
        throw new Error('Google OAuth is not configured. Please contact administrator.');
      }

      const redirectUri = `${globalThis.location.origin}/auth/callback`;
      const { url, codeVerifier } = await getGoogleAuthUrl(googleClientId, redirectUri);

      globalThis.sessionStorage.setItem('google_code_verifier', codeVerifier);
      globalThis.location.href = url;
    } catch (err: unknown) {
      if (isDev()) {
        console.error('Google OAuth Error:', err);
      }
      let message = err instanceof Error ? err.message : 'Google sign-in failed';
      if (message.includes('status code')) message = 'Unable to connect to Google service.';
      showError(message, 'Google Login Error');
    } finally {
      // Note: If redirecting, isLoading might not be relevant but it's good practice
      // in case the error handler or pre-redirect logic takes time.
      isGoogleLoading.value = false;
    }
  };

  return {
    isLogin,
    isLoading,
    isEmailLoading,
    isGoogleLoading,
    showPassword,
    form,
    formErrors,
    toggleMode,
    handleSubmit,
    handleGoogleLogin,
  };
}
