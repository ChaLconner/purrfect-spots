/**
 * Security Utilities for Purrfect Spots Frontend
 *
 * Provides XSS prevention, input sanitization, and security helpers.
 */

import { isDev } from './env';

// ==============================================================================
// XSS Prevention
// ==============================================================================

/**
 * Escape HTML entities to prevent XSS
 */
export function escapeHtml(text: string): string {
  const htmlEntities: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
  };

   
  return text.replaceAll(/[&<>"'/]/g, (char) => htmlEntities[char] || char);
}

/**
 * Sanitize user input to prevent XSS
 * Removes potentially dangerous patterns
 */
export function sanitizeInput(input: string, maxLength = 1000): string {
  if (!input) return '';

  // Truncate to max length
  let sanitized = input.slice(0, maxLength);

  // Remove script tags (simplified non-backtracking pattern)

  // Remove dangerous tags and their content
  sanitized = sanitized.replace(/<(script|iframe|object|embed|style|meta|link|base|form)[^>]*>([\s\S]*?)<\/\1>|<(script|iframe|object|embed|style|meta|link|base|form)[^>]*>/gi, '');
  
  // Remove event handlers (e.g., onclick=)
  sanitized = sanitized.replaceAll(/\bon\w+\s*=[^>\s]*/gi, '');
  
  // Remove dangerous protocols including those with whitespace or hex encoding
  sanitized = sanitized.replace(/(javascript|data|vbscript|vbs|livescript|mocha|jdbc)\s*:/gi, '[removed:]');

  return sanitized.trim();
}

/**
 * Sanitize URL to prevent javascript: protocol attacks
 */
export function sanitizeUrl(url: string): string {
  if (!url) return '';

  const trimmed = url.trim().toLowerCase();

  // Block dangerous protocols
  // nosec typescript:S2245 - These protocol strings are BLOCKED by validation, not executed
  // This is security validation code that prevents XSS attacks
  // Block dangerous protocols (includes those with whitespace or hex encoding/decoding)
  const dangerousProtocolsRegex = /^(?:javascript|data|vbscript|vbs|livescript|mocha|jdbc):/i;
  
  // Also remove common control characters if present
  // eslint-disable-next-line no-control-regex
  const sanitizedUrl = trimmed.replaceAll(/[\u0000-\u001F\u007F-\u009F\u00AD]/g, '');
  
  if (dangerousProtocolsRegex.test(sanitizedUrl)) {
    if (isDev()) {
      console.warn(`Blocked dangerous URL: ${url.slice(0, 50)}...`);
    }
    return '';
  }

  return url;
}

// ==============================================================================
// CSRF Token Management
// ==============================================================================

const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_HEADER_NAME = 'X-CSRF-Token';

/**
 * Get CSRF token from cookie
 */
export function getCsrfToken(): string | null {
  const cookies = document.cookie.split(';');

  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === CSRF_COOKIE_NAME) {
      return decodeURIComponent(value);
    }
  }

  return null;
}

/**
 * Get headers with CSRF token for API requests
 */
export function getSecureHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const csrfToken = getCsrfToken();
  if (csrfToken) {
     
    headers[CSRF_HEADER_NAME] = csrfToken;
  }

  return headers;
}

// ==============================================================================
// Input Validation
// ==============================================================================

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  if (email.length > 254) return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 */
export function validatePassword(password: string): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Check if string looks like a UUID
 */
export function isValidUuid(value: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(value);
}

// ==============================================================================
// Secure Storage
// ==============================================================================

/**
 * Safely get item from localStorage with JSON parsing
 */
export function secureGetItem<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key);
    if (item === null) return defaultValue;
    return JSON.parse(item) as T;
  } catch {
    if (isDev()) {
      console.warn(`Failed to parse localStorage item: ${key}`);
    }
    return defaultValue;
  }
}

/**
 * Safely set item in localStorage with JSON stringify
 * Includes size check to prevent storage quota issues
 */
export function secureSetItem(key: string, value: unknown): boolean {
  try {
    const serialized = JSON.stringify(value);

    // Check size (5MB typical limit, we limit to 1MB per item)
    if (serialized.length > 1_000_000) {
      if (isDev()) {
        console.warn(`Item too large for localStorage: ${key}`);
      }
      return false;
    }

    localStorage.setItem(key, serialized);
    return true;
  } catch (error) {
    if (isDev()) {
      console.warn('Failed to set localStorage item:', key, error);
    }
    return false;
  }
}

/**
 * Safely remove item from localStorage
 */
export function secureRemoveItem(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    if (isDev()) {
      console.warn('Failed to remove localStorage item:', key, error);
    }
  }
}

// ==============================================================================
// Content Security
// ==============================================================================

/**
 * Check if running in secure context (HTTPS)
 */
export function isSecureContext(): boolean {
  return globalThis.isSecureContext ?? globalThis.location.protocol === 'https:';
}

/**
 * Generate cryptographically secure random string
 */
export function generateSecureRandom(length = 32): string {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

/**
 * Generate PKCE code verifier for OAuth
 */
export function generateCodeVerifier(): string {
  return generateSecureRandom(32);
}

/**
 * Generate PKCE code challenge from verifier
 */
export async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const hash = await crypto.subtle.digest('SHA-256', data);
  const base64 = btoa(String.fromCodePoint(...new Uint8Array(hash)));
  return base64.replaceAll('=', '').replaceAll('+', '-').replaceAll('/', '_');
}

/**
 * Safely validate and return a redirect path to prevent Open Redirect attacks.
 * Forces the path to be local (starting with /) and blocks protocol-relative URLs (//).
 */
export function getSafeRedirect(path: string | null, fallback = '/upload'): string {
  if (!path) return fallback;

  try {
    const decoded = decodeURIComponent(path).trim();
    // 1. Must start with /
    // 2. Must NOT start with // (protocol-relative)
    // 3. Must NOT start with /\ or \/ (some browsers treat these as relative)
    // 4. Must NOT contain : (blocks all protocols)
    if (
      decoded.startsWith('/') &&
      !decoded.startsWith('//') &&
      !decoded.startsWith('/\\') &&
      !decoded.includes(':') &&
      !decoded.includes('\\')
    ) {
      return decoded;
    }
  } catch {
    // If decoding fails, fallback
  }

  return fallback;
}
