<template>
  <div class="fixed inset-0 min-h-screen bg-transparent flex items-center justify-center z-50 pointer-events-none">
    <!-- Visual feedback removed as requested, toast handles success notification -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onErrorCaptured } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { AuthService } from '../services/authService';
import { useAuthStore } from '../store/authStore';
import { showError, showSuccess } from '../store/toast';

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
  window.addEventListener('unhandledrejection', (event) => {
    if (
      event.reason &&
      event.reason.message &&
      event.reason.message.includes('message channel closed')
    ) {
      event.preventDefault();
    }
  });
});



const handleAuthCallback = async () => {
  let retryCount = 0;
  const maxRetries = 3;
  
  while (retryCount < maxRetries) {
    try {
      const code = route.query.code as string;
      const codeVerifier = sessionStorage.getItem('google_code_verifier');
      
      
      if (!code) {
        throw new Error('Authentication code not found from Google');
      }
      
      if (!codeVerifier) {
        throw new Error('Authentication data not found. Please try logging in again.');
      }
      
      // Exchange code for tokens with retry logic
      const data = await AuthService.googleCodeExchange(code, codeVerifier);
      
      // Save authentication data
      useAuthStore().setAuth(data);
      
      // Sync user data with backend
      try {
        await AuthService.syncUser();
      } catch (syncError: any) {
        // Don't let sync error stop the login process
      }
      
      // Clean up
      sessionStorage.removeItem('google_code_verifier');
      
      success.value = true;
      showSuccess('Google Login Successful!');
      
      // Redirect to intended destination
      setTimeout(() => {
        const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/upload';
        sessionStorage.removeItem('redirectAfterAuth');
        router.push(redirectPath);
      }, 1000);
      
      return; // Success, exit retry loop
      
    } catch (err: any) {
      // Handle browser extension errors
      if (err.message && err.message.includes('message channel closed')) {
        retryCount++;
        if (retryCount < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
          continue;
        }
      }
      
      // Handle specific OAuth errors
      if (err.message && err.message.includes('invalid_grant')) {
        error.value = 'Authentication expired. Please try logging in again.';
      } else if (err.message && err.message.includes('redirect_uri')) {
        error.value = 'Invalid OAuth configuration. Please contact the administrator.';
      } else if (err.message === 'Failed to fetch') {
        error.value = 'Cannot connect to server. Please check your internet connection.';
      } else {
        error.value = err.message || 'An error occurred during login.';
      }
      break;
    }
  }
  
  if (retryCount >= maxRetries) {
    error.value = 'An error occurred from browser extensions. Please disable extensions and try again.';
    showError(error.value, 'Login Error');
  } else if (error.value) {
    showError(error.value, 'Login Failed');
  }

  // Redirect to login after a short delay if there was an error
  if (error.value) {
    setTimeout(() => {
      router.push('/login');
    }, 3000);
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
