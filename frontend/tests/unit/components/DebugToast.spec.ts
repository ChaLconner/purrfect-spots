import { showSuccess } from '@/store/toast';
import { describe, it, expect } from 'vitest';

describe('Debug Toast', () => {
  it('should import', () => {
    expect(showSuccess).toBeDefined();
  });
});
