<template>
  <div class="relative flex flex-col h-full pt-6 px-6 pb-4 overflow-hidden">
    <!-- Map Container with 3D Frame -->
    <div
      class="relative flex-1 p-2 bg-[var(--color-btn-shade-e)] border-[3px] border-[var(--color-btn-shade-a)] rounded-[1.25rem] shadow-[0_0_0_3px_var(--color-btn-shade-b),0_0.5em_0_0_var(--color-btn-shade-a)]"
    >
      <div class="relative w-full h-full overflow-hidden rounded-xl bg-[var(--color-btn-shade-d)]">
        <!-- Initial Loading State (Progressive) -->
        <transition
          enter-active-class="transition-opacity duration-300"
          leave-active-class="transition-opacity duration-200"
          enter-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="isInitialLoading"
            class="absolute inset-0 flex flex-col items-center justify-center bg-[#e8f0e6] z-10 rounded-xl"
          >
            <GhibliLoader :text="$t('map.loadingMap')" />
          </div>
        </transition>

        <!-- Data Loading State -->
        <transition
          enter-active-class="transition-opacity duration-300"
          leave-active-class="transition-opacity duration-200"
          enter-from-class="opacity-0"
          leave-to-class="opacity-0"
        >
          <div
            v-if="isLoading && !isInitialLoading"
            class="absolute inset-0 flex flex-col items-center justify-center bg-white/90 backdrop-blur-sm z-20 rounded-xl"
          >
            <GhibliLoader :text="$t('map.findingCats')" />
          </div>
        </transition>

        <!-- Error State -->
        <div
          v-if="error && !isLoading && !isInitialLoading"
          class="absolute inset-0 flex flex-col items-center justify-center bg-black/60 backdrop-blur-md z-20 p-6 rounded-xl"
        >
          <ErrorState :message="error" @retry="loadCatLocations" />
        </div>

        <!-- Google Map -->
        <div id="map" class="w-full h-full outline-none rounded-[inherit]"></div>

        <!-- Custom Map Controls (Glassmorphism) -->

        <MapSearchBadge
          :show="!isLoading && !error && !!searchQuery"
          :count="displayedLocations.length"
          :query="searchQuery || ''"
          @clear="clearSearch"
        />

        <!-- Onboarding Banner for new users -->
        <OnboardingBanner />
      </div>
    </div>

    <!-- Cat Details Modal -->
    <CatDetailModal
      :cat="selectedCat"
      @close="closeModal"
      @tag-click="searchByTag"
      @get-directions="openDirections"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, nextTick, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { GalleryService } from '../services/galleryService';
import { showError } from '../store/toast';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import ErrorState from '@/components/ui/ErrorState.vue';
import CatDetailModal from '@/components/map/CatDetailModal.vue';
import MapSearchBadge from '@/components/map/MapSearchBadge.vue';
import OnboardingBanner from '@/components/map/OnboardingBanner.vue';

import { loadGoogleMaps, isGoogleMapsLoaded } from '../utils/googleMapsLoader';
import { getEnvVar } from '../utils/env';
import { FALLBACK_LOCATION, MAP_CONFIG, EXTERNAL_URLS } from '../utils/constants';
import { useCatsStore } from '../store';
import type { CatLocation } from '../types/api';

// Composables
import { useGeolocation } from '../composables/useGeolocation';
import { useMapMarkers } from '../composables/useMapMarkers';
import { useSeo } from '../composables/useSeo';

const route = useRoute();
const router = useRouter();
const catsStore = useCatsStore();
const { t } = useI18n();

// State
const isLoading = ref(false);
const isInitialLoading = ref(true); // Progressive loading state
const error = ref<string | null>(null);
const selectedCat = ref<CatLocation | null>(null);

// Google Maps Refs
const map = ref<google.maps.Map | null>(null);

// Composables Setup
const { userLocation, getCurrentPosition, startWatchingPosition, stopWatchingPosition } =
  useGeolocation();

const { updateMarkers, updateUserMarker, clearMarkers } = useMapMarkers(map);

// SEO Setup
const { setMetaTags, resetMetaTags } = useSeo();

// Search Query
const searchQuery = computed(() => catsStore.searchQuery);
const displayedLocations = computed(() => catsStore.filteredLocations);

// Viewport fetch logic
// Using ref for proper cleanup
const viewportFetchTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const isViewportFetching = ref(false);

// ==========================================
// Handlers
// ==========================================

const searchByTag = (tag: string) => {
  catsStore.setSearchQuery(`#${tag}`);
  closeModal();
};

const clearSearch = () => {
  catsStore.clearSearch();
};

const selectCat = (cat: CatLocation) => {
  router.push({ query: { ...route.query, image: cat.id } });
};

const closeModal = () => {
  const query = { ...route.query };
  delete query.image;
  router.push({ query });
};

// ==========================================
// Map Logic
// ==========================================

const initializeMap = async () => {
  await nextTick();

  // Progressive loading: Start map initialization in background
  // Don't block the UI - show skeleton immediately

  if (!isGoogleMapsLoaded()) {
    try {
      const apiKey = getEnvVar('VITE_GOOGLE_MAPS_API_KEY');
      if (!apiKey) {
        throw new Error('Google Maps API key is missing.');
      }

      // Load Google Maps without blocking
      await loadGoogleMaps({
        apiKey,
        libraries: 'places,marker',
        version: 'weekly',
      });
    } catch (err: unknown) {
      error.value = t('map.errorInitializing', { message: (err as Error).message });
      showError(error.value);
      isInitialLoading.value = false;
      return;
    }
  }

  try {
    let mapElement = document.getElementById('map');

    // Ensure map container exists
    if (!mapElement) {
      mapElement = document.getElementById('map');
    }

    if (!mapElement) {
      throw new Error('Map container not found');
    }

    // Defensive sizing
    if (mapElement.offsetWidth === 0 || mapElement.offsetHeight === 0) {
      mapElement.style.height = '500px';
      mapElement.style.width = '100%';
    }

    const defaultCenter = userLocation.value || FALLBACK_LOCATION;

    // Create map
    // Note: When using mapId, styles must be configured in Google Cloud Console
    // The 'styles' property is ignored when mapId is present
    map.value = new google.maps.Map(mapElement, {
      zoom: MAP_CONFIG.DEFAULT_ZOOM,
      center: defaultCenter,
      mapId: '2e9b14b966a476a5ec49973f',
      disableDefaultUI: true,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      zoomControl: false,
      // styles: ghibliMapStyle, // Disabled: styles are controlled via Cloud Console when mapId is set
    });

    // Listeners with requestAnimationFrame for smooth performance
    map.value.addListener('idle', () => {
      requestAnimationFrame(() => {
        debouncedViewportFetch();
      });
    });

    // Initial Render - use RAF for smooth transition
    requestAnimationFrame(() => {
      if (userLocation.value) {
        updateUserMarker(userLocation.value);
      }

      updateMarkers(displayedLocations.value, selectCat);

      // Hide initial loading state
      isInitialLoading.value = false;
    });
  } catch (err: unknown) {
    const message = (err as Error).message;
    error.value = t('map.errorInitializing', { message });
    isInitialLoading.value = false;
  }
};

// ==========================================
// Data Fetching
// ==========================================

const loadCatLocations = async () => {
  isLoading.value = true;
  catsStore.setLoading(true);
  error.value = null;

  try {
    const locations = await GalleryService.getLocations();

    catsStore.setLocations(locations);

    // sync state from URL if needed
    syncStateFromUrl();
  } catch {
    // Error handling
    const msg = t('map.errorLoadingLocations');
    error.value = msg;
    catsStore.setError(msg);
  } finally {
    isLoading.value = false;
    catsStore.setLoading(false);
  }
};

const fetchLocationsInViewport = async () => {
  if (!map.value || isViewportFetching.value) return;

  const bounds = map.value.getBounds();
  const zoom = map.value.getZoom();

  if (!bounds || (zoom !== undefined && zoom < MAP_CONFIG.MIN_ZOOM_FOR_VIEWPORT_FETCH)) {
    return;
  }

  isViewportFetching.value = true;

  try {
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();

    const locations = await GalleryService.getViewportLocations({
      north: ne.lat(),
      south: sw.lat(),
      east: ne.lng(),
      west: sw.lng(),
      limit: MAP_CONFIG.MAX_MARKERS_PER_VIEWPORT,
    });

    // Merge only new locations
    const existingIds = new Set(catsStore.locations.map((loc) => loc.id));
    const newLocations = locations.filter((loc) => !existingIds.has(loc.id));

    if (newLocations.length > 0) {
      // Create new array reference for reactivity
      catsStore.setLocations([...catsStore.locations, ...newLocations]);
    }
  } catch (err) {
    console.warn('Viewport fetch failed:', err);
  } finally {
    isViewportFetching.value = false;
  }
};

const debouncedViewportFetch = () => {
  if (viewportFetchTimer.value) clearTimeout(viewportFetchTimer.value);
  viewportFetchTimer.value = setTimeout(
    fetchLocationsInViewport,
    MAP_CONFIG.VIEWPORT_FETCH_DEBOUNCE_MS
  );
};

// ==========================================
// Watchers
// ==========================================

// Watch displayed locations and update markers efficiently
watch(
  displayedLocations,
  (locations) => {
    updateMarkers(locations, selectCat);

    // Fit bounds logic for search
    if (searchQuery.value && map.value && locations.length > 0) {
      if (locations.length > 1) {
        const bounds = new google.maps.LatLngBounds();
        locations.forEach((loc) => bounds.extend({ lat: loc.latitude, lng: loc.longitude }));
        map.value.fitBounds(bounds, MAP_CONFIG.FIT_BOUNDS_PADDING);
      } else {
        map.value.panTo({ lat: locations[0].latitude, lng: locations[0].longitude });
        map.value.setZoom(15);
      }
    }
  },
  { deep: false, immediate: true }
); // Shallow watch is fine since we replace the array

// Watch user location
watch(userLocation, (pos, oldPos) => {
  updateUserMarker(pos);

  // Auto-pan to user's location if newly detected and map is ready
  // Only if no search is active (don't disrupt user's current view if they are searching)
  if (pos && !oldPos && map.value && !searchQuery.value && !route.query.image) {
    map.value.panTo(pos);
    map.value.setZoom(15);
  }
});

// Watch Map Instance - Fix for race condition where data loads before map
watch(map, (newMap) => {
  if (newMap && displayedLocations.value.length > 0) {
    updateMarkers(displayedLocations.value, selectCat);
  }
});

// Watch Search from URL
watch(
  () => route.query.search,
  (newSearch) => {
    if (newSearch) catsStore.setSearchQuery(newSearch as string);
  },
  { immediate: true }
);

// Watch selected image from URL to sync state
watch(
  () => route.query.image,
  () => {
    syncStateFromUrl();
  }
);

const syncStateFromUrl = async () => {
  const imageId = route.query.image as string;
  if (!imageId) {
    selectedCat.value = null;
    return;
  }

  // 1. Try to find in currently displayed locations (fastest) for immediate panning/preview
  let found = displayedLocations.value.find((loc) => loc.id.toString() === imageId);

  // 2. If present, set it immediately (optimistic UI)
  if (found) {
    selectedCat.value = found;
  }

  // 3. Fetch canonical fresh details (for liked status, full description, etc.)
  // This is crucial because map markers are lightweight and cached.
  try {
    const fullCat = await GalleryService.getPhotoById(imageId);

    // Update selectedCat with full data
    if (fullCat) {
      selectedCat.value = fullCat;
      found = fullCat; // Use full details for panning/validation
    }
  } catch (err) {
    console.warn(`Could not fetch details for cat ${imageId}:`, err);
    // If we failed to fetch AND confirm existence locally, clear selection
    if (!found) {
      const q = { ...route.query };
      delete q.image;
      router.replace({ query: q });
      return;
    }
  }

  // 4. Pan to location if found
  if (found && map.value) {
    map.value.panTo({ lat: found.latitude, lng: found.longitude });
    // Only zoom in if we're zoomed out too far
    const currentZoom = map.value.getZoom();
    if (currentZoom !== undefined && currentZoom < 15) {
      map.value.setZoom(15);
    }
  }
};

// ==========================================
// Control Handlers
// ==========================================

const openDirections = (cat: CatLocation) => {
  let url = `${EXTERNAL_URLS.GOOGLE_MAPS_DIRECTIONS}`;
  if (userLocation.value) url += `&origin=${userLocation.value.lat},${userLocation.value.lng}`;
  url += `&destination=${cat.latitude},${cat.longitude}`;
  if (cat.location_name) url += `&destination_place_id=`;
  url += `&travelmode=walking`;
  window.open(url, '_blank');
  closeModal();
};

// ==========================================
// Lifecycle
// ==========================================

onMounted(() => {
  // Set SEO meta tags
  setMetaTags({
    title: `${t('map.metaTitle')} | Purrfect Spots`,
    description: t('map.metaDescription'),
    type: 'website',
  });

  // Parallel fetch and initialization
  getCurrentPosition().then(() => startWatchingPosition());

  // Start map initialization immediately to improve LCP
  initializeMap();

  // Load data concurrently
  loadCatLocations();
});

onUnmounted(() => {
  stopWatchingPosition();
  if (viewportFetchTimer.value) {
    clearTimeout(viewportFetchTimer.value);
  }
  clearMarkers(); // Clean up all map objects
  map.value = null;
  resetMetaTags(); // Reset SEO meta tags
});
</script>
