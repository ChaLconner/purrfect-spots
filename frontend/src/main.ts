import { createApp } from 'vue';
import './styles/main.css';
import App from './App.vue';
import router from './router';
import { pinia } from './store';
import { isDev } from './utils/env';
import {
  handleUnhandledRejection,
  handleError,
  handleVueError,
} from './utils/browserExtensionHandler';
import i18n, { initializeI18n } from './i18n';

// ========== Sentry Initialization ==========
// Sentry is opt-in so production builds without monitoring enabled do not ship the SDK chunk.
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
const ENVIRONMENT = import.meta.env.MODE;
const ENABLE_SENTRY = import.meta.env.VITE_ENABLE_SENTRY === 'true';
const ENABLE_SENTRY_REPLAY = import.meta.env.VITE_SENTRY_REPLAY_ENABLED === 'true';

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
      replaysSessionSampleRate: ENABLE_SENTRY_REPLAY ? 0.1 : 0,
      replaysOnErrorSampleRate: ENABLE_SENTRY_REPLAY ? 1 : 0,

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

// Install Pinia BEFORE using any stores
app.use(pinia);

// Handle browser extension conflicts globally
globalThis.addEventListener('unhandledrejection', handleUnhandledRejection);
globalThis.addEventListener('error', handleError);

const recoverFromStaleChunk = (): void => {
  const reloadKey = 'purrfect-spots:stale-chunk-reload';
  const now = Date.now();
  const lastReload = Number(sessionStorage.getItem(reloadKey) || '0');

  if (now - lastReload < 30_000) {
    return;
  }

  sessionStorage.setItem(reloadKey, String(now));
  const url = new URL(window.location.href);
  url.searchParams.set('__reload', String(now));
  window.location.replace(url.toString());
};

// Handle Vite dynamic import (preload) errors.
// A stale HTML shell can point at old hashed chunks after deploy; cache-bust once
// so Ctrl+Shift+R gets a fresh module graph instead of looping on old assets.
globalThis.addEventListener('vite:preloadError', (event) => {
  event.preventDefault();
  recoverFromStaleChunk();
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

const schedulePostPaintTask = (task: () => void): void => {
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    window.requestIdleCallback(() => task(), { timeout: 1500 });
    return;
  }

  setTimeout(task, 0);
};

const loadDeferredStylesheet = (href: string): void => {
  if (typeof document === 'undefined') {
    return;
  }

  const existingStylesheet = document.querySelector(`link[rel="stylesheet"][href="${href}"]`);
  if (existingStylesheet) {
    return;
  }

  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = href;
  // Silently handle font CDN failures (e.g. Google Fonts 404s) so they
  // don't surface as unhandled resource errors in the console.
  link.onerror = (): void => {
    if (isDev()) {
      console.warn(`[Fonts] Failed to load stylesheet: ${href}`);
    }
  };
  document.head.appendChild(link);
};

// Continue non-critical boot work after first paint.
schedulePostPaintTask(() => {
  void initializeI18n();
  void initSentry(app);
  import('./utils/webVitals')
    .then(({ initWebVitals }) => initWebVitals())
    .catch(() => {
      // Web Vitals tracking is optional, don't break the app
    });
});

// Kick off auth initialization immediately so the background session check
// starts as soon as possible, reducing skeleton visibility time.
queueMicrotask(() => {
  import('./store/authStore')
    .then(({ useAuthStore }) => useAuthStore().initializeAuth())
    .catch((e) => {
      console.warn('[Auth] Failed to initialize auth:', e);
    });
});

schedulePostPaintTask(() => {
  loadDeferredStylesheet(
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
  );
  loadDeferredStylesheet(
    'https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap'
  );
});
