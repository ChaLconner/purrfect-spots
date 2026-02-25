/**
 * Performance Monitoring Composable
 *
 * Provides utilities for tracking and reporting performance metrics:
 * - Page load times
 * - Component render times
 * - API call durations
 * - Web Vitals metrics
 *
 * @module usePerformance
 */
import { onMounted, ref, type Ref } from 'vue';

/**
 * Performance metric entry
 */
interface PerformanceMetric {
  name: string;
  value: number;
  unit: 'ms' | 's' | 'score';
  timestamp: number;
  metadata?: Record<string, unknown>;
}

/**
 * Web Vitals thresholds for performance rating
 */
const VITALS_THRESHOLDS = {
  LCP: { good: 2500, poor: 4000 }, // Largest Contentful Paint
  FID: { good: 100, poor: 300 }, // First Input Delay
  CLS: { good: 0.1, poor: 0.25 }, // Cumulative Layout Shift
  FCP: { good: 1800, poor: 3000 }, // First Contentful Paint
  TTFB: { good: 800, poor: 1800 }, // Time to First Byte
};

/**
 * Performance metrics store
 */
const metrics = ref<PerformanceMetric[]>([]);

/**
 * Rate a metric as good, needs improvement, or poor
 */
function rateMetric(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = VITALS_THRESHOLDS[name as keyof typeof VITALS_THRESHOLDS];
  if (!threshold) return 'good';

  if (value <= threshold.good) return 'good';
  if (value <= threshold.poor) return 'needs-improvement';
  return 'poor';
}

/**
 * Log a performance metric
 */
export function logMetric(metric: PerformanceMetric): void {
  metrics.value.push(metric);

  // Log to console in development
  if (import.meta.env.DEV) {
    const rating = rateMetric(metric.name, metric.value);
    const ratingEmojis: Record<string, string> = {
      good: '✅',
      'needs-improvement': '⚠️',
      poor: '❌',
    };
     
    const emoji = ratingEmojis[rating] || '❓';
    // eslint-disable-next-line no-console
    console.log(
      '[Perf]',
      emoji,
      `${metric.name}:`,
      `${metric.value.toFixed(2)}${metric.unit}`,
      metric.metadata || ''
    );
  }

  // Send to analytics in production (if configured)
  const win = globalThis as unknown as {
    gtag?: (command: string, action: string, params: Record<string, unknown>) => void;
  };
  if (import.meta.env.PROD && win.gtag) {
    win.gtag('event', 'performance_metric', {
      metric_name: metric.name,
      metric_value: metric.value,
      metric_rating: rateMetric(metric.name, metric.value),
    });
  }
}

/**
 * Measure execution time of an async function
 */
export async function measureAsync<T>(
  name: string,
  fn: () => Promise<T>,
  metadata?: Record<string, unknown>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const duration = performance.now() - start;

    logMetric({
      name,
      value: duration,
      unit: 'ms',
      timestamp: Date.now(),
      metadata: { ...metadata, success: true },
    });

    return result;
  } catch (error) {
    const duration = performance.now() - start;

    logMetric({
      name,
      value: duration,
      unit: 'ms',
      timestamp: Date.now(),
      metadata: { ...metadata, success: false, error: String(error) },
    });

    throw error;
  }
}

/**
 * Measure execution time of a sync function
 */
export function measureSync<T>(name: string, fn: () => T, metadata?: Record<string, unknown>): T {
  const start = performance.now();
  const result = fn();
  const duration = performance.now() - start;

  logMetric({
    name,
    value: duration,
    unit: 'ms',
    timestamp: Date.now(),
    metadata,
  });

  return result;
}

/**
 * Web Vitals observer
 */
export function useWebVitals(): { vitals: Ref<Record<string, number>> } {
  const vitals = ref<Record<string, number>>({});

  onMounted(() => {
    if (typeof globalThis === 'undefined' || typeof performance === 'undefined') return;

    // Use PerformanceObserver for Web Vitals
    try {
      // Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        vitals.value.LCP = lastEntry.startTime;
        logMetric({
          name: 'LCP',
          value: lastEntry.startTime,
          unit: 'ms',
          timestamp: Date.now(),
        });
      });
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });

      // First Input Delay
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries() as PerformanceEventTiming[];
        entries.forEach((entry) => {
          vitals.value.FID = entry.processingStart - entry.startTime;
          logMetric({
            name: 'FID',
            value: entry.processingStart - entry.startTime,
            unit: 'ms',
            timestamp: Date.now(),
          });
        });
      });
      fidObserver.observe({ type: 'first-input', buffered: true });

      // Cumulative Layout Shift
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries() as LayoutShiftEntry[];
        entries.forEach((entry) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
            vitals.value.CLS = clsValue;
          }
        });
      });
      clsObserver.observe({ type: 'layout-shift', buffered: true });
    } catch (e) {
      console.warn('[Perf] PerformanceObserver not supported:', e);
    }

    // Navigation timing - use modern API if available
    const [navigation] = performance.getEntriesByType(
      'navigation'
    ) as PerformanceNavigationTiming[];
    if (navigation) {
      // Wait for load to complete
      globalThis.addEventListener('load', () => {
        setTimeout(() => {
          const ttfb = navigation.responseStart;
          const fcp = performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0;

          if (ttfb > 0) {
            vitals.value.TTFB = ttfb;
            logMetric({
              name: 'TTFB',
              value: ttfb,
              unit: 'ms',
              timestamp: Date.now(),
            });
          }

          if (fcp > 0) {
            vitals.value.FCP = fcp;
            logMetric({
              name: 'FCP',
              value: fcp,
              unit: 'ms',
              timestamp: Date.now(),
            });
          }
        }, 0);
      });
    }
  });

  return { vitals };
}

/**
 * Component render time tracking
 */
export function useRenderTime(componentName: string): { renderTime: Ref<number>; startMeasure: () => void } {
  const renderStart = ref(0);
  const renderTime = ref(0);

  onMounted(() => {
    renderTime.value = performance.now() - renderStart.value;

    if (renderTime.value > 100) {
      // Only log slow renders
      logMetric({
        name: 'component_render',
        value: renderTime.value,
        unit: 'ms',
        timestamp: Date.now(),
        metadata: { component: componentName },
      });
    }
  });

  // Call this at the start of setup()
  const startMeasure = (): void => {
    renderStart.value = performance.now();
  };

  return { renderTime, startMeasure };
}

/**
 * API call timing wrapper
 */
export function useApiTiming(): { apiCalls: Ref<Map<string, number>>; trackApiCall: <T>(endpoint: string, method: string, apiCall: () => Promise<T>) => Promise<T> } {
  const apiCalls = ref<Map<string, number>>(new Map());

  const trackApiCall = async <T>(
    endpoint: string,
    method: string,
    apiCall: () => Promise<T>
  ): Promise<T> => {
    return measureAsync(`api_${method}_${endpoint}`, apiCall, {
      endpoint,
      method,
    });
  };

  return { apiCalls, trackApiCall };
}

/**
 * Get all collected metrics
 */
export function getMetrics(): PerformanceMetric[] {
  return [...metrics.value];
}

/**
 * Clear all collected metrics
 */
export function clearMetrics(): void {
  metrics.value = [];
}

/**
 * Get performance summary
 */
export function getPerformanceSummary(): Record<
  string,
  { avg: number; min: number; max: number; count: number }
> {
  const summary: Record<
    string,
    { avg: number; min: number; max: number; count: number; total: number }
  > = {};

  metrics.value.forEach((metric) => {
    if (!summary[metric.name]) {
      summary[metric.name] = { avg: 0, min: Infinity, max: -Infinity, count: 0, total: 0 };
    }

    summary[metric.name].count++;
    summary[metric.name].total += metric.value;
    summary[metric.name].min = Math.min(summary[metric.name].min, metric.value);
    summary[metric.name].max = Math.max(summary[metric.name].max, metric.value);
    summary[metric.name].avg = summary[metric.name].total / summary[metric.name].count;
  });

  return summary;
}

// TypeScript declarations for window extensions
declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }

  interface LayoutShiftEntry extends PerformanceEntry {
    hadRecentInput: boolean;
    value: number;
  }
}

export default {
  logMetric,
  measureAsync,
  measureSync,
  useWebVitals,
  useRenderTime,
  useApiTiming,
  getMetrics,
  clearMetrics,
  getPerformanceSummary,
};
