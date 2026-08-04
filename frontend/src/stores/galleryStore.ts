import { defineStore } from 'pinia';
import { computed, onScopeDispose, ref, shallowRef, watch } from 'vue';
import type { CatLocation, PaginationMeta } from '../types/api';

const DEFAULT_PAGINATION: PaginationMeta = {
  total: 0,
  limit: 20,
  offset: 0,
  has_more: false,
  page: 1,
  total_pages: 0,
};
const LOCAL_STORAGE_DEBOUNCE_MS = 2000;
const CACHE_LIMIT = 100;

export const useGalleryStore = defineStore('gallery', () => {
  const galleryLocations = shallowRef<CatLocation[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const gallerySearchQuery = ref('');
  const galleryCountValue = ref(0);
  const pagination = ref<PaginationMeta>({ ...DEFAULT_PAGINATION });

  if (typeof window !== 'undefined') {
    const restoreCache = (): void => {
      try {
        const saved = window.localStorage.getItem('gallery_store_cache');
        if (!saved) return;
        const data = JSON.parse(saved);
        if (Array.isArray(data.locations) && galleryLocations.value.length === 0) {
          galleryLocations.value = data.locations;
        }
      } catch {
        // Cache is optional and must not block the gallery.
      }
    };

    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(restoreCache, { timeout: 1000 });
    } else {
      setTimeout(restoreCache, 0);
    }
  }

  let storageWriteTimer: ReturnType<typeof setTimeout> | null = null;
  watch(
    galleryLocations,
    (newLocations) => {
      if (storageWriteTimer) clearTimeout(storageWriteTimer);
      storageWriteTimer = setTimeout(() => {
        try {
          if (typeof window !== 'undefined') {
            window.localStorage.setItem(
              'gallery_store_cache',
              JSON.stringify({ locations: newLocations.slice(0, CACHE_LIMIT) })
            );
          }
        } catch {
          // Quota errors only disable this optional cache write.
        }
      }, LOCAL_STORAGE_DEBOUNCE_MS);
    },
    { deep: false }
  );

  const galleryCount = computed(() => galleryCountValue.value);
  const totalCount = computed(() => pagination.value.total);
  const hasMore = computed(() => pagination.value.has_more);
  const currentPage = computed(() => pagination.value.page);
  const totalPages = computed(() => pagination.value.total_pages);

  function setPagination(data: PaginationMeta): void {
    pagination.value = data;
    galleryCountValue.value = data.total;
  }

  function setGalleryLocations(data: CatLocation[], paginationData?: PaginationMeta): void {
    galleryLocations.value = data;
    if (paginationData) setPagination(paginationData);
  }

  function clearGalleryLocations(): void {
    galleryLocations.value = [];
  }

  function setLoading(loading: boolean): void {
    isLoading.value = loading;
  }

  function setError(value: string | null): void {
    error.value = value;
  }

  function setGallerySearchQuery(query: string): void {
    gallerySearchQuery.value = query;
  }

  function clearGallerySearch(): void {
    gallerySearchQuery.value = '';
  }

  function resetPagination(): void {
    pagination.value = { ...pagination.value, offset: 0, page: 1, total_pages: 0 };
  }

  function nextPage(): void {
    if (pagination.value.has_more) {
      pagination.value.page++;
      pagination.value.offset = (pagination.value.page - 1) * pagination.value.limit;
    }
  }

  function prevPage(): void {
    if (pagination.value.page > 1) {
      pagination.value.page--;
      pagination.value.offset = (pagination.value.page - 1) * pagination.value.limit;
    }
  }

  function goToPage(page: number): void {
    if (page >= 1 && page <= pagination.value.total_pages) {
      pagination.value.page = page;
      pagination.value.offset = (page - 1) * pagination.value.limit;
    }
  }

  onScopeDispose(() => {
    if (storageWriteTimer) clearTimeout(storageWriteTimer);
  });

  return {
    galleryLocations,
    isLoading,
    error,
    gallerySearchQuery,
    galleryCount,
    pagination,
    totalCount,
    hasMore,
    currentPage,
    totalPages,
    setPagination,
    setGalleryLocations,
    clearGalleryLocations,
    setLoading,
    setError,
    setGallerySearchQuery,
    clearGallerySearch,
    resetPagination,
    nextPage,
    prevPage,
    goToPage,
  };
});
