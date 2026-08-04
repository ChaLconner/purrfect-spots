import { defineStore } from 'pinia';
import { computed, onScopeDispose, ref, shallowRef, watch } from 'vue';
import type { CatLocation } from '../types/api';
import {
  extractTags,
  type TagInfo,
} from './catStoreUtils';

const MAX_MAP_LOCATIONS = 2000;
const LOCAL_STORAGE_DEBOUNCE_MS = 2000;
const CACHE_LIMIT = 100;

export const useMapStore = defineStore('map', () => {
  const locations = shallowRef<CatLocation[]>([]);
  const searchQuery = ref('');
  const popularTags = ref<TagInfo[]>([]);
  const selectedTags = ref<string[]>([]);

  if (typeof window !== 'undefined') {
    const restoreCache = (): void => {
      try {
        const saved = window.localStorage.getItem('cats_store_cache');
        if (!saved) return;
        const data = JSON.parse(saved);
        if (Array.isArray(data.locations) && locations.value.length === 0) locations.value = data.locations;
      } catch {
        // Cache is optional and must not block the map.
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
    locations,
    (newLocations) => {
      if (storageWriteTimer) clearTimeout(storageWriteTimer);
      storageWriteTimer = setTimeout(() => {
        try {
          if (typeof window !== 'undefined') {
            window.localStorage.setItem(
              'cats_store_cache',
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

  const catCount = computed(() => locations.value.length);
  const searchableLocations = computed(() =>
    locations.value.map((cat) => ({
      cat,
      locationName: cat.location_name?.toLowerCase() ?? '',
      description: cat.description?.toLowerCase() ?? '',
      tags: cat.tags?.map((tag) => tag.toLowerCase()) ?? [],
    }))
  );
  const filteredLocations = computed(() => {
    if (!searchQuery.value.trim()) return locations.value;

    const rawQuery = searchQuery.value.toLowerCase().trim();
    const normalizedQuery = rawQuery.replace(/^#/, '');
    const hashtagQuery = `#${normalizedQuery}`;
    return searchableLocations.value
      .filter(({ locationName, description, tags }) =>
        locationName.includes(normalizedQuery) ||
        description.includes(normalizedQuery) ||
        description.includes(hashtagQuery) ||
        tags.some((tag) => tag.includes(normalizedQuery))
      )
      .map(({ cat }) => cat);
  });
  const filteredCount = computed(() => filteredLocations.value.length);
  const tagStats = computed(() => {
    const counts = new Map<string, number>();
    locations.value.forEach((location) => {
      const tags = location.tags && location.tags.length > 0 ? location.tags : extractTags(location.description);
      tags.forEach((tag) => {
        const normalizedTag = tag.toLowerCase();
        counts.set(normalizedTag, (counts.get(normalizedTag) || 0) + 1);
      });
    });
    return counts;
  });
  const allTags = computed(() => Array.from(tagStats.value.keys()).sort((a, b) => a.localeCompare(b)));
  const popularTagsComputed = computed(() =>
    Array.from(tagStats.value.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([tag, count]) => ({ tag, count }))
  );

  function setLocations(data: CatLocation[]): void {
    locations.value = data.slice(-MAX_MAP_LOCATIONS);
  }

  function appendLocations(data: CatLocation[]): void {
    const incomingIds = new Set(data.map((item) => item.id));
    const existingById = new Map(locations.value.map((item) => [item.id, item]));
    const retained = locations.value.filter((item) => !incomingIds.has(item.id));
    const mergedIncoming = data.map((newItem) => {
      const existing = existingById.get(newItem.id);
      if (
        existing &&
        existing.latitude === newItem.latitude &&
        existing.longitude === newItem.longitude &&
        existing.image_url === newItem.image_url &&
        existing.description === newItem.description &&
        existing.location_name === newItem.location_name
      ) {
        return existing;
      }
      return existing ? { ...existing, ...newItem } : newItem;
    });
    locations.value = [...retained, ...mergedIncoming].slice(-MAX_MAP_LOCATIONS);
  }

  function setSearchQuery(query: string): void {
    searchQuery.value = query;
  }

  function clearSearch(): void {
    searchQuery.value = '';
    selectedTags.value = [];
  }

  function setPopularTags(tags: TagInfo[]): void {
    popularTags.value = tags;
  }

  function toggleTag(tag: string): void {
    const index = selectedTags.value.indexOf(tag);
    if (index === -1) selectedTags.value.push(tag);
    else selectedTags.value.splice(index, 1);
  }

  function clearFilters(): void {
    searchQuery.value = '';
    selectedTags.value = [];
  }

  onScopeDispose(() => {
    if (storageWriteTimer) clearTimeout(storageWriteTimer);
  });

  return {
    locations,
    searchQuery,
    popularTags,
    selectedTags,
    catCount,
    filteredLocations,
    filteredCount,
    allTags,
    popularTagsComputed,
    setLocations,
    appendLocations,
    setSearchQuery,
    clearSearch,
    setPopularTags,
    toggleTag,
    clearFilters,
  };
});
