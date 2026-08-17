import { ref, shallowRef, watch, nextTick, type Ref } from 'vue';
import { GalleryService } from '@/services/galleryService';
import { useCatsStore } from '@/stores';
import { GALLERY_CONFIG } from '@/utils/constants';
import { isRequestAborted } from '@/utils/api';
import type { CatLocation } from '@/types/api';

const MAX_VISIBLE_IMAGES = 1000;

interface GalleryPageResult {
  images: CatLocation[];
  hasMore: boolean;
  total: number;
}

async function fetchGalleryPage(
  query: string,
  page: number,
  limit: number,
  signal: AbortSignal
): Promise<GalleryPageResult> {
  if (query) {
    const response = await GalleryService.search(
      { query, page, limit },
      { signal }
    );
    const total = response.total || 0;
    return {
      images: response.results || [],
      total,
      hasMore: page * limit < total,
    };
  }

  const response = await GalleryService.getImages({ page, limit }, { signal });
  return {
    images: response.images || [],
    hasMore: response.pagination?.has_more || false,
    total: response.pagination?.total || 0,
  };
}

export function useGalleryState(): {
  loading: Ref<boolean>;
  loadingMore: Ref<boolean>;
  error: Ref<string>;
  visibleImages: Ref<CatLocation[]>;
  hasMoreImages: Ref<boolean>;
  totalImages: Ref<number>;
  fetchImages: (callback?: () => void) => void;
  loadMoreImages: () => void;
  cleanupPreloads: () => void;
} {
  const catsStore = useCatsStore();

  const loading = ref(catsStore.galleryLocations.length === 0);
  const loadingMore = ref(false);
  const error = ref('');
  const visibleImages = shallowRef<CatLocation[]>(catsStore.galleryLocations.slice(-MAX_VISIBLE_IMAGES));

  const currentPage = ref(1);
  const imagesPerPage = GALLERY_CONFIG.IMAGES_PER_PAGE;
  const hasMoreImages = ref(catsStore.galleryLocations.length > 0);
  const totalImages = ref(catsStore.galleryLocations.length);
  let latestRequestId = 0;
  let inFlightRequestKey: string | null = null;
  let inFlightRequest: Promise<void> | null = null;
  let lastLoadMoreRequestAt = 0;
  let activeAbortController: AbortController | null = null;

  const preloadedLinks: HTMLLinkElement[] = [];

  const appendUniqueImages = (current: CatLocation[], incoming: CatLocation[]): CatLocation[] => {
    const currentIds = new Set(current.map((image) => image.id));
    const uniqueIncoming = incoming.filter((image) => !currentIds.has(image.id));
    return [...current, ...uniqueIncoming].slice(-MAX_VISIBLE_IMAGES);
  };

  const applyGalleryPage = (page: GalleryPageResult, reset: boolean, callback?: () => void): void => {
    visibleImages.value = reset
      ? page.images.slice(-MAX_VISIBLE_IMAGES)
      : appendUniqueImages(visibleImages.value, page.images);
    hasMoreImages.value = page.hasMore;
    totalImages.value = page.total || visibleImages.value.length;
    if (page.total > 0) {
      catsStore.setGalleryLocations(visibleImages.value, {
        total: page.total,
        limit: imagesPerPage,
        offset: (currentPage.value - 1) * imagesPerPage,
        has_more: page.hasMore,
        page: currentPage.value,
        total_pages: Math.ceil(page.total / imagesPerPage),
      });
    } else {
      catsStore.setGalleryLocations(visibleImages.value);
    }
    if (reset && callback) nextTick(() => callback());
  };

  const handleGalleryRequestError = (requestError: unknown): void => {
    if (isRequestAborted(requestError)) return;
    const message = (requestError as Error).message || 'Failed to load images from server';
    console.error(`[Gallery] Error fetching data:`, requestError);
    if (visibleImages.value.length === 0) error.value = message;
  };

  const finishGalleryRequest = (requestId: number, controller: AbortController): void => {
    if (requestId === latestRequestId) {
      loading.value = false;
      loadingMore.value = false;
    }
    if (activeAbortController === controller) activeAbortController = null;
  };

  async function fetchGalleryData(reset = false, callback?: () => void): Promise<void> {
    if (!reset && inFlightRequest && inFlightRequestKey) {
      return inFlightRequest;
    }

    if (reset) {
      activeAbortController?.abort();
      currentPage.value = 1;
    }

    const currentController = new AbortController();
    activeAbortController = currentController;

    const requestKey = `${reset ? 'reset' : 'append'}:${catsStore.gallerySearchQuery}:${currentPage.value}:${imagesPerPage}`;

    const runRequest = async (): Promise<void> => {
      const requestId = ++latestRequestId;
      if (reset) {
        if (visibleImages.value.length === 0) loading.value = true;
        hasMoreImages.value = true;
      } else {
        loadingMore.value = true;
      }
      error.value = '';

      try {
        const page = await fetchGalleryPage(
          catsStore.gallerySearchQuery,
          currentPage.value,
          imagesPerPage,
          currentController.signal
        );
        if (requestId !== latestRequestId) return;
        applyGalleryPage(page, reset, callback);
      } catch (requestError: unknown) {
        handleGalleryRequestError(requestError);
      } finally {
        finishGalleryRequest(requestId, currentController);
      }
    };

    inFlightRequestKey = requestKey;
    inFlightRequest = runRequest().finally(() => {
      if (inFlightRequestKey === requestKey) {
        inFlightRequestKey = null;
        inFlightRequest = null;
      }
    });

    return inFlightRequest;
  }

  function fetchImages(callback?: () => void): void {
    fetchGalleryData(true, callback);
  }

  function loadMoreImages(): void {
    if (loadingMore.value || !hasMoreImages.value) return;
    const now = Date.now();
    // Prevent request bursts when the observer re-initializes while trigger is still visible.
    if (now - lastLoadMoreRequestAt < 500) return;
    lastLoadMoreRequestAt = now;
    currentPage.value++;
    fetchGalleryData(false);
  }

  function preloadFirstImages(): void {
    if (preloadedLinks.length > 0) return;

    const criticalImages = visibleImages.value.slice(0, 2);

    criticalImages.forEach((image, index) => {
      if (image.image_url) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        let preloadUrl = image.image_url;
        if (image.image_url.includes('supabase.co')) {
          if (image.image_url.includes('width=')) {
            preloadUrl = image.image_url.replace(/width=\d+/, 'width=300');
          } else {
            preloadUrl = `${image.image_url}${image.image_url.includes('?') ? '&' : '?'}width=300`;
          }
        }
        link.href = preloadUrl;
        link.setAttribute('fetchpriority', index === 0 ? 'high' : 'low');
        document.head.appendChild(link);
        preloadedLinks.push(link);
      }
    });
  }

  function cleanupPreloads(): void {
    if (activeAbortController) {
      activeAbortController.abort();
      activeAbortController = null;
    }
    preloadedLinks.forEach((link) => {
      link.remove();
    });
    preloadedLinks.length = 0;
  }

  watch(
    () => visibleImages.value.length,
    (newCount, oldCount) => {
      if (newCount > 0 && oldCount === 0) {
        preloadFirstImages();
      }
    }
  );

  return {
    loading,
    loadingMore,
    error,
    visibleImages,
    hasMoreImages,
    totalImages,
    fetchImages,
    loadMoreImages,
    cleanupPreloads,
  };
}
