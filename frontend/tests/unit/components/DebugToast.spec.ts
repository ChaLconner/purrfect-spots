import { showSuccess } from '@/store/toast';
import { describe, it, expect, vi } from 'vitest';

describe('Debug Toast', () => {
  it('should import', () => {
    expect(showSuccess).toBeDefined();
  });
});
