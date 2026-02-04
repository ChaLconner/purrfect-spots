/**
 * Lazy loading utilities for images and components
 */

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

  const setupObserver = () => {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            const src = img.dataset.src;
            if (src && !img.src) {
              img.src = src;
              img.onload = () => {
                img.classList.add('loaded');
              };
              img.onerror = () => {
                img.classList.add('error');
                img.src = 'https://placehold.co/400x300?text=Image+Error';
              };
              observer?.unobserve(img);
            }
          }
        });
      },
      {
        rootMargin,
        threshold,
      }
    );
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

  const setupObserver = () => {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            callback();
            observer?.disconnect();
          }
        });
      },
      {
        rootMargin,
        threshold,
      }
    );
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
