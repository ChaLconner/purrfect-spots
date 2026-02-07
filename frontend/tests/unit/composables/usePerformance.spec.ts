import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { usePerformance, logMetric, measureAsync, measureSync, useRenderTime, useApiTiming, getMetrics, clearMetrics } from '@/composables/usePerformance';
import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';

describe('usePerformance', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    clearMetrics();
    
    // Mock Performance APIs
    globalThis.performance = {
      now: vi.fn(),
      getEntriesByType: vi.fn(() => []),
      getEntriesByName: vi.fn(() => []),
    } as any;
    
    // Mock PerformanceObserver
    globalThis.PerformanceObserver = vi.fn().mockImplementation((callback) => ({
      observe: vi.fn(),
      disconnect: vi.fn(),
    })) as any;

    // Setup now() sequence via mock implementation if needed
    (globalThis.performance.now as any).mockReturnValue(1000);
  });

  afterEach(() => {
    vi.restoreAllMocks();
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
  });
});

