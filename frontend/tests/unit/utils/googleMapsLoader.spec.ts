import { afterEach, describe, expect, it, vi } from 'vitest';

const googleGlobal = globalThis as typeof globalThis & {
  google?: { maps?: Record<string, unknown> };
};

afterEach(() => {
  vi.useRealTimers();
  delete googleGlobal.google;
  document.head.querySelectorAll('script').forEach((script) => script.remove());
  vi.resetModules();
});

describe('googleMapsLoader', () => {
  it('resolves the script callback and returns early when Maps is already loaded', async () => {
    const { isGoogleMapsLoaded, loadGoogleMaps } = await import('@/utils/googleMapsLoader');
    const loadPromise = loadGoogleMaps({ apiKey: 'test-key' });
    const script = document.head.querySelector<HTMLScriptElement>(
      'script[src*="maps.googleapis.com"]'
    );
    expect(script).not.toBeNull();

    googleGlobal.google = { maps: {} };
    const callbackName = new URL(script?.src || '').searchParams.get('callback');
    expect(callbackName).toBeTruthy();
    const callback = (globalThis as Record<string, unknown>)[callbackName || ''];
    expect(typeof callback).toBe('function');
    (callback as () => void)();

    await loadPromise;
    expect(isGoogleMapsLoaded()).toBe(true);
    await loadGoogleMaps({ apiKey: 'test-key' }); // pragma: allowlist secret
    expect(document.head.querySelectorAll('script[src*="maps.googleapis.com"]')).toHaveLength(1);
  });

  it('removes the script and rejects when loading times out', async () => {
    vi.useFakeTimers();
    const { loadGoogleMaps } = await import('@/utils/googleMapsLoader');
    const loadPromise = loadGoogleMaps({ apiKey: 'test-key' });
    const script = document.head.querySelector<HTMLScriptElement>(
      'script[src*="maps.googleapis.com"]'
    );
    expect(script).not.toBeNull();
    const removeSpy = vi.spyOn(script as HTMLScriptElement, 'remove');
    const rejection = expect(loadPromise).rejects.toThrow('loading timed out');

    await vi.advanceTimersByTimeAsync(15000);

    await rejection;
    expect(removeSpy).toHaveBeenCalledOnce();
  });
});
