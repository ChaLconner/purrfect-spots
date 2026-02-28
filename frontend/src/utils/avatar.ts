/**
 * Utility functions for user avatars
 */

export const getAvatarFallback = (name?: string | null): string => {
  if (!name) return '/default-avatar.svg';
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=EBE4DD&color=C26D45`;
};

export const handleAvatarError = (event: Event, name?: string | null): void => {
  const target = event.target as HTMLImageElement;
  const fallbackUrl = getAvatarFallback(name);

  // Use proper URL parsing to check the hostname instead of substring matching
  // to prevent bypasses like "evil.com?q=ui-avatars.com"
  let isAvatarService = false;
  try {
    const parsedUrl = new URL(target.src);
    isAvatarService = parsedUrl.hostname === 'ui-avatars.com';
  } catch {
    // Invalid URL - not an avatar service URL
  }

  if (target.src !== fallbackUrl && !isAvatarService) {
    target.src = fallbackUrl;
  }
};
