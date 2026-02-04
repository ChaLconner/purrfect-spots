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

// ========== Sentry Initialization ==========
// Only initialize in production or if explicitly enabled
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
const ENVIRONMENT = import.meta.env.MODE;

import type { App as VueApp } from 'vue';

async function initSentry(app: VueApp) {
  if (!SENTRY_DSN) {
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
        // Ignore browser extension errors
        if (
          event.message?.includes('Extension context invalidated') ||
          event.message?.includes('message channel closed') ||
          event.message?.includes('ResizeObserver loop')
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

await initSentry(app);

// Install Pinia BEFORE using any stores
app.use(pinia);

// Initialize auth state (now using Pinia store internally)
// Initialize auth by creating the store instance
const authStore = useAuthStore();
await authStore.initializeAuth();

// Handle browser extension conflicts globally
globalThis.addEventListener('unhandledrejection', handleUnhandledRejection);
globalThis.addEventListener('error', handleError);

// Global error handler for browser extension conflicts
app.config.errorHandler = (err, _instance, info) => {
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
app.mount('#app');

// Initialize Service Worker for offline support
if ('serviceWorker' in navigator && import.meta.env.MODE === 'production') {
  globalThis.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        // Check for updates

        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New version available
              }
            });
          }
        });
      })
      .catch((error) => {
        console.error('[SW] Service Worker registration failed:', error);
      });
  });
}

// Initialize Web Vitals tracking after app mount
try {
  const { initWebVitals } = await import('./utils/webVitals');
  initWebVitals();
} catch {
  // Web Vitals tracking is optional, don't break the app
}
