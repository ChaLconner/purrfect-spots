/**
 * Pinia Cats Store
 *
 * State management for cat locations and gallery data.
 * Supports search, filtering, pagination, and tag-based queries.
 *
 * Performance optimizations included:
 * 1. Debounced localStorage writes (2s) to avoid blocking main thread
 * 2. Shallow watch for better performance
 * 3. Memoized filtering
 */
import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';

// Re-export CatLocation from types/api.ts (single source of truth)
export type { CatLocation } from '../types/api';
import type { CatLocation } from '../types/api';

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  page: number;
  total_pages: number;
}

export interface TagInfo {
  tag: string;
  count: number;
}

// ========== Store Definition ==========
export const useCatsStore = defineStore('cats', () => {
  // ========== State ==========
  const locations = ref<CatLocation[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Client-side search for Map View (filters loaded locations)
  const searchQuery = ref('');

  // Server-side search for Gallery View (API based)
  const gallerySearchQuery = ref('');
  const popularTags = ref<TagInfo[]>([]);
  const selectedTags = ref<string[]>([]);

  // Pagination state
  const pagination = ref<PaginationMeta>({
    total: 0,
    limit: 20,
    offset: 0,
    has_more: false,
    page: 1,
    total_pages: 0,
  });

  // ========== Persistence ==========
  try {
    const saved = localStorage.getItem('cats_store_cache');
    if (saved) {
      const data = JSON.parse(saved);
      if (Array.isArray(data.locations)) {
        locations.value = data.locations;
      }
    }
  } catch {
    // Ignore restoration errors
  }

  // OPTIMIZATION: Debounced localStorage write to avoid blocking main thread
  let localStorageWriteTimer: ReturnType<typeof setTimeout> | null = null;
  const LOCAL_STORAGE_DEBOUNCE_MS = 2000; // 2 seconds debounce

  watch(
    locations,
    (newLocations) => {
      // Clear previous timer
      if (localStorageWriteTimer) {
        clearTimeout(localStorageWriteTimer);
      }

      // Debounce the write operation
      localStorageWriteTimer = setTimeout(() => {
        try {
          // Limit cache size to avoid quota exceeded
          const cacheData = { locations: newLocations.slice(0, 100) };
          localStorage.setItem('cats_store_cache', JSON.stringify(cacheData));
        } catch {
          // Ignore quota errors
        }
      }, LOCAL_STORAGE_DEBOUNCE_MS);
    },
    { deep: false } // OPTIMIZATION: Shallow watch - only trigger when array reference changes
  );

  // ========== Getters ==========

  const catCount = computed(() => locations.value.length);

  const totalCount = computed(() => pagination.value.total);

  const hasMore = computed(() => pagination.value.has_more);

  const currentPage = computed(() => pagination.value.page);

  const totalPages = computed(() => pagination.value.total_pages);

  /**
   * Filter locations by search query (client-side)
   * Usage: Primary for Map View filtering
   * OPTIMIZATION: Memoized for better performance
   */
  const filteredLocations = computed(() => {
    if (!searchQuery.value.trim()) {
      return locations.value;
    }

    const rawQuery = searchQuery.value.toLowerCase().trim();
    const normalizedQuery = rawQuery.replace(/^#/, '');
    const hashtagQuery = `#${normalizedQuery}`;

    return locations.value.filter((cat) => {
      const locationMatch = cat.location_name?.toLowerCase().includes(normalizedQuery);
      const descriptionMatch = cat.description?.toLowerCase().includes(normalizedQuery);
      const hashtagMatch = cat.description?.toLowerCase().includes(hashtagQuery);
      const tagMatch = cat.tags?.some((tag) => tag.toLowerCase().includes(normalizedQuery));

      return locationMatch || descriptionMatch || hashtagMatch || tagMatch;
    });
  });

  const filteredCount = computed(() => filteredLocations.value.length);

  /**
   * Get all unique tags from loaded locations
   */
  const allTags = computed(() => {
    const tagSet = new Set<string>();
    locations.value.forEach((location) => {
      extractTags(location.description).forEach((tag) => tagSet.add(tag));
      location.tags?.forEach((tag) => tagSet.add(tag.toLowerCase()));
    });
    return Array.from(tagSet).sort((a, b) => a.localeCompare(b));
  });

  /**
   * Get popular tags from loaded locations (computed locally)
   */
  const popularTagsComputed = computed(() => {
    const tagCounts = new Map<string, number>();

    locations.value.forEach((location) => {
      const tags = location.tags || extractTags(location.description);
      tags.forEach((tag) => {
        const normalizedTag = tag.toLowerCase();
        tagCounts.set(normalizedTag, (tagCounts.get(normalizedTag) || 0) + 1);
      });
    });

    return Array.from(tagCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([tag, count]) => ({ tag, count }));
  });

  // ========== Actions ==========

  /**
   * Set locations data with pagination info
   */
  function setLocations(data: CatLocation[], paginationData?: PaginationMeta) {
    locations.value = data;
    if (paginationData) {
      pagination.value = paginationData;
    }
  }

  /**
   * Append more locations (for infinite scroll)
   */
  function appendLocations(data: CatLocation[], paginationData?: PaginationMeta) {
    locations.value = [...locations.value, ...data];
    if (paginationData) {
      pagination.value = paginationData;
    }
  }

  /**
   * Set loading state
   */
  function setLoading(loading: boolean) {
    isLoading.value = loading;
  }

  /**
   * Set error state
   */
  function setError(err: string | null) {
    error.value = err;
  }

  /**
   * Set search query (Global/Map)
   */
  function setSearchQuery(query: string) {
    searchQuery.value = query;
  }

  /**
   * Set gallery search query
   */
  function setGallerySearchQuery(query: string) {
    gallerySearchQuery.value = query;
  }

  /**
   * Clear search query
   */
  function clearSearch() {
    searchQuery.value = '';
    selectedTags.value = [];
  }

  /**
   * Clear gallery search
   */
  function clearGallerySearch() {
    gallerySearchQuery.value = '';
  }

  /**
   * Set popular tags from API
   */
  function setPopularTags(tags: TagInfo[]) {
    popularTags.value = tags;
  }

  /**
   * Toggle tag selection for filtering
   */
  function toggleTag(tag: string) {
    const index = selectedTags.value.indexOf(tag);
    if (index === -1) {
      selectedTags.value.push(tag);
    } else {
      selectedTags.value.splice(index, 1);
    }
  }

  /**
   * Clear all filters
   */
  function clearFilters() {
    searchQuery.value = '';
    selectedTags.value = [];
  }

  /**
   * Reset pagination to first page
   */
  function resetPagination() {
    pagination.value = {
      ...pagination.value,
      offset: 0,
      page: 1,
      total_pages: 0,
    };
  }

  /**
   * Go to next page
   */
  function nextPage() {
    if (pagination.value.has_more) {
      pagination.value.page++;
      pagination.value.offset = (pagination.value.page - 1) * pagination.value.limit;
    }
  }

  /**
   * Go to previous page
   */
  function prevPage() {
    if (pagination.value.page > 1) {
      pagination.value.page--;
      pagination.value.offset = (pagination.value.page - 1) * pagination.value.limit;
    }
  }

  /**
   * Go to specific page
   */
  function goToPage(page: number) {
    if (page >= 1 && page <= pagination.value.total_pages) {
      pagination.value.page = page;
      pagination.value.offset = (page - 1) * pagination.value.limit;
    }
  }

  return {
    // State
    locations,
    isLoading,
    error,
    searchQuery,
    gallerySearchQuery,
    popularTags,

    selectedTags,
    pagination,

    // Getters
    catCount,
    totalCount,
    hasMore,
    currentPage,
    totalPages,
    filteredLocations,
    filteredCount,
    allTags,
    popularTagsComputed,

    // Actions
    setLocations,
    appendLocations,
    setLoading,
    setError,
    setSearchQuery,
    setGallerySearchQuery,
    clearSearch,
    clearGallerySearch,
    setPopularTags,
    toggleTag,
    clearFilters,
    resetPagination,
    nextPage,
    prevPage,
    goToPage,
  };
});

// ========== Utility Functions ==========

/**
 * Extract hashtags from a description string
 */
export function extractTags(description: string | null | undefined): string[] {
  if (!description) return [];
  const matches = description.match(/#[a-z0-9ก-๙]+/gi);
  if (!matches) return [];
  return [...new Set(matches.map((tag) => tag.slice(1).toLowerCase()))];
}

/**
 * Get clean description without hashtags section
 */
export function getCleanDescription(description: string | null | undefined): string {
  if (!description) return '';
  return description.replace(/\n\n#.+$/s, '').trim();
}

/**
 * Check if a location matches the given tag
 */
export function hasTag(location: CatLocation, tag: string): boolean {
  const normalizedTag = tag.toLowerCase().replace(/^#/, '');
  const tags =
    location.tags && location.tags.length > 0 ? location.tags : extractTags(location.description);
  return tags.some((t) => t.toLowerCase() === normalizedTag);
}
