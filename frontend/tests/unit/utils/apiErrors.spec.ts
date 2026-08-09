import { describe, expect, it } from 'vitest';

import { ApiError, ApiErrorTypes, formatApiErrorMessage, formatFormErrorMessage } from '@/utils/apiErrors';

describe('API error formatting', () => {
  it('maps transport errors to actionable messages', () => {
    expect(formatApiErrorMessage(new ApiError(ApiErrorTypes.NETWORK_ERROR, 'offline'))).toContain('connect');
    expect(formatApiErrorMessage(new ApiError(ApiErrorTypes.AUTHENTICATION_ERROR, 'expired'))).toContain('session');
  });

  it('uses the form status-code fallback only for status-code errors', () => {
    expect(formatFormErrorMessage(new Error('status code 422'), 'fallback', 'server status')).toBe('server status');
    expect(formatFormErrorMessage(new Error('invalid name'), 'fallback', 'server status')).toBe('invalid name');
  });
});
