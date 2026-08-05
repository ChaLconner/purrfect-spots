import { beforeEach, describe, expect, it, vi } from 'vitest';

const { onINP } = vi.hoisted(() => ({ onINP: vi.fn() }));

vi.mock('web-vitals', () => ({ onINP }));
vi.mock('@/utils/env', () => ({ isDev: () => false }));

import { initWebVitals } from '@/utils/webVitals';

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
});
