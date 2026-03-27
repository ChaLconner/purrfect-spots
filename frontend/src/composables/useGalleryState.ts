import { ref, watch, nextTick, type Ref } from 'vue';
import { GalleryService } from '@/services/galleryService';
import { useCatsStore } from '@/store';
import { GALLERY_CONFIG } from '@/utils/constants';
import type { CatLocation } from '@/types/api';

export function useGalleryState(isInitialized: Ref<boolean>): {
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

  const loading = ref(true);
  const loadingMore = ref(false);
  const error = ref('');
  const visibleImages = ref<CatLocation[]>([]);

  const currentPage = ref(1);
  const imagesPerPage = GALLERY_CONFIG.IMAGES_PER_PAGE;
  const hasMoreImages = ref(false);
  const totalImages = ref(0);

  const preloadedLinks: HTMLLinkElement[] = [];

  async function fetchGalleryData(reset = false, callback?: () => void): Promise<void> {
    if (!isInitialized.value) return;

    if (reset) {
      loading.value = true;
      currentPage.value = 1;
      visibleImages.value = [];
      hasMoreImages.value = true;
      totalImages.value = 0;
    } else {
      loadingMore.value = true;
    }

    error.value = '';

    try {
      const query = catsStore.gallerySearchQuery;
      let newImages: CatLocation[] = [];
      let hasNext = false;
      let total = 0;

      if (query) {
        const response = await GalleryService.search({
          query,
          page: currentPage.value,
          limit: imagesPerPage,
        });

        newImages = response.results || [];
        total = response.total || 0;
        hasNext = visibleImages.value.length + newImages.length < total;
      } else {
        const response = await GalleryService.getImages({
          page: currentPage.value,
          limit: imagesPerPage,
        });

        newImages = response.images || [];
        if (response.pagination) {
          hasNext = response.pagination.has_more;
          total = response.pagination.total;
        }
      }

      if (reset) {
        visibleImages.value = newImages;
      } else {
        visibleImages.value.push(...newImages);
      }

      hasMoreImages.value = hasNext;
      if (total > 0) {
        totalImages.value = total;
        catsStore.setLocations(visibleImages.value, {
          total,
          limit: imagesPerPage,
          offset: (currentPage.value - 1) * imagesPerPage,
          has_more: hasNext,
          page: currentPage.value,
          total_pages: Math.ceil(total / imagesPerPage),
        });
      } else {
        totalImages.value = visibleImages.value.length;
      }

      if (reset && callback) {
        nextTick(() => callback());
      }
    } catch (err: unknown) {
      const message = (err as Error).message || 'Failed to load images from server';
      console.error(`[Gallery] Error fetching data:`, err);
      error.value = message;
      if (reset) visibleImages.value = [];
    } finally {
      loading.value = false;
      loadingMore.value = false;
    }
  }

  function fetchImages(callback?: () => void): void {
    fetchGalleryData(true, callback);
  }

  function loadMoreImages(): void {
    if (loadingMore.value || !hasMoreImages.value) return;
    currentPage.value++;
    fetchGalleryData(false);
  }

  function preloadFirstImages(): void {
    if (preloadedLinks.length > 0) return;

    const imagesToPreload = visibleImages.value.slice(0, 6);

    imagesToPreload.forEach((image, index) => {
      if (image.image_url) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        let preloadUrl = image.image_url;
        if (image.image_url.includes('supabase.co')) {
          preloadUrl = image.image_url.includes('width=')
            ? image.image_url.replace(/width=\d+/, 'width=300')
            : `${image.image_url}${image.image_url.includes('?') ? '&' : '?'}width=300`;
        }
        link.href = preloadUrl;
        link.setAttribute('fetchpriority', index === 0 ? 'high' : 'low');
        document.head.appendChild(link);
        preloadedLinks.push(link);
      }
    });
  }

  function cleanupPreloads(): void {
    preloadedLinks.forEach((link) => {
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
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
