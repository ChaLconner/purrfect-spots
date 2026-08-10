import { describe, expect, it } from 'vitest';

import { calculateScaledDimensions } from '@/utils/imageDimensions';

describe('calculateScaledDimensions', () => {
  it('preserves aspect ratio while applying the canvas and width bounds', () => {
    expect(calculateScaledDimensions(8000, 4000, 1000, undefined, 4096)).toEqual({ width: 1000, height: 500 });
  });

  it('applies the height bound after width scaling', () => {
    expect(calculateScaledDimensions(1000, 2000, 900, 600)).toEqual({ width: 300, height: 600 });
  });
});
