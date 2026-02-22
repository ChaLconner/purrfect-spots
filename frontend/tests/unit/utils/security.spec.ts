import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  escapeHtml,
  sanitizeInput,
  sanitizeUrl,
  getCsrfToken,
  getSecureHeaders,
  isValidEmail,
  validatePassword,
  isValidUuid,
  secureGetItem,
  secureSetItem,
  secureRemoveItem,
  isSecureContext,
  generateSecureRandom,
  generateCodeVerifier,
  generateCodeChallenge,
} from '@/utils/security';

vi.mock('@/utils/env', () => ({
  isDev: vi.fn(() => false),
}));

describe('security utils', () => {
  describe('escapeHtml', () => {
    it('escapes HTML entities', () => {
      expect(escapeHtml('<script>alert("xss")</script>')).toBe(
        '&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;'
      );
    });

    it('escapes ampersand', () => {
      expect(escapeHtml('foo & bar')).toBe('foo &amp; bar');
    });

    it('escapes single quotes', () => {
      expect(escapeHtml("it's")).toBe('it&#x27;s');
    });

    it('returns unchanged text without special chars', () => {
      expect(escapeHtml('hello world')).toBe('hello world');
    });
  });

  describe('sanitizeInput', () => {
    it('removes script tags', () => {
      expect(sanitizeInput('<script>alert(1)</script>hello')).toBe('hello');
    });

    it('removes on event handlers', () => {
      const result = sanitizeInput('<img onerror="alert(1)" src="x">');
      expect(result).not.toContain('onerror=');
      expect(result).toContain('src="x"');
    });

    it('removes javascript: protocol', () => {
      expect(sanitizeInput('javascript:alert(1)')).toBe('alert(1)');
    });

    it('truncates to max length', () => {
      const long = 'a'.repeat(2000);
      const result = sanitizeInput(long, 500);
      expect(result.length).toBe(500);
    });

    it('returns empty string for null/undefined', () => {
      expect(sanitizeInput(null as any)).toBe('');
      expect(sanitizeInput(undefined as any)).toBe('');
    });

    it('trims whitespace', () => {
      expect(sanitizeInput('  hello  ')).toBe('hello');
    });
  });

  describe('sanitizeUrl', () => {
    it('blocks javascript: protocol', () => {
      expect(sanitizeUrl('javascript:alert(1)')).toBe('');
    });

    it('blocks data:text/html protocol', () => {
      expect(sanitizeUrl('data:text/html,<script>alert(1)</script>')).toBe('');
    });

    it('blocks vbscript: protocol', () => {
      expect(sanitizeUrl('vbscript:msgbox(1)')).toBe('');
    });

    it('allows safe URLs', () => {
      expect(sanitizeUrl('https://example.com')).toBe('https://example.com');
    });

    it('returns empty string for null/undefined', () => {
      expect(sanitizeUrl(null as any)).toBe('');
      expect(sanitizeUrl(undefined as any)).toBe('');
    });

    it('is case insensitive', () => {
      expect(sanitizeUrl('JAVASCRIPT:alert(1)')).toBe('');
      expect(sanitizeUrl('JavaScript:alert(1)')).toBe('');
    });
  });

  describe('getCsrfToken', () => {
    let originalCookie: string;

    beforeEach(() => {
      originalCookie = document.cookie;
    });

    afterEach(() => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: originalCookie,
      });
    });

    it('returns token from cookie', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=test-token-123',
      });
      expect(getCsrfToken()).toBe('test-token-123');
    });

    it('returns null when cookie not present', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: '',
      });
      expect(getCsrfToken()).toBeNull();
    });

    it('decodes URI encoded tokens', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=token%20with%20spaces',
      });
      expect(getCsrfToken()).toBe('token with spaces');
    });
  });

  describe('getSecureHeaders', () => {
    it('returns headers with content type', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: '',
      });
      const headers = getSecureHeaders();
      expect(headers['Content-Type']).toBe('application/json');
    });

    it('includes CSRF token when present', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=my-csrf-token',
      });
      const headers = getSecureHeaders();
      expect(headers['X-CSRF-Token']).toBe('my-csrf-token');
    });
  });

  describe('isValidEmail', () => {
    it('validates correct emails', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name@domain.co')).toBe(true);
    });

    it('rejects invalid emails', () => {
      expect(isValidEmail('invalid')).toBe(false);
      expect(isValidEmail('no@domain')).toBe(false);
      expect(isValidEmail('@nodomain.com')).toBe(false);
    });

    it('rejects emails over 254 chars', () => {
      const longEmail = 'a'.repeat(250) + '@a.co';
      expect(isValidEmail(longEmail)).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('validates strong passwords', () => {
      const result = validatePassword('Password1');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('requires 8 characters', () => {
      const result = validatePassword('Pass1');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Password must be at least 8 characters');
    });

    it('requires uppercase letter', () => {
      const result = validatePassword('password1');
      expect(result.errors).toContain('Password must contain at least one uppercase letter');
    });

    it('requires lowercase letter', () => {
      const result = validatePassword('PASSWORD1');
      expect(result.errors).toContain('Password must contain at least one lowercase letter');
    });

    it('requires number', () => {
      const result = validatePassword('Password');
      expect(result.errors).toContain('Password must contain at least one number');
    });
  });

  describe('isValidUuid', () => {
    it('validates UUIDs', () => {
      expect(isValidUuid('123e4567-e89b-12d3-a456-426614174000')).toBe(true);
      expect(isValidUuid('123E4567-E89B-12D3-A456-426614174000')).toBe(true);
    });

    it('rejects invalid UUIDs', () => {
      expect(isValidUuid('not-a-uuid')).toBe(false);
      expect(isValidUuid('123e4567-e89b-12d3-a456')).toBe(false);
    });
  });

  describe('secureGetItem', () => {
    let storage: Record<string, string> = {};

    beforeEach(() => {
      storage = {};
      vi.stubGlobal('localStorage', {
        getItem: (key: string) => storage[key] ?? null,
        setItem: (key: string, value: string) => {
          storage[key] = value;
        },
      });
    });

    it('returns parsed JSON', () => {
      storage['test'] = JSON.stringify({ foo: 'bar' });
      expect(secureGetItem('test', {})).toEqual({ foo: 'bar' });
    });

    it('returns default on parse error', () => {
      storage['test'] = 'not json';
      expect(secureGetItem('test', { default: true })).toEqual({ default: true });
    });

    it('returns default when key missing', () => {
      expect(secureGetItem('missing', 'default')).toBe('default');
    });
  });

  describe('secureSetItem', () => {
    let storage: Record<string, string> = {};
    let mockSetItem: ReturnType<typeof vi.fn>;

    beforeEach(() => {
      storage = {};
      mockSetItem = vi.fn((key: string, value: string) => {
        storage[key] = value;
      });
      vi.stubGlobal('localStorage', {
        setItem: mockSetItem,
      });
    });

    it('stores JSON stringified value', () => {
      const result = secureSetItem('key', { foo: 'bar' });
      expect(result).toBe(true);
      expect(mockSetItem).toHaveBeenCalledWith('key', '{"foo":"bar"}');
    });

    it('returns false for items over 1MB', () => {
      const largeValue = 'x'.repeat(1_100_000);
      const result = secureSetItem('key', largeValue);
      expect(result).toBe(false);
    });

    it('returns false on storage error', () => {
      mockSetItem.mockImplementation(() => {
        throw new Error('Quota exceeded');
      });
      const result = secureSetItem('key', 'value');
      expect(result).toBe(false);
    });
  });

  describe('secureRemoveItem', () => {
    let mockRemoveItem: ReturnType<typeof vi.fn>;

    beforeEach(() => {
      mockRemoveItem = vi.fn();
      vi.stubGlobal('localStorage', {
        removeItem: mockRemoveItem,
      });
    });

    it('removes item', () => {
      secureRemoveItem('key');
      expect(mockRemoveItem).toHaveBeenCalledWith('key');
    });

    it('handles errors gracefully', () => {
      mockRemoveItem.mockImplementation(() => {
        throw new Error('Failed');
      });
      expect(() => secureRemoveItem('key')).not.toThrow();
    });
  });

  describe('isSecureContext', () => {
    it('returns isSecureContext when available', () => {
      vi.stubGlobal('isSecureContext', true);
      expect(isSecureContext()).toBe(true);
    });

    it('checks https protocol as fallback', () => {
      vi.stubGlobal('isSecureContext', undefined);
      vi.stubGlobal('location', { protocol: 'https:' });
      expect(isSecureContext()).toBe(true);
    });
  });

  describe('generateSecureRandom', () => {
    it('generates hex string of correct length', () => {
      const result = generateSecureRandom(16);
      expect(result).toHaveLength(32);
      expect(/^[0-9a-f]+$/.test(result)).toBe(true);
    });

    it('uses default length of 32', () => {
      const result = generateSecureRandom();
      expect(result).toHaveLength(64);
    });
  });

  describe('generateCodeVerifier', () => {
    it('generates 64 char hex string', () => {
      const result = generateCodeVerifier();
      expect(result).toHaveLength(64);
    });
  });

  describe('generateCodeChallenge', () => {
    it('generates base64url encoded SHA256 hash', async () => {
      const challenge = await generateCodeChallenge('test-verifier');
      expect(challenge).not.toContain('=');
      expect(challenge).not.toContain('+');
      expect(challenge).not.toContain('/');
    });
  });
});
