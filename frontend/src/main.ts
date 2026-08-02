import { createApp } from 'vue';
import './styles/main.css';
import App from './App.vue';
import router from './router';
import { pinia } from './stores';
import { isDev } from './utils/env';
import {
  handleVueError,
  reloadWithCacheBust,
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
        // Ignore browser extension errors
        if (
          event.message?.includes('Extension context invalidated') ||
          event.message?.includes('message channel closed') ||
          event.message?.includes('ResizeObserver loop') ||
          event.message?.includes('Element not found')
        ) {
          return null;
        }
        const searchableText = [
          event.message,
          event.request?.url,
          ...(event.exception?.values ?? []).map((value) => value.value),
          ...Object.values(event.tags ?? {}),
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        if (['webdriver', 'playwright', 'vitest', 'jsdom'].some((term) => searchableText.includes(term))) {
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

// Handle Vite dynamic import (preload) errors.
// A stale HTML shell can point at old hashed chunks after deploy; cache-bust once
// so Ctrl+Shift+R gets a fresh module graph instead of looping on old assets.
globalThis.addEventListener('vite:preloadError', (event) => {
  event.preventDefault();
  reloadWithCacheBust();
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
const schedulePostPaintTask = (task: () => void): void => {
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    window.requestIdleCallback(() => task(), { timeout: 1500 });
    return;
  }

  setTimeout(task, 0);
};

// Load selected locale before mount, preventing translated views from flashing keys.
async function mountWhenLocaleReady(): Promise<void> {
  try {
    await initializeI18n();
  } catch {
    // Mount with fallback locale if locale chunk cannot be fetched.
  }
  app.mount('#app');
}

void mountWhenLocaleReady();


// Continue non-critical boot work after first paint.
schedulePostPaintTask(() => {
  void initSentry(app);
  import('./utils/webVitals')
    .then(({ initWebVitals }) => initWebVitals())
    .catch(() => {
      // Web Vitals tracking is optional, don't break the app
    });
});
