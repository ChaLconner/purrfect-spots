import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { usePerformance, logMetric, measureAsync, measureSync, useRenderTime, useApiTiming, getMetrics, clearMetrics, getPerformanceSummary } from '@/composables/usePerformance';
import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';

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
    
    // Mock PerformanceObserver
    globalThis.PerformanceObserver = vi.fn().mockImplementation(function() {
      return {
        observe: vi.fn(),
        disconnect: vi.fn()
      };
    }) as any;

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
    it('should initialize observers', async () => {
      const { useWebVitals } = await import('@/composables/usePerformance');
      
      const TestComponent = defineComponent({
        setup() {
          useWebVitals();
          return {};
        },
        template: '<div></div>',
      });

      mount(TestComponent);
      
      expect(globalThis.PerformanceObserver).toHaveBeenCalled();
    });
    
    it('should handle missing globalThis gracefully', async () => {
      const originalGlobalThis = globalThis.globalThis;
      delete (globalThis as any).globalThis;
      
      const { useWebVitals } = await import('@/composables/usePerformance');
      
      const TestComponent = defineComponent({
        setup() {
          useWebVitals();
          return {};
        },
        template: '<div></div>',
      });

      expect(() => mount(TestComponent)).not.toThrow();
      
      globalThis.globalThis = originalGlobalThis;
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
      const { apiCalls, trackApiCall } = useApiTiming();
      
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

  describe('production mode', () => {
    it('should call gtag in production', async () => {
      const mockGtag = vi.fn();
      vi.stubGlobal('import.meta', { env: { DEV: false, PROD: true } });
      (globalThis as any).gtag = mockGtag;

      // Re-import to get fresh module with new import.meta
      vi.resetModules();
      const { logMetric: logMetricProd } = await import('@/composables/usePerformance');
      
      logMetricProd({ name: 'LCP', value: 2000, unit: 'ms', timestamp: 1 });
      
      expect(mockGtag).toHaveBeenCalledWith('event', 'performance_metric', {
        metric_name: 'LCP',
        metric_value: 2000,
        metric_rating: 'good',
      });
    });
  });
});

