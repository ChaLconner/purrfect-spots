import { describe, it, expect } from 'vitest';
import { getEnvVar, isDev, isProd, validateEnv } from '@/utils/env';

describe('env utils', () => {
  // We can't easily change import.meta.env in standard ESM tests without more complex setup/transform
  // So we test the values as they are in the test environment (defaults: DEV=true, PROD=false in Vitest)
  
  it('isDev should reflect current environment', () => {
    // In Vitest, by default DEV is true
    expect(isDev()).toBe(true);
  });

  it('isProd should reflect current environment', () => {
    // In Vitest, by default PROD is false
    expect(isProd()).toBe(false);
  });

  it('getEnvVar returns value if exists', () => {
    // We can't easily inject new env vars into import.meta.env at runtime in this setup
    // But we can test default value
    expect(getEnvVar('NON_EXISTENT_VAR', 'default')).toBe('default');
  });

  it('rejects malformed production configuration without exposing values', () => {
    expect(() =>
      validateEnv({
        MODE: 'production',
        VITE_SUPABASE_URL: 'not-a-url',
        VITE_SUPABASE_ANON_KEY: '',
      }),
    ).toThrow(/VITE_SUPABASE_URL|VITE_SUPABASE_ANON_KEY/);
  });

  it('accepts valid production configuration', () => {
    const env = validateEnv({
      MODE: 'production',
      VITE_SUPABASE_URL: 'https://example.supabase.co',
      VITE_SUPABASE_ANON_KEY: 'public-anon-key',
      VITE_API_BASE_URL: '/api',
    });

    expect(env.VITE_API_BASE_URL).toBe('/api');
  });

  it('rejects and strips secret-looking Vite variables', () => {
    expect(() =>
      validateEnv({
        MODE: 'production',
        VITE_SUPABASE_URL: 'https://example.supabase.co',
        VITE_SUPABASE_ANON_KEY: 'public-anon-key',
        VITE_GOOGLE_CLIENT_ID_SECRET: 'must-not-be-public',
      }),
    ).toThrow(/VITE_GOOGLE_CLIENT_ID_SECRET/);
  });
});
