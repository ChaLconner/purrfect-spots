/**
 * Compatibility facade for the modular map and gallery stores.
 *
 * Existing views keep using useCatsStore while each domain owns its state in
 * mapStore.ts or galleryStore.ts. New code should import the narrower store.
 */
import { defineStore, storeToRefs } from 'pinia';
import type { CatLocation, PaginationMeta } from '../types/api';
import { useGalleryStore } from './galleryStore';
import { useMapStore } from './mapStore';

export type { CatLocation } from '../types/api';
export type { TagInfo } from './catStoreUtils';
export { extractTags, getCleanDescription, hasTag } from './catStoreUtils';

export const useCatsStore = defineStore('cats', () => {
  const mapStore = useMapStore();
  const galleryStore = useGalleryStore();
  const map = storeToRefs(mapStore);
  const gallery = storeToRefs(galleryStore);

  function setLocations(data: CatLocation[], pagination?: PaginationMeta): void {
    mapStore.setLocations(data);
    if (pagination) galleryStore.setPagination(pagination);
  }

  function appendLocations(data: CatLocation[], pagination?: PaginationMeta): void {
    mapStore.appendLocations(data);
    if (pagination) galleryStore.setPagination(pagination);
  }

  return {
    locations: map.locations,
    galleryLocations: gallery.galleryLocations,
    isLoading: gallery.isLoading,
    error: gallery.error,
    searchQuery: map.searchQuery,
    gallerySearchQuery: gallery.gallerySearchQuery,
    popularTags: map.popularTags,
    selectedTags: map.selectedTags,
    pagination: gallery.pagination,
    catCount: map.catCount,
    totalCount: gallery.totalCount,
    galleryCount: gallery.galleryCount,
    hasMore: gallery.hasMore,
    currentPage: gallery.currentPage,
    totalPages: gallery.totalPages,
    filteredLocations: map.filteredLocations,
    filteredCount: map.filteredCount,
    allTags: map.allTags,
    popularTagsComputed: map.popularTagsComputed,
    setLocations,
    appendLocations,
    setGalleryLocations: galleryStore.setGalleryLocations,
    clearGalleryLocations: galleryStore.clearGalleryLocations,
    setLoading: galleryStore.setLoading,
    setError: galleryStore.setError,
    setSearchQuery: mapStore.setSearchQuery,
    setGallerySearchQuery: galleryStore.setGallerySearchQuery,
    clearSearch: mapStore.clearSearch,
    clearGallerySearch: galleryStore.clearGallerySearch,
    setPopularTags: mapStore.setPopularTags,
    toggleTag: mapStore.toggleTag,
    clearFilters: mapStore.clearFilters,
    resetPagination: galleryStore.resetPagination,
    nextPage: galleryStore.nextPage,
    prevPage: galleryStore.prevPage,
    goToPage: galleryStore.goToPage,
  };
});

export type { TagInfo as CatsTagInfo } from './catStoreUtils';
