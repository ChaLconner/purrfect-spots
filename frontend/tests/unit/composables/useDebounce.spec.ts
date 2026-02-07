import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ref, nextTick } from 'vue';
import { useDebounce, useDebounceFn, useDebouncedAsync } from '@/composables/useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('useDebounce (ref)', () => {
    it('should debounce ref value changes', async () => {
      const source = ref('initial');
      const debounced = useDebounce(source, 300);

      expect(debounced.value).toBe('initial');

      source.value = 'changed';
      await nextTick();
      
      // Value should not have changed yet
      expect(debounced.value).toBe('initial');

      // Fast-forward time
      vi.advanceTimersByTime(300);
      await nextTick();
      
      expect(debounced.value).toBe('changed');
    });

    it('should reset timer on rapid changes', async () => {
      const source = ref(0);
      const debounced = useDebounce(source, 300);

      source.value = 1;
      await nextTick();
      vi.advanceTimersByTime(100);

      source.value = 2;
      await nextTick();
      vi.advanceTimersByTime(100);

      source.value = 3;
      await nextTick();
      
      // Not enough time has passed
      expect(debounced.value).toBe(0);

      // Complete the debounce
      vi.advanceTimersByTime(300);
      await nextTick();
      
      expect(debounced.value).toBe(3);
    });

    it('should use default delay of 300ms', async () => {
      const source = ref('test');
      const debounced = useDebounce(source);

      source.value = 'updated';
      await nextTick();
      
      vi.advanceTimersByTime(299);
      await nextTick();
      expect(debounced.value).toBe('test');

      vi.advanceTimersByTime(1);
      await nextTick();
      expect(debounced.value).toBe('updated');
    });
  });

  describe('useDebounceFn', () => {
    it('should debounce function calls', () => {
      const mockFn = vi.fn();
      const debouncedFn = useDebounceFn(mockFn, 300);

      debouncedFn('arg1');
      debouncedFn('arg2');
      debouncedFn('arg3');

      expect(mockFn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(300);

      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('arg3');
    });

    it('should pass correct arguments', () => {
      const mockFn = vi.fn();
      const debouncedFn = useDebounceFn(mockFn, 100);

      debouncedFn('a', 'b', 'c');
      vi.advanceTimersByTime(100);

      expect(mockFn).toHaveBeenCalledWith('a', 'b', 'c');
    });

    it('should have cancel method', () => {
      const mockFn = vi.fn();
      const debouncedFn = useDebounceFn(mockFn, 300);

      debouncedFn('test');
      (debouncedFn as any).cancel();
      vi.advanceTimersByTime(300);

      expect(mockFn).not.toHaveBeenCalled();
    });
  });

  describe('useDebouncedAsync', () => {
    it('should debounce async function', async () => {
      const mockAsyncFn = vi.fn().mockResolvedValue('result');
      const debouncedAsync = useDebouncedAsync(mockAsyncFn, 300);

      const promise1 = debouncedAsync('first');
      const promise2 = debouncedAsync('second');

      vi.advanceTimersByTime(300);

      const result1 = await promise1;
      const result2 = await promise2;

      // First call should be cancelled (undefined)
      expect(result1).toBeUndefined();
      // Second call should succeed
      expect(result2).toBe('result');
      expect(mockAsyncFn).toHaveBeenCalledTimes(1);
      expect(mockAsyncFn).toHaveBeenCalledWith('second');
    });
  });
});
