import { describe, expect, it } from 'vitest';
import { distanceInKm } from '@/utils/geo';

describe('distanceInKm', () => {
  it('returns zero for identical points', () => {
    expect(distanceInKm({ lat: 13.7563, lng: 100.5018 }, { lat: 13.7563, lng: 100.5018 })).toBe(0);
  });

  it('returns a useful nearby distance for radius filtering', () => {
    const distance = distanceInKm(
      { lat: 13.7563, lng: 100.5018 },
      { lat: 13.765, lng: 100.5018 }
    );

    expect(distance).toBeGreaterThan(0.9);
    expect(distance).toBeLessThan(1.1);
  });
});
