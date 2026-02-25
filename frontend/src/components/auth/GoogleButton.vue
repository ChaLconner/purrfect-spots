<script setup lang="ts">
import { getEnvVar, isDev } from '../../utils/env';
import { showError } from '../../store/toast';
import { ref } from 'vue';
import { getGoogleAuthUrl } from '../../utils/oauth';

const isLoading = ref(false);

const handleGoogleLogin = async (): Promise<void> => {
  isLoading.value = true;

  try {
    const googleClientId = getEnvVar('VITE_GOOGLE_CLIENT_ID');

    if (!googleClientId) {
      throw new Error('Google OAuth is not configured. Please contact administrator.');
    }

    const redirectUri = `${globalThis.location.origin}/auth/callback`;
    const { url, codeVerifier } = await getGoogleAuthUrl(googleClientId, redirectUri);

    sessionStorage.setItem('google_code_verifier', codeVerifier);
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
</script>

<template>
  <button
    :disabled="isLoading"
    type="button"
    class="flex items-center justify-center gap-3 w-full py-[0.9rem] px-6 font-['Nunito'] text-base font-semibold text-[#5a4632] bg-white/90 border-2 border-[rgba(127,183,164,0.2)] rounded-2xl cursor-pointer transition-all duration-300 hover:not:disabled:bg-white hover:not:disabled:border-[rgba(127,183,164,0.4)] hover:not:disabled:shadow-[0_4px_12px_rgba(0,0,0,0.08)] disabled:opacity-60 disabled:cursor-not-allowed"
    @click="handleGoogleLogin"
  >
    <svg class="w-5 h-5" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
    {{ isLoading ? 'Connecting...' : 'Google' }}
  </button>
</template>
