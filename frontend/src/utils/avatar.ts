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
  if (target.src !== fallbackUrl && !target.src.includes('ui-avatars.com')) {
    target.src = fallbackUrl;
  }
};
