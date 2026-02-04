import { ref, onMounted, onUnmounted, type Ref } from 'vue';

interface UseImageLoaderOptions {
  src: string;
  lazy?: boolean;
  viewportMargin?: string;
  threshold?: number;
}

interface UseImageLoaderReturn {
  isLoaded: Ref<boolean>;
  hasError: Ref<boolean>;
  isIntersecting: Ref<boolean>;
  handleLoad: () => void;
  handleError: (event: Event) => void;
  retry: () => void;
  imageRef: Ref<HTMLElement | null>;
}

export function useImageLoader(options: UseImageLoaderOptions): UseImageLoaderReturn {
  const { src, lazy = true, viewportMargin = '200px', threshold = 0.01 } = options;

  const isLoaded = ref(false);
  const hasError = ref(false);
  const isIntersecting = ref(!lazy);
  const imageRef = ref<HTMLElement | null>(null);
  let observer: IntersectionObserver | null = null;

  const handleLoad = () => {
    isLoaded.value = true;
  };

  const handleError = (event: Event) => {
    hasError.value = true;
    console.error('Image failed to load:', src, event);
  };

  const retry = () => {
    hasError.value = false;
    isLoaded.value = false;
    // Force re-render if needed, but usually src change or just retry logic in component handles it.
    // Here we can reset intersection if we want to force re-observation,
    // but usually user clicks retry.
    if (lazy) {
      isIntersecting.value = false;
      setTimeout(() => {
        isIntersecting.value = true;
      }, 100);
    }
  };

  onMounted(() => {
    if (!lazy || !imageRef.value) {
      isIntersecting.value = true;
      return;
    }

    if ('IntersectionObserver' in globalThis) {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              isIntersecting.value = true;
              if (observer) observer.disconnect();
            }
          });
        },
        {
          rootMargin: viewportMargin,
          threshold: threshold,
        }
      );
      observer.observe(imageRef.value);
    } else {
      // Fallback for browsers without IntersectionObserver
      isIntersecting.value = true;
    }
  });

  onUnmounted(() => {
    if (observer) {
      observer.disconnect();
    }
  });

  return {
    isLoaded,
    hasError,
    isIntersecting,
    handleLoad,
    handleError,
    retry,
    imageRef,
  };
}
