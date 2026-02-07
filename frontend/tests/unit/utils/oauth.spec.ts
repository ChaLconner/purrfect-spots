import { describe, it, expect } from 'vitest';
import {
  generateCodeVerifier,
  generateCodeChallenge,
  base64URLEncode,
  getGoogleAuthUrl,
} from '@/utils/oauth';

describe('OAuth Utils', () => {
  describe('base64URLEncode', () => {
    it('should encode correctly and be URL safe', () => {
      // "hello world" byte array
      const text = 'hello world';
      const array = new TextEncoder().encode(text);
      const encoded = base64URLEncode(array);
      
      // btoa("hello world") is "aGVsbG8gd29ybGQ="
      // URL safe replace = should remove =
      expect(encoded).toBe('aGVsbG8gd29ybGQ');
    });

    it('should handle special chars replacement', () => {
      // We need input that produces + and / in standard base64
      // + -> -
      // / -> _
      // Example: 0xFB, 0xFF (binary 11111011 11111111) -> +/8=
      const input = new Uint8Array([0xfb, 0xff, 0xff]);
      // btoa... +//w
      const encoded = base64URLEncode(input);
      expect(encoded).not.toContain('+');
      expect(encoded).not.toContain('/');
      expect(encoded).not.toContain('=');
    });
  });

  describe('generateCodeVerifier', () => {
    it('should generate a string of correct length and charset', () => {
      const verifier = generateCodeVerifier();
      expect(typeof verifier).toBe('string');
      expect(verifier.length).toBeGreaterThan(0);
      // PKCE verifier length usually 43-128 chars.
      // 32 bytes * 4/3 approx 43 chars.
      expect(verifier.length).toBeGreaterThanOrEqual(43);
    });
  });

  describe('generateCodeChallenge', () => {
    it('should generate a SHA-256 challenge', async () => {
      const verifier = 'test-verifier';
      const challenge = await generateCodeChallenge(verifier);
      expect(typeof challenge).toBe('string');
      expect(challenge).not.toBe(verifier);
    });
  });

  describe('getGoogleAuthUrl', () => {
    it('should constructs correct URL with params', async () => {
      const clientId = 'test-client-id';
      const redirectUri = 'http://localhost/callback';
      
      const { url, codeVerifier } = await getGoogleAuthUrl(clientId, redirectUri);
      
      expect(codeVerifier).toBeTruthy();
      
      const urlObj = new URL(url);
      expect(urlObj.origin).toBe('https://accounts.google.com');
      expect(urlObj.pathname).toBe('/o/oauth2/v2/auth');
      
      const params = urlObj.searchParams;
      expect(params.get('client_id')).toBe(clientId);
      expect(params.get('redirect_uri')).toBe(redirectUri);
      expect(params.get('response_type')).toBe('code');
      expect(params.get('code_challenge_method')).toBe('S256');
      expect(params.get('code_challenge')).toBeTruthy();
    });
  });
});
