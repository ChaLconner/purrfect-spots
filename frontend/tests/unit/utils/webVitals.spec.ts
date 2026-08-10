import { beforeEach, describe, expect, it, vi } from 'vitest';

const { onINP } = vi.hoisted(() => ({ onINP: vi.fn() }));

vi.mock('web-vitals', () => ({ onINP }));
vi.mock('@/utils/env', () => ({ isDev: () => false }));

import { getPerformanceSummary, initWebVitals } from '@/utils/webVitals';

describe('web vitals', () => {
  beforeEach(() => {
    onINP.mockReset();
    Object.defineProperty(globalThis, 'requestIdleCallback', {
      configurable: true,
      value: (callback: () => void) => callback(),
    });
  });

  it('uses the standards-compliant INP reporter', () => {
    initWebVitals();

    expect(onINP).toHaveBeenCalledOnce();
    expect(onINP).toHaveBeenCalledWith(expect.any(Function));
  });

  it('returns available navigation performance metrics', () => {
    const original = performance.getEntriesByType;
    Object.defineProperty(performance, 'getEntriesByType', {
      configurable: true,
      value: (type: string) =>
        type === 'navigation'
          ? [{ responseStart: 12, domContentLoadedEventEnd: 34, loadEventEnd: 56, domInteractive: 23 }]
          : [{ name: 'first-contentful-paint', startTime: 45 }],
    });

    expect(getPerformanceSummary()).toEqual({
      ttfb: 12,
      domContentLoaded: 34,
      loadComplete: 56,
      domInteractive: 23,
      fcp: 45,
    });

    Object.defineProperty(performance, 'getEntriesByType', { configurable: true, value: original });
  });
});
