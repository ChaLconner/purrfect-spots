<script setup lang="ts">
import NavBar from './components/NavBar.vue';
import BottomNav from './components/layout/BottomNav.vue';
import LicenseOverlay from './components/layout/LicenseOverlay.vue';
import ToastContainer from './components/toast/ToastContainer.vue';
import { onErrorCaptured, onMounted, ref } from 'vue';
import { isBrowserExtensionError, logBrowserExtensionError } from './utils/browserExtensionHandler';
import { showError } from './store/toast';
import { useAuthStore } from './store/authStore';
import { ApiError, ApiErrorTypes } from './utils/api';
import { useNetwork } from './composables/useNetwork';
import { ErrorBoundary } from './components/ui';
import { useStructuredData } from './composables/useStructuredData';

import { useWebVitals } from './composables/usePerformance';
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const { isOnline } = useNetwork();
const route = useRoute();

const showNav = computed(() => {
  return !route.path.startsWith('/admin');
});
const errorCount = ref(0);
const MAX_ERRORS_BEFORE_REFRESH = 5;

// Initialize Web Vitals monitoring
useWebVitals();

// Global SEO Schema
useStructuredData({
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'Purrfect Spots',
  url: 'https://purrfectspots.xyz',
  potentialAction: {
    '@type': 'SearchAction',
    target: 'https://purrfectspots.xyz/search?q={search_term_string}',
    'query-input': 'required name=search_term_string',
  },
  publisher: {
    '@type': 'Organization',
    name: 'Purrfect Spots Community',
    logo: {
      '@type': 'ImageObject',
      url: 'https://purrfectspots.xyz/cat-icon-512.png',
    },
  },
});

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
    let userMessage = err.message;

    // Check for technical keywords
    const technicalKeywords = [
      'failed',
      'undefined',
      'null',
      'read properties',
      'status code',
      'json',
    ];
    const isTechnical = technicalKeywords.some((keyword) =>
      userMessage.toLowerCase().includes(keyword)
    );

    if (isTechnical) {
      userMessage = 'Something went wrong. Please refresh and try again.';
    }

    showError(userMessage, 'Error');
  } else {
    showError('An unexpected error occurred.', 'Application Error');
  }

  // Log for debugging
  console.error('[App Error Boundary]', { error: err, component: instance, info });

  // Allow propagation in test environment for better debugging
  if (import.meta.env.MODE === 'test') {
    return true;
  }

  return false; // Prevent error propagation
});
</script>

<template>
  <div class="flex flex-col min-h-screen relative">
    <div class="ghibli-texture-overlay"></div>
    <NavBar v-if="showNav" />

    <!-- Offline Indicator -->
    <div
      v-if="!isOnline"
      class="bg-amber-100 border-b border-amber-200 text-amber-800 px-4 py-2 text-center text-sm font-medium z-50 animate-fade-in"
      role="alert"
    >
      <span class="mr-2">📡</span>
      You are currently offline. Some features may be unavailable.
    </div>

    <ToastContainer />
    <main
      id="main-content"
      role="main"
      tabindex="-1"
      class="flex-1 overflow-auto flex flex-col focus:outline-none w-full pb-20 xl:pb-0"
    >
      <ErrorBoundary>
        <router-view />
      </ErrorBoundary>
      <LicenseOverlay />
    </main>

    <BottomNav v-if="showNav" />
  </div>
</template>
