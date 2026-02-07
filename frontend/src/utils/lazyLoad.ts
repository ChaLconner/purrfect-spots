/**
 * Lazy loading utilities for images and components
 */

// Shared image load handler
function handleImageLoad(img: HTMLImageElement): void {
  img.classList.add('loaded');
}

// Shared image error handler
function handleImageError(img: HTMLImageElement): void {
  img.classList.add('error');
  img.src = 'https://placehold.co/400x300?text=Image+Error';
}

// Helper to create an IntersectionObserver with common options
function createIntersectionObserver(
  callback: IntersectionObserverCallback,
  rootMargin: string,
  threshold: number
): IntersectionObserver {
  return new IntersectionObserver(callback, { rootMargin, threshold });
}

// Image lazy loading with Intersection Observer
export function useImageLazyLoad(
  imageElements: Element[],
  options: {
    rootMargin?: string;
    threshold?: number;
  } = {}
) {
  const { rootMargin = '50px', threshold = 0.1 } = options;

  let observer: IntersectionObserver | null = null;

  const handleIntersection = (entries: IntersectionObserverEntry[]) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        const src = img.dataset.src;
        if (src && !img.src) {
          img.src = src;
          img.onload = () => handleImageLoad(img);
          img.onerror = () => handleImageError(img);
          observer?.unobserve(img);
        }
      }
    }
  };

  const setupObserver = () => {
    observer = createIntersectionObserver(handleIntersection, rootMargin, threshold);
  };

  const observeImages = () => {
    if (!observer) {
      setupObserver();
    }

    imageElements.forEach((element) => {
      const img = element.querySelector('img');
      if (img) {
        observer?.observe(img);
      }
    });
  };

  const disconnect = () => {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
  };

  return {
    observeImages,
    disconnect,
  };
}

// Component lazy loading with Intersection Observer
export function useComponentLazyLoad(
  elementId: string,
  callback: () => void,
  options: {
    rootMargin?: string;
    threshold?: number;
  } = {}
) {
  const { rootMargin = '50px', threshold = 0.1 } = options;

  let observer: IntersectionObserver | null = null;

  const handleIntersection = (entries: IntersectionObserverEntry[]) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        callback();
        observer?.disconnect();
        break;
      }
    }
  };

  const setupObserver = () => {
    observer = createIntersectionObserver(handleIntersection, rootMargin, threshold);
  };

  const observe = () => {
    const element = document.getElementById(elementId);
    if (element) {
      if (!observer) {
        setupObserver();
      }
      observer?.observe(element);
    }
  };

  const disconnect = () => {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
  };

  return {
    observe,
    disconnect,
  };
}

// Script lazy loading for external resources
export function loadScript(
  src: string,
  callback?: () => void,
  errorCallback?: () => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    // Check if script is already loaded
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      callback?.();
      resolve();
    };

    script.onerror = () => {
      errorCallback?.();
      reject(new Error(`Failed to load script: ${src}`));
    };

    document.head.appendChild(script);
  });
}

// Preload images
export function preloadImages(urls: string[]): Promise<void[]> {
  return Promise.all(
    urls.map((url) => {
      return new Promise<void>((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = () => reject(new Error(`Failed to preload image: ${url}`));
        img.src = url;
      });
    })
  );
}
