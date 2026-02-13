/**
 * SEO Meta Tags Composable
 *
 * Provides utilities for managing document meta tags for SEO.
 * Useful for dynamic pages like Gallery where content changes.
 */

interface MetaTagOptions {
  title?: string;
  description?: string;
  image?: string;
  url?: string;
  type?: string;
}

const SITE_NAME = 'Purrfect Spots';
const DEFAULT_TITLE = `Home | ${SITE_NAME}`;
const DEFAULT_DESCRIPTION =
  'Discover and share adorable cat photos from around the world. Find cat-friendly spots near you.';
const DEFAULT_IMAGE = '/og-image.png';

/**
 * Set document title and meta tags
 */
export function setMetaTags(options: MetaTagOptions) {
  const {
    title = DEFAULT_TITLE,
    description = DEFAULT_DESCRIPTION,
    image = DEFAULT_IMAGE,
    url = globalThis.location.href,
    type = 'website',
  } = options;

  // Set document title
  document.title = title;

  // Helper to set or create meta tag
  const setMeta = (name: string, content: string, property = false) => {
    const attr = property ? 'property' : 'name';
    let meta = document.querySelector(`meta[${attr}="${name}"]`) as HTMLMetaElement;

    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute(attr, name);
      document.head.appendChild(meta);
    }

    meta.content = content;
  };

  // Standard meta tags
  setMeta('description', description);

  // Open Graph tags
  setMeta('og:title', title, true);
  setMeta('og:description', description, true);
  setMeta('og:image', image, true);
  setMeta('og:url', url, true);
  setMeta('og:type', type, true);

  // Canonical URL
  let canonical = document.querySelector('link[rel="canonical"]') as HTMLLinkElement;
  if (!canonical) {
    canonical = document.createElement('link');
    canonical.rel = 'canonical';
    document.head.appendChild(canonical);
  }
  canonical.href = url;

  // Twitter Card tags
  setMeta('twitter:card', 'summary_large_image');
  setMeta('twitter:title', title);
  setMeta('twitter:description', description);
  setMeta('twitter:image', image);
}

/**
 * Reset meta tags to defaults
 */
export function resetMetaTags() {
  setMetaTags({
    title: DEFAULT_TITLE,
    description: DEFAULT_DESCRIPTION,
    image: DEFAULT_IMAGE,
    type: 'website',
  });
}

/**
 * Composable for managing SEO in components
 */
export function useSeo() {
  return {
    setMetaTags,
    resetMetaTags,
    SITE_NAME,
    DEFAULT_TITLE,
    DEFAULT_DESCRIPTION,
  };
}
