import { describe, expect, it } from 'vitest';

import { formatDate, formatTimestamp } from '@/utils/date';

describe('date utils', () => {
  it('formats dates as DD/MM/YYYY by default', () => {
    expect(formatDate('2026-04-20T00:00:00.000Z')).toBe('20/04/2026');
  });

  it('formats dates with Intl options and locale overrides', () => {
    expect(formatDate('2026-04-20T00:00:00.000Z', { month: 'long' }, 'en')).toBe('April');
    expect(formatDate('2026-04-20T00:00:00.000Z', { month: 'long' }, 'th')).toContain('เมษายน');
  });

  it('returns N/A for empty or invalid dates', () => {
    expect(formatDate(undefined)).toBe('N/A');
    expect(formatDate('not-a-date')).toBe('N/A');
    expect(formatTimestamp(undefined)).toBe('N/A');
    expect(formatTimestamp('not-a-date')).toBe('N/A');
  });

  it('formats timestamps with locale-aware clock output', () => {
    const englishTimestamp = formatTimestamp('2026-04-20T13:05:00.000Z', 'en');
    const thaiTimestamp = formatTimestamp('2026-04-20T13:05:00.000Z', 'th');

    expect(englishTimestamp).toContain('20/04/2026');
    expect(englishTimestamp).toMatch(/AM|PM/);
    expect(thaiTimestamp).toContain('20/04/2026');
    expect(thaiTimestamp.length).toBeGreaterThan('20/04/2026 '.length);
  });
});
