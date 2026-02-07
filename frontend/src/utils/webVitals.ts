/**
 * Web Vitals Tracking Utility
 *
 * Tracks Core Web Vitals metrics for performance monitoring:
 * - LCP (Largest Contentful Paint)
 * - FID (First Input Delay)
 * - CLS (Cumulative Layout Shift)
 * - FCP (First Contentful Paint)
 * - TTFB (Time to First Byte)
 * - INP (Interaction to Next Paint)
 */

import { isDev } from './env';

// Web Vitals metric types
export interface WebVitalMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  entries: PerformanceEntry[];
}

// Threshold values for rating
const thresholds = {
  LCP: { good: 2500, poor: 4000 },
  FID: { good: 100, poor: 300 },
  CLS: { good: 0.1, poor: 0.25 },
  FCP: { good: 1800, poor: 3000 },
  TTFB: { good: 800, poor: 1800 },
  INP: { good: 200, poor: 500 },
};

/**
 * Get rating for a metric value
 */
function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = thresholds[name as keyof typeof thresholds];
  if (!threshold) return 'good';

  if (value <= threshold.good) return 'good';
  if (value <= threshold.poor) return 'needs-improvement';
  return 'poor';
}

/**
 * Log metric to console in development
 */
function logMetric(metric: WebVitalMetric) {
  const colors = {
    good: 'color: #0cce6b',
    'needs-improvement': 'color: #ffa400',
    poor: 'color: #ff4e42',
  };

  // eslint-disable-next-line no-console
  console.log(
    `%c[Web Vitals] ${metric.name}: ${metric.value.toFixed(2)} (${metric.rating})`, // nosemgrep: javascript.lang.security.audit.unsafe-formatstring.unsafe-formatstring
    colors[metric.rating]
  );
}

/**
 * Send metric to analytics endpoint
 */
function sendToAnalytics(metric: WebVitalMetric) {
  // Skip in development unless explicitly enabled
  if (isDev() && !import.meta.env.VITE_ENABLE_ANALYTICS) {
    return;
  }

  // Report to Sentry if available
  const win = globalThis as unknown as Window & {
    Sentry?: {
      addBreadcrumb: (data: Record<string, unknown>) => void;
      captureMessage: (msg: string, data: Record<string, unknown>) => void;
    };
  };
  const Sentry = win.Sentry;
  if (Sentry) {
    Sentry.addBreadcrumb({
      category: 'web-vitals',
      message: `${metric.name}: ${metric.value.toFixed(2)}`,
      level: metric.rating === 'poor' ? 'warning' : 'info',
      data: {
        value: metric.value,
        rating: metric.rating,
        delta: metric.delta,
      },
    });

    // Report poor metrics as exceptions for alerting
    if (metric.rating === 'poor') {
      Sentry.captureMessage(`Poor Web Vital: ${metric.name}`, {
        level: 'warning',
        extra: {
          value: metric.value,
          threshold: thresholds[metric.name as keyof typeof thresholds],
        },
        tags: {
          webVital: metric.name,
          rating: metric.rating,
        },
      });
    }
  }

  // Send to custom analytics endpoint if configured
  const analyticsEndpoint = import.meta.env.VITE_ANALYTICS_ENDPOINT;
  if (analyticsEndpoint) {
    const body = JSON.stringify({
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      delta: metric.delta,
      id: metric.id,
      page: globalThis.location.pathname,
      timestamp: Date.now(),
    });

    // Use sendBeacon for reliability
    if (navigator.sendBeacon) {
      navigator.sendBeacon(analyticsEndpoint, body);
    } else {
      fetch(analyticsEndpoint, {
        body,
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        keepalive: true,
      }).catch(() => {
        // Silently fail - analytics shouldn't break the app
      });
    }
  }
}

/**
 * Create a metric reporter callback
 */
function createReporter(name: string) {
  return (entry: PerformanceEntry & { value?: number }) => {
    const value = entry.value ?? entry.duration ?? 0;
    const metric: WebVitalMetric = {
      name,
      value,
      rating: getRating(name, value),
      delta: value,
      id: `${name}-${Date.now()}`,
      entries: [entry],
    };

    if (isDev()) {
      logMetric(metric);
    }

    sendToAnalytics(metric);
  };
}

/**
 * Observe Largest Contentful Paint
 */
function observeLCP() {
  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1] as PerformanceEntry & { startTime: number };
      if (lastEntry) {
        createReporter('LCP')({ ...lastEntry, value: lastEntry.startTime });
      }
    });
    observer.observe({ type: 'largest-contentful-paint', buffered: true });
  } catch {
    // Browser doesn't support LCP
  }
}

/**
 * Observe First Input Delay
 */
function observeFID() {
  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const firstEntry = entries[0] as PerformanceEntry & {
        processingStart: number;
        startTime: number;
      };
      if (firstEntry) {
        createReporter('FID')({
          ...firstEntry,
          value: firstEntry.processingStart - firstEntry.startTime,
        });
      }
    });
    observer.observe({ type: 'first-input', buffered: true });
  } catch {
    // Browser doesn't support FID
  }
}

/**
 * Observe Cumulative Layout Shift
 */
function observeCLS() {
  try {
    let clsValue = 0;
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as (PerformanceEntry & {
        hadRecentInput: boolean;
        value: number;
      })[]) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      }
    });
    observer.observe({ type: 'layout-shift', buffered: true });

    // Report on page hide
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        createReporter('CLS')({ duration: 0, value: clsValue } as PerformanceEntry & {
          value: number;
        });
      }
    });
  } catch {
    // Browser doesn't support CLS
  }
}

/**
 * Observe First Contentful Paint
 */
function observeFCP() {
  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const fcpEntry = entries.find((entry) => entry.name === 'first-contentful-paint');
      if (fcpEntry) {
        createReporter('FCP')({ ...fcpEntry, value: fcpEntry.startTime } as PerformanceEntry & {
          value: number;
        });
      }
    });
    observer.observe({ type: 'paint', buffered: true });
  } catch {
    // Browser doesn't support FCP
  }
}

/**
 * Observe Time to First Byte
 */
function observeTTFB() {
  try {
    const navigationEntry = performance.getEntriesByType(
      'navigation'
    )[0] as PerformanceNavigationTiming;
    if (navigationEntry) {
      createReporter('TTFB')({
        ...navigationEntry,
        value: navigationEntry.responseStart,
      } as PerformanceEntry & { value: number });
    }
  } catch {
    // Browser doesn't support TTFB
  }
}

/**
 * Observe Interaction to Next Paint
 */
function observeINP() {
  try {
    let maxINP = 0;
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as (PerformanceEntry & { duration: number })[]) {
        if (entry.duration > maxINP) {
          maxINP = entry.duration;
        }
      }
    });
    observer.observe({ type: 'event', buffered: true });

    // Report on page hide
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden' && maxINP > 0) {
        createReporter('INP')({ duration: maxINP, value: maxINP } as PerformanceEntry & {
          value: number;
        });
      }
    });
  } catch {
    // Browser doesn't support INP
  }
}

/**
 * Initialize Web Vitals tracking
 * Call this in your main.ts after the app mounts
 */
export function initWebVitals() {
  if (typeof globalThis === 'undefined' || !globalThis.performance) return;

  // Wait for idle to not block main thread
  if ('requestIdleCallback' in globalThis) {
    (
      globalThis as unknown as { requestIdleCallback: (cb: () => void) => void }
    ).requestIdleCallback(() => {
      observeLCP();
      observeFID();
      observeCLS();
      observeFCP();
      observeTTFB();
      observeINP();
    });
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(() => {
      observeLCP();
      observeFID();
      observeCLS();
      observeFCP();
      observeTTFB();
      observeINP();
    }, 100);
  }

  if (isDev()) {
    // eslint-disable-next-line no-console
    console.log('[Web Vitals] Monitoring initialized');
  }
}

/**
 * Get current performance metrics summary
 */
export function getPerformanceSummary(): Record<string, number> {
  const summary: Record<string, number> = {};

  try {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (navigation) {
      summary.ttfb = navigation.responseStart;
      summary.domContentLoaded = navigation.domContentLoadedEventEnd;
      summary.loadComplete = navigation.loadEventEnd;
      summary.domInteractive = navigation.domInteractive;
    }

    const paint = performance.getEntriesByType('paint');
    const fcp = paint.find((e) => e.name === 'first-contentful-paint');
    if (fcp) {
      summary.fcp = fcp.startTime;
    }
  } catch {
    // Ignore errors
  }

  return summary;
}
