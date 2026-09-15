/**
 * Utility functions for user avatars
 */

import { getEnvVar } from './env';

export const getAvatarFallback = (name?: string | null): string => {
  if (!name) return '/cat-icon.webp';
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=EBE4DD&color=C26D45`;
};

const isUiAvatarUrl = (url: string): boolean => {
  try {
    const parsedUrl = new URL(url, globalThis.location?.origin);
    return parsedUrl.protocol === 'https:' && parsedUrl.hostname.toLowerCase() === 'ui-avatars.com';
  } catch {
    return false;
  }
};

const isRelativeAvatarPath = (url: string): boolean => url.startsWith('/') && !url.startsWith('//');

const getConfiguredAvatarHosts = (): Set<string> => {
  const hosts = new Set<string>();
  for (const key of ['VITE_SUPABASE_URL', 'VITE_CDN_BASE_URL']) {
    const configuredUrl = getEnvVar(key);
    if (!configuredUrl) continue;
    try {
      const parsedUrl = new URL(configuredUrl);
      if (parsedUrl.protocol === 'https:') hosts.add(parsedUrl.hostname.toLowerCase());
    } catch {
      // Invalid optional configuration is already reported by env validation.
    }
  }
  return hosts;
};

const isApprovedAvatarHost = (hostname: string, configuredHosts: Set<string>): boolean => {
  return (
    configuredHosts.has(hostname) ||
    hostname === 'ui-avatars.com' ||
    hostname === 'lh3.googleusercontent.com' ||
    hostname.endsWith('.googleusercontent.com') ||
    hostname === 'avatars.githubusercontent.com' ||
    hostname.endsWith('.githubusercontent.com') ||
    hostname === 'cdn.discordapp.com' ||
    hostname.endsWith('.discordapp.com')
  );
};

export const isAvatarUrl = (url?: string | null): boolean => {
  if (!url) return false;

  const trimmedUrl = url.trim();
  if (!trimmedUrl || isRelativeAvatarPath(trimmedUrl)) return isRelativeAvatarPath(trimmedUrl);
  if (!/^[a-z][a-z\d+.-]*:/i.test(trimmedUrl)) return false;

  try {
    const parsedUrl = new URL(trimmedUrl, globalThis.location?.origin);
    if (parsedUrl.username || parsedUrl.password || parsedUrl.hash) return false;
    if (parsedUrl.protocol !== 'https:') {
      return parsedUrl.origin === globalThis.location?.origin;
    }

    const hostname = parsedUrl.hostname.toLowerCase();
    return parsedUrl.origin === globalThis.location?.origin || isApprovedAvatarHost(hostname, getConfiguredAvatarHosts());
  } catch {
    return false;
  }
};

/** Return only an allowlisted avatar URL; unsafe server data becomes null. */
export const sanitizeAvatarUrl = (url?: string | null): string | null => {
  if (!url || !isAvatarUrl(url)) return null;
  return url.trim();
};

/** Return a safe avatar URL with a local/generated fallback. */
export const getAvatarSrc = (url?: string | null, name?: string | null): string => {
  return sanitizeAvatarUrl(url) || getAvatarFallback(name);
};

export const handleAvatarError = (event: Event, name?: string | null): void => {
  const target = event.target as HTMLImageElement;
  if (!target) return;

  const fallbackUrl = getAvatarFallback(name);
  const staticFallback = '/cat-icon.webp';

  if (target.src !== fallbackUrl && !isUiAvatarUrl(target.src)) {
    target.src = fallbackUrl;
  } else if (target.src !== staticFallback && !target.src.endsWith(staticFallback)) {
    target.src = staticFallback;
  }
};
