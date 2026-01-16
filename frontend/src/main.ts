import { createApp } from 'vue'
import './styles/main.css'
import App from './App.vue'
import router from './router'
import { pinia } from './store'
import { useAuthStore } from './store/authStore'
import { isDev } from './utils/env'
import {
  handleUnhandledRejection,
  handleError,
  handleVueError
} from './utils/browserExtensionHandler'

// ========== Sentry Initialization ==========
// Only initialize in production or if explicitly enabled
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN
const ENVIRONMENT = import.meta.env.MODE

async function initSentry(app: any) {
  if (!SENTRY_DSN) {
    if (isDev()) {
      // eslint-disable-next-line no-console
      console.log('[Sentry] DSN not configured - error monitoring disabled')
    }
    return
  }

  try {
    // Dynamic import to reduce bundle size when Sentry is not used
    const Sentry = await import('@sentry/vue')
    
    Sentry.init({
      app,
      dsn: SENTRY_DSN,
      environment: ENVIRONMENT,
      
      // Performance monitoring
      tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,
      
      // Session replay (optional)
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
      
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
          return null
        }
        return event
      },
      
      // Add release version if available
      release: import.meta.env.VITE_APP_VERSION || '3.0.0',
    })
    
    // Make Sentry available globally for ErrorBoundary
    ;(window as any).Sentry = Sentry
    
    if (isDev()) {
      // eslint-disable-next-line no-console
      console.log(`[Sentry] Initialized for ${ENVIRONMENT} environment`)
    }
  } catch (error) {
    if (isDev()) {
      // eslint-disable-next-line no-console
      console.warn('[Sentry] Failed to initialize:', error)
    }
  }
}

const app = createApp(App)

// Initialize Sentry with app instance
initSentry(app)

// Install Pinia BEFORE using any stores
app.use(pinia)

// Initialize auth state (now using Pinia store internally)
// Initialize auth by creating the store instance
useAuthStore()


// Handle browser extension conflicts globally
window.addEventListener('unhandledrejection', handleUnhandledRejection);

window.addEventListener('error', handleError);

// Global error handler for browser extension conflicts
app.config.errorHandler = (err, instance, info) => {
  const result = handleVueError(err, info);
  
  // If handleVueError returned false, it means the error was handled
  if (result === false) {
    return;
  }
  
  // Report to Sentry if available
  if ((window as any).Sentry) {
    (window as any).Sentry.captureException(err, {
      extra: { info },
      tags: { handler: 'global' }
    })
  }
  
  // Log other errors normally
  if (isDev()) {
    // eslint-disable-next-line no-console
    console.error('Vue error:', err, info);
  }
};

app.use(router)
app.mount('#app')

// Initialize Web Vitals tracking after app mount
import('./utils/webVitals').then(({ initWebVitals }) => {
  initWebVitals();
}).catch(() => {
  // Web Vitals tracking is optional, don't break the app
});