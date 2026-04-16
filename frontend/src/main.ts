import { createApp } from 'vue';
import './styles/main.css';
import App from './App.vue';
import router from './router';
import { pinia } from './store';
import { useAuthStore } from './store/authStore';
import { isDev } from './utils/env';
import {
  handleUnhandledRejection,
  handleError,
  handleVueError,
} from './utils/browserExtensionHandler';
import i18n from './i18n';

// ========== Sentry Initialization ==========
// Only initialize in production or if explicitly enabled
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
const ENVIRONMENT = import.meta.env.MODE;
const ENABLE_SENTRY = ENVIRONMENT === 'production' || import.meta.env.VITE_ENABLE_SENTRY === 'true';

import type { App as VueApp } from 'vue';

async function initSentry(app: VueApp): Promise<void> {
  if (!SENTRY_DSN || !ENABLE_SENTRY) {
    return;
  }

  try {
    // Dynamic import to reduce bundle size when Sentry is not used
    const Sentry = await import('@sentry/vue');

    Sentry.init({
      app,
      dsn: SENTRY_DSN,
      environment: ENVIRONMENT,

      // Performance monitoring
      tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1,

      // Session replay (optional)
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1,

      // Don't send PII
      sendDefaultPii: false,

      // Filter out common non-actionable errors
      beforeSend(event) {
        const serializedEvent = JSON.stringify(event);
        // Ignore browser extension errors
        if (
          event.message?.includes('Extension context invalidated') ||
          event.message?.includes('message channel closed') ||
          event.message?.includes('ResizeObserver loop') ||
          event.message?.includes('Element not found')
        ) {
          return null;
        }
        if (
          serializedEvent.includes('webdriver') ||
          serializedEvent.includes('playwright') ||
          serializedEvent.includes('vitest') ||
          serializedEvent.includes('jsdom')
        ) {
          return null;
        }
        return event;
      },

      // Add release version if available
      release: import.meta.env.VITE_APP_VERSION || '3.0.0',
    });

    // Make Sentry available globally for ErrorBoundary
    const win = globalThis as unknown as Window & { Sentry?: typeof Sentry };
    win.Sentry = Sentry;
  } catch {
    // Sentry init failed
  }
}

const app = createApp(App);

// Non-blocking initialization
initSentry(app); 

// Install Pinia BEFORE using any stores
app.use(pinia);

// Initialize auth state asynchronously to prevent blocking FCP/LCP
const authStore = useAuthStore();
authStore.initializeAuth().catch((e) => {
  console.warn('[Auth] Failed to initialize auth:', e);
});

// Handle browser extension conflicts globally
globalThis.addEventListener('unhandledrejection', handleUnhandledRejection);
globalThis.addEventListener('error', handleError);

// Handle Vite dynamic import (preload) errors
// This occurs when the browser tries to fetch a JS chunk that no longer exists on the server
// (common after a new deployment). The best recovery is a full page reload.
globalThis.addEventListener('vite:preloadError', () => {
  window.location.reload();
});

// Global error handler for browser extension conflicts
app.config.errorHandler = (err, _instance, info): void => {
  const result = handleVueError(err, info);

  // If handleVueError returned false, it means the error was handled
  if (result === false) {
    return;
  }

  // Report to Sentry if available
  const win = globalThis as unknown as Window & {
    Sentry?: {
      captureException: (
        err: unknown,
        context: { extra: { info: string }; tags: { handler: string } }
      ) => void;
    };
  };
  if (win.Sentry) {
    win.Sentry.captureException(err, {
      extra: { info },
      tags: { handler: 'global' },
    });
  }

  // Log other errors normally
  if (isDev()) {
    console.error('Vue error:', err, info);
  }
};

app.use(router);
app.use(i18n);

// Mount immediately - router will handle initial navigation internally
app.mount('#app');

// Web Vitals tracking is handled below

// Initialize Web Vitals tracking after app mount
try {
  const { initWebVitals } = await import('./utils/webVitals');
  initWebVitals();
} catch {
  // Web Vitals tracking is optional, don't break the app
}
