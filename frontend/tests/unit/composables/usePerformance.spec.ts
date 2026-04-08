import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { logMetric, measureAsync, measureSync, useRenderTime, useApiTiming, getMetrics, clearMetrics, getPerformanceSummary, useWebVitals } from '@/composables/usePerformance';
import { mount } from '@vue/test-utils';
import { defineComponent, nextTick, h } from 'vue';

describe('usePerformance', () => {
  let originalImportMeta: any;

  beforeEach(() => {
    vi.useFakeTimers();
    clearMetrics();
    
    originalImportMeta = { ...import.meta };
    
    // Mock import.meta.env
    vi.stubGlobal('import.meta', {
      env: { DEV: true, PROD: false }
    });
    
    // Mock Performance APIs
    globalThis.performance = {
      now: vi.fn(),
      getEntriesByType: vi.fn(() => []),
      getEntriesByName: vi.fn(() => []),
    } as any;
    
    // Mock PerformanceObserver to handle multiple observers
    const callbacks = new Map<string, any>();
    globalThis.PerformanceObserver = vi.fn().mockImplementation(function(cb) {
      return {
        observe: vi.fn().mockImplementation((options) => {
          if (options.type) {
            callbacks.set(options.type, cb);
          }
        }),
        disconnect: vi.fn()
      };
    }) as any;

    (globalThis as any).triggerPerformanceObserver = (type: string, entries: any[]) => {
      const cb = callbacks.get(type);
      if (cb) {
        cb({
          getEntries: () => entries
        });
      }
    };

    // Setup now() sequence via mock implementation if needed
    (globalThis.performance.now as any).mockReturnValue(1000);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal('import.meta', originalImportMeta);
  });

  describe('logMetric', () => {
    it('should add metric to store', () => {
      logMetric({
        name: 'test-metric',
        value: 123,
        unit: 'ms',
        timestamp: Date.now(),
      });
      
      const metrics = getMetrics();
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe('test-metric');
      expect(metrics[0].value).toBe(123);
    });

    it('should handle multiple metrics', () => {
      logMetric({ name: 'metric1', value: 100, unit: 'ms', timestamp: 1 });
      logMetric({ name: 'metric2', value: 200, unit: 'ms', timestamp: 2 });
      logMetric({ name: 'metric1', value: 150, unit: 'ms', timestamp: 3 });

      expect(getMetrics()).toHaveLength(3);
    });
  });

  describe('clearMetrics', () => {
    it('should clear all metrics', () => {
      logMetric({ name: 'test', value: 1, unit: 'ms', timestamp: 1 });
      expect(getMetrics()).toHaveLength(1);
      
      clearMetrics();
      expect(getMetrics()).toHaveLength(0);
    });
  });

  describe('getPerformanceSummary', () => {
    it('should return empty object when no metrics', () => {
      expect(getPerformanceSummary()).toEqual({});
    });

    it('should calculate summary statistics', () => {
      logMetric({ name: 'api', value: 100, unit: 'ms', timestamp: 1 });
      logMetric({ name: 'api', value: 200, unit: 'ms', timestamp: 2 });
      logMetric({ name: 'api', value: 300, unit: 'ms', timestamp: 3 });

      const summary = getPerformanceSummary();
      expect(summary.api).toBeDefined();
      expect(summary.api.count).toBe(3);
      expect(summary.api.min).toBe(100);
      expect(summary.api.max).toBe(300);
      expect(summary.api.avg).toBe(200);
    });

    it('should handle multiple metric types', () => {
      logMetric({ name: 'render', value: 50, unit: 'ms', timestamp: 1 });
      logMetric({ name: 'api', value: 100, unit: 'ms', timestamp: 2 });

      const summary = getPerformanceSummary();
      expect(summary.render).toBeDefined();
      expect(summary.api).toBeDefined();
    });
  });

  describe('measureAsync', () => {
    it('should measure execution time', async () => {
      (globalThis.performance.now as any)
        .mockReturnValueOnce(1000) // start
        .mockReturnValueOnce(1500); // end
        
      const fn = vi.fn().mockResolvedValue('result');
      
      const result = await measureAsync('test-async', fn);
      
      expect(result).toBe('result');
      expect(fn).toHaveBeenCalled();
      
      const metrics = getMetrics();
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe('test-async');
      expect(metrics[0].value).toBe(500);
    });

    it('should measure time even if function throws', async () => {
       (globalThis.performance.now as any)
        .mockReturnValueOnce(1000) // start
        .mockReturnValueOnce(1200); // end (in catch)

      const fn = vi.fn().mockRejectedValue(new Error('fail'));
      
      await expect(measureAsync('test-fail', fn)).rejects.toThrow('fail');
      
      const metrics = getMetrics();
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe('test-fail');
      expect(metrics[0].value).toBe(200);
      expect(metrics[0].metadata?.success).toBe(false);
    });

    it('should pass metadata to logged metric', async () => {
      (globalThis.performance.now as any)
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1100);

      await measureAsync('test', async () => 'ok', { extra: 'data' });

      const metrics = getMetrics();
      expect(metrics[0].metadata?.extra).toBe('data');
    });
  });

  describe('useWebVitals', () => {
    it('should track Web Vitals from observers', async () => {
      let vitalsRef: any;
      const TestComponent = defineComponent({
        setup() {
          const { vitals } = useWebVitals();
          vitalsRef = vitals;
          return {};
        },
        template: '<div></div>'
      });
      
      mount(TestComponent);
      await nextTick();
      
      expect(globalThis.PerformanceObserver).toHaveBeenCalled();
      
      // Trigger LCP
      const lcpEntry = { name: 'LCP', startTime: 2000, entryType: 'largest-contentful-paint' };
      (globalThis as any).triggerPerformanceObserver('largest-contentful-paint', [lcpEntry]);
      expect(vitalsRef.value.LCP).toBe(2000);
      
      // Trigger FID
      const fidEntry = { name: 'FID', startTime: 1000, processingStart: 1150, entryType: 'first-input' };
      (globalThis as any).triggerPerformanceObserver('first-input', [fidEntry]);
      expect(vitalsRef.value.FID).toBe(150);
      
      // Trigger CLS
      const clsEntry = { name: 'CLS', value: 0.05, hadRecentInput: false, entryType: 'layout-shift' };
      (globalThis as any).triggerPerformanceObserver('layout-shift', [clsEntry]);
      expect(vitalsRef.value.CLS).toBe(0.05);

      const metrics = getMetrics();
      expect(metrics.some(m => m.name === 'LCP')).toBe(true);
      expect(metrics.some(m => m.name === 'FID')).toBe(true);
      expect(metrics.some(m => m.name === 'CLS')).toBe(true);
    });
    
    it('should handle missing globalThis gracefully', async () => {
      vi.stubGlobal('import.meta', { env: { DEV: true, PROD: false } });
      
      const { useWebVitals } = await import('@/composables/usePerformance');
      
      const TestComponent = defineComponent({
        setup() {
          useWebVitals();
          return {};
        },
        template: '<div></div>',
      });

      expect(() => mount(TestComponent)).not.toThrow();
    });
  });

  describe('useRenderTime', () => {
    it('should measure component render time', async () => {
      let time = 1000;
      (globalThis.performance.now as any).mockImplementation(() => {
        time += 200;
        return time;
      });
        
      const TestComponent = defineComponent({
        setup() {
          const { startMeasure } = useRenderTime('TestComp');
          startMeasure();
          return {};
        },
        template: '<div></div>',
      });
      
      const wrapper = mount(TestComponent);
      
      // Wait for onMounted (sync in mounting normally, but good to be safe)
      await wrapper.vm.$nextTick(); 
      
      const metrics = getMetrics();
      // It only logs if > 100ms. 200 > 100.
      expect(metrics.length).toBeGreaterThan(0);
      expect(metrics[0].name).toBe('component_render');
      expect(metrics[0].metadata?.component).toBe('TestComp');
      expect(metrics[0].value).toBeGreaterThanOrEqual(200);
    });

    it('should not log fast renders under 100ms', async () => {
      let time = 1000;
      (globalThis.performance.now as any).mockImplementation(() => {
        time += 50;
        return time;
      });

      const TestComponent = defineComponent({
        setup() {
          const { startMeasure } = useRenderTime('FastComp');
          startMeasure();
          return {};
        },
        template: '<div></div>',
      });

      mount(TestComponent);
      
      const metrics = getMetrics();
      expect(metrics.length).toBe(0);
    });
  });

  describe('measureSync', () => {
    it('should measure sync function', () => {
      let time = 1000;
      (globalThis.performance.now as any).mockImplementation(() => {
        time += 50;
        return time;
      });

      const result = measureSync('sync-test', () => 'success');
      expect(result).toBe('success');

      const metrics = getMetrics();
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe('sync-test');
      expect(metrics[0].value).toBeGreaterThanOrEqual(50);
    });

    it('should pass metadata to logged metric', () => {
      (globalThis.performance.now as any)
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1050);

      measureSync('test', () => {}, { context: 'unit-test' });

      const metrics = getMetrics();
      expect(metrics[0].metadata?.context).toBe('unit-test');
    });
  });

  describe('useApiTiming', () => {
    it('should track api calls', async () => {
      const { trackApiCall } = useApiTiming();
      
      let time = 1000;
      (globalThis.performance.now as any).mockImplementation(() => {
        time += 300;
        return time;
      });

      const result = await trackApiCall('/api/test', 'GET', async () => 'data');
      
      expect(result).toBe('data');
      const metrics = getMetrics();
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe('api_GET_/api/test');
      expect(metrics[0].metadata?.endpoint).toBe('/api/test');
    });

    it('should track api calls with errors', async () => {
      const { trackApiCall } = useApiTiming();
      
      (globalThis.performance.now as any)
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(500);

      await expect(
        trackApiCall('/api/error', 'POST', async () => {
          throw new Error('Network error');
        })
      ).rejects.toThrow('Network error');

      const metrics = getMetrics();
      expect(metrics[0].metadata?.success).toBe(false);
    });
  });

  describe('rateMetric (via logMetric in PROD)', () => {
    beforeEach(() => {
      vi.stubEnv('PROD', 'true');
    });

    afterEach(() => {
      vi.unstubAllEnvs();
    });

    it('should use gtag for logging in production', () => {
      const gtag = vi.fn();
      vi.stubGlobal('gtag', gtag);

      logMetric({
        name: 'LCP',
        value: 1000,
        unit: 'ms',
        timestamp: Date.now(),
      });

      expect(gtag).toHaveBeenCalledWith('event', 'performance_metric', {
        metric_name: 'LCP',
        metric_value: 1000,
        metric_rating: 'good',
      });
    });

    it('should rate LCP correctly', () => {
      const gtag = vi.fn();
      vi.stubGlobal('gtag', gtag);

      logMetric({ name: 'LCP', value: 3000, unit: 'ms', timestamp: Date.now() });
      expect(gtag).toHaveBeenLastCalledWith('event', 'performance_metric', expect.objectContaining({
        metric_rating: 'needs-improvement'
      }));

      logMetric({ name: 'LCP', value: 5000, unit: 'ms', timestamp: Date.now() });
      expect(gtag).toHaveBeenLastCalledWith('event', 'performance_metric', expect.objectContaining({
        metric_rating: 'poor'
      }));
    });

    it('should rate FID correctly', () => {
      const gtag = vi.fn();
      vi.stubGlobal('gtag', gtag);

      logMetric({ name: 'FID', value: 50, unit: 'ms', timestamp: Date.now() });
      expect(gtag).toHaveBeenLastCalledWith('event', 'performance_metric', expect.objectContaining({
        metric_rating: 'good'
      }));

      logMetric({ name: 'FID', value: 200, unit: 'ms', timestamp: Date.now() });
      expect(gtag).toHaveBeenLastCalledWith('event', 'performance_metric', expect.objectContaining({
        metric_rating: 'needs-improvement'
      }));

      logMetric({ name: 'FID', value: 400, unit: 'ms', timestamp: Date.now() });
      expect(gtag).toHaveBeenLastCalledWith('event', 'performance_metric', expect.objectContaining({
        metric_rating: 'poor'
      }));
    });

    it('should return good for unknown metrics', () => {
      const gtag = vi.fn();
      vi.stubGlobal('gtag', gtag);

      logMetric({ name: 'unknown', value: 9999, unit: 'ms', timestamp: Date.now() });
      expect(gtag).toHaveBeenLastCalledWith('event', 'performance_metric', expect.objectContaining({
        metric_rating: 'good'
      }));
    });
  });

  describe('useWebVitals - CLS logic', () => {
    it('should skip CLS value if hadRecentInput is true', () => {
      let vitalsRef: any;
      const TestComponent = defineComponent({
        setup() {
          const { vitals } = useWebVitals();
          vitalsRef = vitals;
          return {};
        },
        template: '<div></div>'
      });
      
      mount(TestComponent);
      
      const clsEntry = { name: 'CLS', value: 0.1, hadRecentInput: true, entryType: 'layout-shift' };
      (globalThis as any).triggerPerformanceObserver('layout-shift', [clsEntry]);
      
      expect(vitalsRef.value.CLS).toBeUndefined();
    });
  });

  describe('useWebVitals - Navigation Timing', () => {
    it('should track TTFB and FCP when navigation entry exists', async () => {
      const navigationEntry = { 
        entryType: 'navigation', 
        responseStart: 150 
      };
      const fcpEntry = { 
        name: 'first-contentful-paint', 
        startTime: 400 
      };
      
      (globalThis.performance.getEntriesByType as any).mockReturnValue([navigationEntry]);
      (globalThis.performance.getEntriesByName as any).mockReturnValue([fcpEntry]);
      
      const handlers: (() => void)[] = [];
      const spy = vi.spyOn(globalThis, 'addEventListener').mockImplementation((ev, handler) => {
        if (ev === 'load') handlers.push(handler as any);
      });
      
      let vitalsRef: any;
      const TestComponent = defineComponent({
        setup() {
          const { vitals } = useWebVitals();
          vitalsRef = vitals;
          return {};
        },
        template: '<div></div>'
      });
      
      mount(TestComponent);
      
      // Trigger all registered load handlers
      handlers.forEach(h => h());
      
      // Advance timers to trigger setTimeout(0)
      vi.runAllTimers();
      await nextTick();
      
      expect(vitalsRef.value.TTFB).toBe(150);
      expect(vitalsRef.value.FCP).toBe(400);
      
      const metrics = getMetrics();
      expect(metrics.some(m => m.name === 'TTFB')).toBe(true);
      expect(metrics.some(m => m.name === 'FCP')).toBe(true);
      
      spy.mockRestore();
    });

    it('should not log TTFB/FCP if they are zero', async () => {
       const navigationEntry = { 
        entryType: 'navigation', 
        responseStart: 0 // Zero
      };
      (globalThis.performance.getEntriesByType as any).mockReturnValue([navigationEntry]);
       (globalThis.performance.getEntriesByName as any).mockReturnValue([]);
      
      const handlers: (() => void)[] = [];
      const spy = vi.spyOn(globalThis, 'addEventListener').mockImplementation((ev, handler) => {
        if (ev === 'load') handlers.push(handler as any);
      });

      mount(defineComponent({
        setup() { useWebVitals(); return () => h('div'); }
      }));
      
      handlers.forEach(h => h());
      vi.runAllTimers();
      
      const metrics = getMetrics();
      expect(metrics.some(m => m.name === 'TTFB')).toBe(false);
      expect(metrics.some(m => m.name === 'FCP')).toBe(false);
      
      spy.mockRestore();
    });
  });

  describe('PerformanceObserver support', () => {
    it('should handle observer failure gracefully', () => {
      globalThis.PerformanceObserver = vi.fn().mockImplementation(() => {
        throw new Error('Not supported');
      }) as any;

      expect(() => {
        mount(defineComponent({
          setup() { useWebVitals(); return () => h('div'); }
        }));
      }).not.toThrow();
    });
  });
});

