import { describe, expect, it } from 'vitest';
import { getAvatarFallback, handleAvatarError, isAvatarUrl } from '@/utils/avatar';

describe('avatar utilities', () => {
  it('builds a ui-avatar fallback from a display name', () => {
    expect(getAvatarFallback('Milo Cat')).toBe(
      'https://ui-avatars.com/api/?name=Milo%20Cat&background=EBE4DD&color=C26D45'
    );
  });

  it('uses the local cat icon when no display name is available', () => {
    expect(getAvatarFallback()).toBe('/cat-icon.webp');
    expect(getAvatarFallback(null)).toBe('/cat-icon.webp');
  });

  it.each([
    'https://ui-avatars.com/api/?name=Cat',
    'https://lh3.googleusercontent.com/a/avatar',
    'https://photos.googleusercontent.com/a/avatar',
    'https://avatars.githubusercontent.com/u/1',
    'https://media.githubusercontent.com/avatar.png',
    'https://cdn.discordapp.com/avatars/1/2.png',
    'https://images.discordapp.com/avatar.png',
  ])('accepts trusted avatar host %s', (url) => {
    expect(isAvatarUrl(url)).toBe(true);
  });

  it.each([
    undefined,
    null,
    'https://example.com/avatar.png',
    'not a url with spaces',
  ])('rejects untrusted or missing avatar url %s', (url) => {
    expect(isAvatarUrl(url)).toBe(false);
  });

  it('replaces an untrusted failed image source with a generated fallback', () => {
    const image = document.createElement('img');
    image.src = 'https://example.com/avatar.png';

    handleAvatarError({ target: image } as unknown as Event, 'Milo Cat');

    expect(image.src).toBe(getAvatarFallback('Milo Cat'));
  });

  it('keeps trusted avatar URLs unchanged after an image error', () => {
    const image = document.createElement('img');
    image.src = 'https://avatars.githubusercontent.com/u/1';

    handleAvatarError({ target: image } as unknown as Event, 'Milo Cat');

    expect(image.src).toBe('https://avatars.githubusercontent.com/u/1');
  });
});
