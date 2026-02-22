import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  isBrowserExtensionError,
  logBrowserExtensionError,
  handleBrowserExtensionError,
  withBrowserExtensionHandling,
  handleUnhandledRejection,
  handleError,
  handleVueError,
} from '@/utils/browserExtensionHandler';

vi.mock('@/utils/env', () => ({
  isDev: vi.fn(() => true),
}));

describe('browserExtensionHandler', () => {
  let consoleWarnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.clearAllMocks();
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleWarnSpy.mockRestore();
  });

  describe('isBrowserExtensionError', () => {
    it('detects message channel closed errors', () => {
      expect(isBrowserExtensionError({ message: 'message channel closed' })).toBe(true);
      expect(
        isBrowserExtensionError({
          message: 'asynchronous response by returning true, but the message channel closed',
        })
      ).toBe(true);
    });

    it('detects ChunkLoadError', () => {
      expect(isBrowserExtensionError({ name: 'ChunkLoadError' })).toBe(true);
    });

    it('detects error codes', () => {
      expect(isBrowserExtensionError({ code: 'NETWORK_ERROR' })).toBe(true);
      expect(isBrowserExtensionError({ code: 'ERR_NETWORK' })).toBe(true);
    });

    it('returns false for normal errors', () => {
      expect(isBrowserExtensionError({ message: 'Network timeout' })).toBeFalsy();
      expect(isBrowserExtensionError({ message: 'Server error 500' })).toBeFalsy();
    });

    it('returns false for null/undefined', () => {
      expect(isBrowserExtensionError(null)).toBe(false);
      expect(isBrowserExtensionError(undefined)).toBe(false);
    });

    it('uses toString if message missing', () => {
      const error = {
        toString: () => 'listener indicated an asynchronous response',
      };
      expect(isBrowserExtensionError(error)).toBe(true);
    });
  });

  describe('logBrowserExtensionError', () => {
    it('logs warning in dev mode', () => {
      logBrowserExtensionError({ message: 'test error' }, 'test context');

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('Browser extension error'),
        expect.any(String),
        ':',
        'test error'
      );
    });

    it('includes context in log', () => {
      logBrowserExtensionError({ message: 'error' }, 'my-context');

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining('my-context'),
        expect.anything(),
        expect.anything()
      );
    });

    it('handles missing message', () => {
      logBrowserExtensionError(null);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.anything(),
        expect.anything(),
        expect.anything(),
        'Unknown browser extension error'
      );
    });
  });

  describe('handleBrowserExtensionError', () => {
    it('rethrows non-extension errors', async () => {
      const normalError = new Error('Normal error');

      await expect(
        handleBrowserExtensionError(normalError, async () => 'result')
      ).rejects.toThrow('Normal error');
    });

    it('retries on extension error', async () => {
      const extError = { message: 'message channel closed' };
      const retryCallback = vi.fn().mockResolvedValue('success');

      const result = await handleBrowserExtensionError(extError, retryCallback, 2, 0);

      expect(result).toBe('success');
      expect(retryCallback).toHaveBeenCalledTimes(1);
    });

    it('retries multiple times on persistent errors', async () => {
      const extError = { message: 'message channel closed' };
      const retryCallback = vi
        .fn()
        .mockRejectedValueOnce({ message: 'message channel closed' })
        .mockRejectedValueOnce({ message: 'message channel closed' })
        .mockResolvedValue('success');

      const result = await handleBrowserExtensionError(extError, retryCallback, 3, 0);

      expect(result).toBe('success');
      expect(retryCallback).toHaveBeenCalledTimes(3);
    });

    it('throws last error after max retries', async () => {
      const extError = { message: 'message channel closed' };
      const lastError = { message: 'still failing' };
      const retryCallback = vi.fn().mockRejectedValue(lastError);

      await expect(
        handleBrowserExtensionError(extError, retryCallback, 1, 0)
      ).rejects.toEqual(lastError);
    });

    it('stops retrying on non-extension error', async () => {
      const extError = { message: 'message channel closed' };
      const normalError = new Error('Different error');
      const retryCallback = vi.fn().mockRejectedValue(normalError);

      await expect(
        handleBrowserExtensionError(extError, retryCallback, 3, 0)
      ).rejects.toThrow('Different error');

      expect(retryCallback).toHaveBeenCalledTimes(1);
    });
  });

  describe('withBrowserExtensionHandling', () => {
    it('passes through successful results', async () => {
      const fn = vi.fn().mockResolvedValue('result');
      const wrapped = withBrowserExtensionHandling(fn);

      const result = await wrapped();

      expect(result).toBe('result');
    });

    it('retries on extension errors', async () => {
      const fn = vi
        .fn()
        .mockRejectedValueOnce({ message: 'message channel closed' })
        .mockResolvedValue('success');
      const wrapped = withBrowserExtensionHandling(fn, { maxRetries: 2, retryDelay: 0 });

      const result = await wrapped();

      expect(result).toBe('success');
      expect(fn).toHaveBeenCalledTimes(2);
    });

    it('rethrows non-extension errors', async () => {
      const fn = vi.fn().mockRejectedValue(new Error('Normal error'));
      const wrapped = withBrowserExtensionHandling(fn);

      await expect(wrapped()).rejects.toThrow('Normal error');
    });
  });

  describe('handleUnhandledRejection', () => {
    it('prevents default for extension errors', () => {
      const event = {
        reason: { message: 'message channel closed' },
        preventDefault: vi.fn(),
      } as unknown as PromiseRejectionEvent;

      const result = handleUnhandledRejection(event);

      expect(result).toBe(false);
      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('returns true for normal errors', () => {
      const event = {
        reason: new Error('Normal error'),
        preventDefault: vi.fn(),
      } as unknown as PromiseRejectionEvent;

      const result = handleUnhandledRejection(event);

      expect(result).toBe(true);
      expect(event.preventDefault).not.toHaveBeenCalled();
    });
  });

  describe('handleError', () => {
    it('prevents default for extension errors', () => {
      const event = {
        error: { message: 'message channel closed' },
        preventDefault: vi.fn(),
      } as unknown as ErrorEvent;

      const result = handleError(event);

      expect(result).toBe(false);
      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('checks message if error missing', () => {
      const event = {
        error: null,
        message: 'ChunkLoadError: Loading chunk failed',
        preventDefault: vi.fn(),
      } as unknown as ErrorEvent;

      const result = handleError(event);

      expect(result).toBe(false);
    });

    it('returns true for normal errors', () => {
      const event = {
        error: new Error('Normal error'),
        preventDefault: vi.fn(),
      } as unknown as ErrorEvent;

      const result = handleError(event);

      expect(result).toBe(true);
    });
  });

  describe('handleVueError', () => {
    it('returns false for extension errors', () => {
      const result = handleVueError({ message: 'message channel closed' }, 'Component.vue');

      expect(result).toBe(false);
      expect(consoleWarnSpy).toHaveBeenCalled();
    });

    it('returns undefined for normal errors', () => {
      const result = handleVueError(new Error('Normal error'), 'Component.vue');

      expect(result).toBeUndefined();
    });
  });
});
