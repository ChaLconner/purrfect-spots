<script setup lang="ts">
/**
 * ErrorBoundary Component
 *
 * Global error boundary for catching and displaying errors gracefully.
 * Wraps content and provides fallback UI when errors occur.
 */
import { ref, onErrorCaptured, provide } from 'vue';
import { useRouter } from 'vue-router';

interface Props {
  fallbackMessage?: string;
  showRetry?: boolean;
  showHome?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  fallbackMessage: 'Something went wrong. Please try again.',
  showRetry: true,
  showHome: true,
});

const emit = defineEmits<{
  (e: 'error', error: Error): void;
  (e: 'retry'): void;
}>();

const router = useRouter();
const hasError = ref(false);
const errorMessage = ref('');
const errorStack = ref('');
const isDev = import.meta.env.DEV;

// Capture errors from child components
onErrorCaptured((error: Error, instance, info) => {
  console.error('[ErrorBoundary] Caught error:', error);
  console.error('[ErrorBoundary] Component:', instance);
  console.error('[ErrorBoundary] Info:', info);

  // Ignore browser extension errors
  if (
    error.message?.includes('message channel closed') ||
    error.message?.includes('Extension context invalidated') ||
    error.message?.includes('ResizeObserver loop')
  ) {
    return false; // Don't show error UI for these
  }

  hasError.value = true;
  errorMessage.value = error.message || props.fallbackMessage;
  errorStack.value = error.stack || '';

  // Report to Sentry if available
  interface WindowWithSentry extends Window {
    Sentry?: {
      captureException: (error: Error, options?: Record<string, unknown>) => void;
    };
  }
  const win = globalThis as unknown as WindowWithSentry;
  if (typeof globalThis !== 'undefined' && win.Sentry) {
    win.Sentry.captureException(error, {
      extra: {
        componentInfo: info,
        componentName:
          (instance as { $options?: { name?: string } } | null)?.$options?.name || 'Unknown',
        timestamp: new Date().toISOString(),
      },
      tags: {
        errorBoundary: 'true',
        environment: import.meta.env.MODE,
      },
    });
  }

  emit('error', error);

  // Prevent error from propagating (unless in test)
  return import.meta.env.MODE === 'test';
});

function handleRetry() {
  hasError.value = false;
  errorMessage.value = '';
  errorStack.value = '';
  emit('retry');
}

function handleGoHome() {
  hasError.value = false;
  router.push('/');
}

function handleReload() {
  globalThis.location.reload();
}

// Provide error state to children if needed
provide('errorBoundary', {
  hasError,
  triggerError: (msg: string) => {
    hasError.value = true;
    errorMessage.value = msg;
  },
  clearError: () => {
    hasError.value = false;
    errorMessage.value = '';
  },
});
</script>

<template>
  <!-- Error State -->
  <div
    v-if="hasError"
    class="error-boundary min-h-[400px] flex items-center justify-center p-8"
    role="alert"
    aria-live="assertive"
  >
    <div class="error-content max-w-md w-full text-center">
      <!-- Error Icon -->
      <div class="animate-shake mb-6">
        <div class="w-20 h-20 mx-auto bg-red-100 rounded-full flex items-center justify-center">
          <svg
            class="w-10 h-10 text-red-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
      </div>

      <!-- Error Title -->
      <h2 class="text-2xl font-heading font-bold text-gray-800 mb-3">Oops! Something went wrong</h2>

      <!-- Error Message -->
      <p class="text-gray-600 mb-6 font-body">
        {{ fallbackMessage }}
      </p>

      <!-- Debug Info (Development Only) -->
      <details v-if="errorStack && isDev" class="text-left mb-6 bg-gray-100 rounded-lg p-4">
        <summary class="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
          Technical Details
        </summary>
        <pre class="mt-2 text-xs text-red-600 overflow-x-auto whitespace-pre-wrap"
          >{{ errorMessage }}

        {{ errorStack }}</pre
        >
      </details>

      <!-- Action Buttons -->
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <button
          v-if="showRetry"
          class="px-6 py-3 bg-terracotta text-white rounded-full font-medium hover:bg-terracotta-dark transition-colors focus:outline-none focus:ring-2 focus:ring-terracotta focus:ring-offset-2"
          @click="handleRetry"
        >
          <span class="flex items-center justify-center gap-2">
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Try Again
          </span>
        </button>

        <button
          v-if="showHome"
          class="px-6 py-3 bg-white text-gray-700 rounded-full font-medium border border-gray-300 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
          @click="handleGoHome"
        >
          Go Home
        </button>

        <button
          class="px-6 py-3 text-gray-500 hover:text-gray-700 transition-colors text-sm underline"
          @click="handleReload"
        >
          Reload Page
        </button>
      </div>
    </div>
  </div>

  <!-- Normal Content -->
  <slot v-else></slot>
</template>
