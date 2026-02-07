/**
 * useDebounce composable
 *
 * Provides debouncing utilities for Vue 3 applications.
 * Useful for search boxes, form inputs, and API calls.
 */

import { ref, watch, type Ref } from 'vue';

/**
 * Creates a debounced ref that updates after a delay
 *
 * @param value - The source ref to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns A debounced ref
 *
 * @example
 * const searchQuery = ref('');
 * const debouncedQuery = useDebounce(searchQuery, 500);
 *
 * // debouncedQuery will update 500ms after searchQuery stops changing
 */
export function useDebounce<T>(value: Ref<T>, delay: number = 300): Ref<T> {
  const debouncedValue = ref(value.value) as Ref<T>;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  watch(value, (newValue) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      debouncedValue.value = newValue;
      timeoutId = null;
    }, delay);
  });

  return debouncedValue;
}

/**
 * Creates a debounced function
 *
 * @param fn - The function to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns A debounced version of the function
 *
 * @example
 * const debouncedSearch = useDebounceFn((query: string) => {
 *   api.search(query);
 * }, 500);
 */
export function useDebounceFn<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  delay: number = 300
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  const debouncedFn = (...args: Parameters<T>): void => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delay);
  };

  // Add cancel method
  debouncedFn.cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  return debouncedFn;
}

/**
 * Creates a debounced async function that returns a promise
 *
 * @param fn - The async function to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns A debounced version of the async function
 */
export function useDebouncedAsync<T extends (...args: Parameters<T>) => Promise<ReturnType<T>>>(
  fn: T,
  delay: number = 300
): (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>> | undefined> {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let latestResolve: ((value: Awaited<ReturnType<T>> | undefined) => void) | null = null;

  return (...args: Parameters<T>): Promise<Awaited<ReturnType<T>> | undefined> => {
    return new Promise((resolve) => {
      // Cancel previous pending call
      if (timeoutId) {
        clearTimeout(timeoutId);
        if (latestResolve) {
          latestResolve(undefined);
        }
      }

      latestResolve = resolve;

      timeoutId = setTimeout(async () => {
        const result = await fn(...args);
        resolve(result as Awaited<ReturnType<T>>);
        timeoutId = null;
        latestResolve = null;
      }, delay);
    });
  };
}
