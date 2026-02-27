<template>
  <div
    class="fixed inset-0 min-h-screen bg-transparent flex items-center justify-center z-50 pointer-events-none"
  ></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onErrorCaptured } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { AuthService } from '../services/authService';
import { useAuthStore } from '../store/authStore';
import { showError, showSuccess } from '../store/toast';
import { getSafeRedirect } from '../utils/security';
import type { LoginResponse } from '../types/auth';

const { t } = useI18n();

const router = useRouter();
const route = useRoute();

const isLoading = ref(true);
const error = ref('');
const success = ref(false);

// Error handling for browser extension conflicts
onErrorCaptured((err) => {
  // Ignore extension-related errors
  if (err.message && err.message.includes('message channel closed')) {
    return false; // Prevent the error from propagating
  }
  return true; // Let other errors propagate normally
});

// Handle unhandled promise rejections (often from extensions)
onMounted(() => {
  globalThis.addEventListener('unhandledrejection', (event) => {
    if (
      event.reason &&
      event.reason.message &&
      event.reason.message.includes('message channel closed')
    ) {
      event.preventDefault();
    }
  });
});

const handleMagicLink = async (hash: string): Promise<boolean> => {
  const params = new URLSearchParams(hash.substring(1));
  const accessToken = params.get('access_token');
  const refreshToken = params.get('refresh_token');
  const type = params.get('type');

  if (accessToken && refreshToken) {
    const { apiV1 } = await import('../utils/api');
    const response = await apiV1.post<LoginResponse>('/auth/session-exchange', {
      access_token: accessToken,
      refresh_token: refreshToken,
    });

    await useAuthStore().setAuth(response);
    success.value = true;
    showSuccess(
      type === 'recovery'
        ? t('auth.callback.passwordResetVerified')
        : t('auth.callback.emailVerified')
    );

    if (type === 'recovery') {
      router.push('/reset-password');
    } else {
      setTimeout(() => router.push('/upload'), 1000);
    }
    return true;
  }
  return false;
};

const handleGoogleCode = async (code: string, codeVerifier: string): Promise<boolean> => {
  const data = await AuthService.googleCodeExchange(code, codeVerifier);
  useAuthStore().setAuth(data);

  try {
    await AuthService.syncUser();
  } catch {
    // Ignore sync errors
  }

  globalThis.sessionStorage.removeItem('google_code_verifier');
  success.value = true;

  setTimeout(() => {
    const redirectPath = sessionStorage.getItem('redirectAfterAuth');
    sessionStorage.removeItem('redirectAfterAuth');
    router.push(getSafeRedirect(redirectPath));
  }, 1000);
  return true;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleAuthError = (err: any): void => {
  if (err.message?.includes('invalid_grant')) {
    error.value = t('auth.callback.authExpired');
  } else if (err.message?.includes('redirect_uri')) {
    error.value = t('auth.callback.invalidOauth');
  } else if (err.message === 'Failed to fetch') {
    error.value = t('auth.callback.connectionError');
  } else if (err instanceof Error && err.message) {
    const msg = err.message;
    error.value = msg.includes('status code') ? t('auth.callback.serviceUnavailable') : msg;
  } else {
    error.value = t('auth.callback.generalError');
  }
};

const processAuthCallback = async (): Promise<boolean> => {
  const code = route.query.code as string;
  const codeVerifier = globalThis.sessionStorage.getItem('google_code_verifier');
  const hash = globalThis.location.hash;

  if (hash && hash.includes('access_token=')) {
    if (await handleMagicLink(hash)) return true;
  }

  if (code) {
    if (!codeVerifier) throw new Error(t('auth.callback.authDataNotFound'));
    if (await handleGoogleCode(code, codeVerifier)) return true;
  } else if (!hash) {
    throw new Error(t('auth.callback.noAuthData'));
  }

  if (hash && !hash.includes('access_token=')) {
    const params = new URLSearchParams(hash.substring(1));
    const errorMsg = params.get('error_description');
    if (errorMsg) throw new Error(decodeURIComponent(errorMsg.replace(/\+/g, ' ')));
  }
  return false;
};

const handleAuthCallback = async (): Promise<void> => {
  let retryCount = 0;
  const maxRetries = 3;

  while (retryCount < maxRetries) {
    try {
      if (await processAuthCallback()) return;
      break;
    } catch (err: unknown) {
      if (err instanceof Error && err.message?.includes('message channel closed')) {
        retryCount++;
        if (retryCount < maxRetries) {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          continue;
        }
      }
      handleAuthError(err);
      break;
    }
  }

  if (retryCount >= maxRetries) {
    error.value = t('auth.callback.extensionError');
    showError(error.value, t('auth.callback.loginErrorTitle'));
  } else if (error.value) {
    showError(error.value, t('auth.callback.loginFailedTitle'));
  }

  if (error.value) {
    setTimeout(() => router.push('/login'), 3000);
  }
};

onMounted(async () => {
  try {
    await handleAuthCallback();
  } finally {
    isLoading.value = false;
  }
});
</script>
