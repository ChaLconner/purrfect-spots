import { reactive, computed } from 'vue';

// Re-export CatLocation from types/api.ts (single source of truth)
export type { CatLocation } from '../types/api';
import type { CatLocation } from '../types/api';

interface CatState {
  locations: CatLocation[];
  isLoading: boolean;
  error: string | null;
  searchQuery: string;
  popularTags: string[];
}

// Reactive state for cat locations - shared across components
export const catStore = reactive<CatState>({
  locations: [],
  isLoading: false,
  error: null,
  searchQuery: '',
  popularTags: [],
});

// ========== Tag Utility Functions ==========

/**
 * Extract hashtags from a description string
 * Supports both English and Thai characters
 */
export function extractTags(description: string | null | undefined): string[] {
  if (!description) return [];
  const matches = description.match(/#[a-z0-9ก-๙]+/gi);
  if (!matches) return [];
  // Remove # prefix and dedupe
  return [...new Set(matches.map(tag => tag.slice(1).toLowerCase()))];
}

/**
 * Get clean description without hashtags section
 * Removes the trailing hashtag section that was appended by backend
 */
export function getCleanDescription(description: string | null | undefined): string {
  if (!description) return '';
  // Remove the hashtag section (typically at the end after double newline)
  return description.replace(/\n\n#.+$/s, '').trim();
}

/**
 * Check if a location matches the given tag
 */
export function hasTag(location: CatLocation, tag: string): boolean {
  const normalizedTag = tag.toLowerCase().replace(/^#/, '');
  const tags = extractTags(location.description);
  return tags.includes(normalizedTag);
}

// ========== Computed values ==========

export const catCount = computed(() => catStore.locations.length);

export const filteredLocations = computed(() => {
  if (!catStore.searchQuery.trim()) {
    return catStore.locations;
  }
  
  const rawQuery = catStore.searchQuery.toLowerCase().trim();
  // Normalize query: remove # prefix for hashtag searches
  const normalizedQuery = rawQuery.replace(/^#/, '');
  // Also search with # prefix to find hashtags in description
  const hashtagQuery = `#${normalizedQuery}`;
  
  return catStore.locations.filter(cat => {
    const locationMatch = cat.location_name?.toLowerCase().includes(normalizedQuery);
    const descriptionMatch = cat.description?.toLowerCase().includes(normalizedQuery);
    const hashtagMatch = cat.description?.toLowerCase().includes(hashtagQuery);
    
    return locationMatch || descriptionMatch || hashtagMatch;
  });
});

/**
 * Get count of filtered locations
 */
export const filteredCount = computed(() => filteredLocations.value.length);

/**
 * Extract all unique tags from all locations
 */
export const allTags = computed(() => {
  const tagSet = new Set<string>();
  catStore.locations.forEach(location => {
    extractTags(location.description).forEach(tag => tagSet.add(tag));
  });
  return Array.from(tagSet).sort();
});

/**
 * Get popular tags (most frequently used)
 */
export const popularTagsComputed = computed(() => {
  const tagCounts = new Map<string, number>();
  
  catStore.locations.forEach(location => {
    extractTags(location.description).forEach(tag => {
      tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
    });
  });
  
  // Sort by count descending and take top 10
  return Array.from(tagCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([tag]) => tag);
});

// Actions
export function setLocations(locations: CatLocation[]) {
  catStore.locations = locations;
}

export function setLoading(loading: boolean) {
  catStore.isLoading = loading;
}

export function setError(error: string | null) {
  catStore.error = error;
}

export function setSearchQuery(query: string) {
  catStore.searchQuery = query;
}

export function clearSearch() {
  catStore.searchQuery = '';
}
