<template>
  <div
    class="fixed inset-0 min-h-screen bg-transparent flex items-center justify-center z-50 pointer-events-none"
  ></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onErrorCaptured } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { AuthService } from '../services/authService';
import { useAuthStore } from '../store/authStore';
import { showError, showSuccess } from '../store/toast';
import type { LoginResponse } from '../types/auth';

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

const handleMagicLink = async (hash: string) => {
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
    showSuccess(type === 'recovery' ? 'Password Reset Verified' : 'Email Verified Successfully!');

    if (type === 'recovery') {
      router.push('/reset-password');
    } else {
      setTimeout(() => router.push('/upload'), 1000);
    }
    return true;
  }
  return false;
};

const handleGoogleCode = async (code: string, codeVerifier: string) => {
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
    const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/upload';
    sessionStorage.removeItem('redirectAfterAuth');
    router.push(redirectPath);
  }, 1000);
  return true;
};

const handleAuthError = (err: unknown) => {
  if (err.message?.includes('invalid_grant')) {
    error.value = 'Authentication expired. Please try logging in again.';
  } else if (err.message?.includes('redirect_uri')) {
    error.value = 'Invalid OAuth configuration. Please contact the administrator.';
  } else if (err.message === 'Failed to fetch') {
    error.value = 'Cannot connect to server. Please check your internet connection.';
  } else if (err instanceof Error && err.message) {
    const msg = err.message;
    error.value = msg.includes('status code') ? 'Service temporarily unavailable.' : msg;
  } else {
    error.value = 'An error occurred during login.';
  }
};

const processAuthCallback = async () => {
  const code = route.query.code as string;
  const codeVerifier = globalThis.sessionStorage.getItem('google_code_verifier');
  const hash = globalThis.location.hash;

  if (hash && hash.includes('access_token=')) {
    if (await handleMagicLink(hash)) return true;
  }

  if (code) {
    if (!codeVerifier)
      throw new Error('Authentication data not found. Please try logging in again.');
    if (await handleGoogleCode(code, codeVerifier)) return true;
  } else if (!hash) {
    throw new Error('No authentication data received.');
  }

  if (hash && !hash.includes('access_token=')) {
    const params = new URLSearchParams(hash.substring(1));
    const errorMsg = params.get('error_description');
    if (errorMsg) throw new Error(errorMsg.replaceAll('+', ' '));
  }
  return false;
};

const handleAuthCallback = async () => {
  let retryCount = 0;
  const maxRetries = 3;

  while (retryCount < maxRetries) {
    try {
      if (await processAuthCallback()) return;
      break;
    } catch (err: unknown) {
      if (err.message?.includes('message channel closed')) {
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
    error.value =
      'An error occurred from browser extensions. Please disable extensions and try again.';
    showError(error.value, 'Login Error');
  } else if (error.value) {
    showError(error.value, 'Login Failed');
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
