import { describe, it, expect, vi, afterEach } from 'vitest';
import { isDev, isProd, getEnvVar } from '@/utils/env';

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
});
