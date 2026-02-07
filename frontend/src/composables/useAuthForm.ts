import { reactive, ref } from 'vue';
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
  const isLoading = ref(false);
  const showPassword = ref(false);

  const form = reactive({
    email: '',
    password: '',
    name: '',
  });

  const toggleMode = () => {
    isLogin.value = !isLogin.value;
  };

  const validateForm = (): boolean => {
    const fields = isLogin.value
      ? [form.email, form.password]
      : [form.name, form.email, form.password];

    if (fields.some((f) => !f?.trim())) {
      showError('Please fill in all fields');
      return false;
    }

    if (!isLogin.value && form.password.length < 8) {
      showError('Password must be at least 8 characters');
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    isLoading.value = true;

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
      showSuccess(`Welcome back, ${data.user.name || 'Traveler'}!`, 'Authentication Successful');

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
      isLoading.value = false;
    }
  };

  const handleGoogleLogin = async () => {
    isLoading.value = true;

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
      isLoading.value = false;
    }
  };

  return {
    isLogin,
    isLoading,
    showPassword,
    form,
    toggleMode,
    handleSubmit,
    handleGoogleLogin,
  };
}
