/**
 * Utility functions for user avatars
 */

export const getAvatarFallback = (name?: string | null): string => {
  if (!name) return '/cat-icon.webp';
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=EBE4DD&color=C26D45`;
};

export const isAvatarUrl = (url?: string | null): boolean => {
  if (!url) return false;

  try {
    const parsedUrl = new URL(url, globalThis.location?.origin);
    const hostname = parsedUrl.hostname.toLowerCase();

    return (
      hostname === 'ui-avatars.com' ||
      hostname === 'lh3.googleusercontent.com' ||
      hostname.endsWith('.googleusercontent.com') ||
      hostname === 'avatars.githubusercontent.com' ||
      hostname.endsWith('.githubusercontent.com') ||
      hostname === 'cdn.discordapp.com' ||
      hostname.endsWith('.discordapp.com')
    );
  } catch {
    return false;
  }
};

export const handleAvatarError = (event: Event, name?: string | null): void => {
  const target = event.target as HTMLImageElement;
  const fallbackUrl = getAvatarFallback(name);

  if (target.src !== fallbackUrl && !isAvatarUrl(target.src)) {
    target.src = fallbackUrl;
  }
};
