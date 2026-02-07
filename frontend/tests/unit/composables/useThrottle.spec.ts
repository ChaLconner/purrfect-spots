import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ref, nextTick } from 'vue';
import { useThrottle, useThrottleFn, useThrottledAsync } from '@/composables/useThrottle';

describe('useThrottle composables', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('useThrottle (ref)', () => {
    it('should throttle ref updates', async () => {
      const source = ref(0);
      const throttled = useThrottle(source, 100);

      expect(throttled.value).toBe(0);

      source.value = 1;
      await nextTick();
      expect(throttled.value).toBe(1); // Leading call is immediate

      source.value = 2;
      await nextTick();
      expect(throttled.value).toBe(1); // Throttled

      vi.advanceTimersByTime(50);
      source.value = 3;
      await nextTick();
      expect(throttled.value).toBe(1); // Still throttled

      vi.advanceTimersByTime(50);
      expect(throttled.value).toBe(3); // Updated after interval
    });
  });

  describe('useThrottleFn', () => {
    it('should throttle function execution', () => {
      const fn = vi.fn();
      const throttled = useThrottleFn(fn, 100);

      throttled();
      expect(fn).toHaveBeenCalledTimes(1);

      throttled();
      expect(fn).toHaveBeenCalledTimes(1);

      vi.advanceTimersByTime(100);
      // Trailing call happens after interval
      expect(fn).toHaveBeenCalledTimes(2);
    });

    it('should respect leading/trailing options', () => {
        const fn = vi.fn();
        const throttled = useThrottleFn(fn, 100, { leading: false, trailing: true });

        throttled();
        expect(fn).toHaveBeenCalledTimes(0);

        vi.advanceTimersByTime(100);
        expect(fn).toHaveBeenCalledTimes(1);
    });
  });

  describe('useThrottledAsync', () => {
    it('should prevent concurrent execution', async () => {
      const fn = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(() => resolve('done'), 50)));
      const throttled = useThrottledAsync(fn, 100);

      const p1 = throttled();
      expect(fn).toHaveBeenCalledTimes(1);

      const p2 = throttled(); 
      expect(fn).toHaveBeenCalledTimes(1);
      
      // Wait for p1 to resolve
      vi.advanceTimersByTime(50);
      const result1 = await p1;
      const result2 = await p2;
      
      expect(result1).toBe('done');
      expect(result2).toBe('done');
    });
  });
});
