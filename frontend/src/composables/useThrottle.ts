/**
 * useThrottle composable
 *
 * Provides throttling utilities for Vue 3 applications.
 * Useful for button clicks, scroll events, and rate-limiting actions.
 */

import { ref, watch, type Ref } from 'vue';

/**
 * Creates a throttled ref that updates at most once per interval
 *
 * @param value - The source ref to throttle
 * @param interval - Minimum interval between updates in milliseconds (default: 300ms)
 * @returns A throttled ref
 *
 * @example
 * const scrollPosition = ref(0);
 * const throttledScroll = useThrottle(scrollPosition, 100);
 */
export function useThrottle<T>(value: Ref<T>, interval: number = 300): Ref<T> {
  const throttledValue = ref(value.value) as Ref<T>;
  let lastUpdate = 0;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  watch(value, (newValue) => {
    const now = Date.now();
    const timeSinceLastUpdate = now - lastUpdate;

    if (timeSinceLastUpdate >= interval) {
      // Enough time has passed, update immediately
      throttledValue.value = newValue;
      lastUpdate = now;
    } else {
      // Schedule update for remaining time
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      timeoutId = setTimeout(() => {
        throttledValue.value = value.value;
        lastUpdate = Date.now();
        timeoutId = null;
      }, interval - timeSinceLastUpdate);
    }
  });

  return throttledValue;
}

/**
 * Creates a throttled function that executes at most once per interval
 *
 * @param fn - The function to throttle
 * @param interval - Minimum interval between executions in milliseconds (default: 300ms)
 * @param options - Throttle options
 * @returns A throttled version of the function
 *
 * @example
 * const throttledSubmit = useThrottleFn(() => {
 *   form.submit();
 * }, 1000);
 */
export function useThrottleFn<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  interval: number = 300,
  options: { leading?: boolean; trailing?: boolean } = {}
): (...args: Parameters<T>) => void {
  const { leading = true, trailing = true } = options;

  let lastExec = 0;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let lastArgs: Parameters<T> | null = null;

  const throttledFn = (...args: Parameters<T>): void => {
    const now = Date.now();
    const timeSinceLastExec = now - lastExec;

    lastArgs = args;

    if (timeSinceLastExec >= interval) {
      // Enough time has passed
      if (leading) {
        fn(...args);
        lastExec = now;
        lastArgs = null;
      }
    }

    // Schedule trailing call
    if (trailing && !timeoutId) {
      timeoutId = setTimeout(() => {
        if (lastArgs) {
          fn(...lastArgs);
          lastExec = Date.now();
          lastArgs = null;
        }
        timeoutId = null;
      }, interval - timeSinceLastExec);
    }
  };

  // Add cancel method
  throttledFn.cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    lastArgs = null;
  };

  return throttledFn;
}

/**
 * Creates a throttled async function
 * Prevents concurrent executions and throttles by interval
 *
 * @param fn - The async function to throttle
 * @param interval - Minimum interval between executions (default: 300ms)
 * @returns A throttled version of the async function
 */
export function useThrottledAsync<T extends (...args: Parameters<T>) => Promise<ReturnType<T>>>(
  fn: T,
  interval: number = 300
): (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>> | null> {
  let lastExec = 0;
  let isExecuting = false;
  let pendingPromise: Promise<Awaited<ReturnType<T>>> | null = null;

  return async (...args: Parameters<T>): Promise<Awaited<ReturnType<T>> | null> => {
    const now = Date.now();
    const timeSinceLastExec = now - lastExec;

    // If already executing, return the pending promise
    if (isExecuting && pendingPromise) {
      return pendingPromise;
    }

    // If within throttle interval, return null
    if (timeSinceLastExec < interval) {
      return null;
    }

    isExecuting = true;
    lastExec = now;

    try {
      pendingPromise = fn(...args) as Promise<Awaited<ReturnType<T>>>;
      const result = await pendingPromise;
      return result;
    } finally {
      isExecuting = false;
      pendingPromise = null;
    }
  };
}
