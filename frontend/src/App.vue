<script setup lang="ts">
import NavBar from './components/NavBar.vue';
import ToastContainer from './components/toast/ToastContainer.vue';
import { onErrorCaptured, onMounted, ref } from 'vue';
import { isBrowserExtensionError, logBrowserExtensionError } from './utils/browserExtensionHandler';
import { showError } from './store/toast';
import { useAuthStore } from './store/authStore';
import { ApiError, ApiErrorTypes } from './utils/api';

// Track error counts for potential recovery
const errorCount = ref(0);
const MAX_ERRORS_BEFORE_REFRESH = 5;

onMounted(() => {
  useAuthStore().verifySession();
});

// Handle browser extension errors at the app level
onErrorCaptured((err, instance, info) => {
  // Reset error count periodically
  setTimeout(() => {
    errorCount.value = Math.max(0, errorCount.value - 1);
  }, 30000);
  
  // Handle browser extension errors silently
  if (isBrowserExtensionError(err)) {
    logBrowserExtensionError(err, 'App component');
    return false; // Suppress the error
  }
  
  errorCount.value++;
  
  // If too many errors, suggest refresh
  if (errorCount.value >= MAX_ERRORS_BEFORE_REFRESH) {
    showError('Multiple errors detected. Please refresh the page.', 'Application Error');
    return false;
  }
  
  // Handle API errors with user-friendly messages
  if (err instanceof ApiError) {
    switch (err.type) {
      case ApiErrorTypes.NETWORK_ERROR:
        showError('Unable to connect. Please check your internet connection.', 'Connection Error');
        break;
      case ApiErrorTypes.AUTHENTICATION_ERROR:
        showError('Your session has expired. Please log in again.', 'Session Expired');
        break;
      case ApiErrorTypes.SERVER_ERROR:
        showError('Server is temporarily unavailable. Please try again later.', 'Server Error');
        break;
      default:
        showError(err.message || 'An unexpected error occurred.', 'Error');
    }
    return false;
  }
  
  // Handle generic errors
  if (err instanceof Error) {
    // Don't show technical error messages to users
    const userMessage = err.message.toLowerCase().includes('failed') 
      ? 'Something went wrong. Please try again.'
      : err.message;
    showError(userMessage, 'Error');
  } else {
    showError('An unexpected error occurred.', 'Application Error');
  }

  // Log for debugging
  console.error('[App Error Boundary]', { error: err, component: instance, info });
  
  return false; // Prevent error propagation
});
</script>

<template>
  <div class="flex flex-col min-h-screen relative">
    <div class="ghibli-texture-overlay"></div>
    <NavBar />
    <ToastContainer />
    <main id="main-content" tabindex="-1" class="flex-1 overflow-auto flex flex-col focus:outline-none">
      <router-view />
    </main>
  </div>
</template>

