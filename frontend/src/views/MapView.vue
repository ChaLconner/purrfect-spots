<template>
  <div class="map-page">
    <!-- Map Container with 3D Frame -->
    <div class="map-frame">
      <div class="map-container">
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
            <GhibliLoader text="Loading map..." />
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
            <GhibliLoader text="Finding cute cats..." />
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
        <div id="map" class="map-element"></div>

        <!-- Custom Map Controls (Glassmorphism) -->

        <!-- Search Results Info (Floating Badge) -->
        <transition
          enter-active-class="transition-all duration-300 ease-out"
          leave-active-class="transition-all duration-200 ease-in"
          enter-from-class="opacity-0 -translate-y-4"
          leave-to-class="opacity-0 -translate-y-4"
        >
          <div
            v-if="!isLoading && !error && searchQuery"
            class="absolute top-6 left-1/2 transform -translate-x-1/2 z-10"
          >
            <div class="search-results-badge">
              <span class="badge-text">
                Found <strong>{{ displayedLocations.length }}</strong> cats for "<span
                  class="search-term"
                  >{{ searchQuery }}</span
                >"
              </span>
              <button class="clear-search-btn" aria-label="Clear search" @click="clearSearch">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>
        </transition>
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
import { GalleryService } from '../services/galleryService';
import { showError } from '../store/toast';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import ErrorState from '@/components/ui/ErrorState.vue';
import CatDetailModal from '@/components/map/CatDetailModal.vue';
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
      error.value = (err as Error).message;
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
    error.value = `Failed to initialize map: ${message}`;
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
  } catch (err: unknown) {
    // Error handling
    const msg = (err as Error).message || 'Failed to load locations';
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

const syncStateFromUrl = () => {
  const imageId = route.query.image as string;
  if (!imageId) {
    selectedCat.value = null;
    return;
  }

  const foundCat = displayedLocations.value.find((loc) => loc.id.toString() === imageId);
  if (foundCat) {
    selectedCat.value = foundCat;
    if (map.value) {
      map.value.panTo({ lat: foundCat.latitude, lng: foundCat.longitude });
      if (map.value.getZoom()! < 15) map.value.setZoom(15);
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
    title: 'Cat Map | Purrfect Spots',
    description: 'Explore cat sightings on an interactive map. Find cat-friendly spots near you.',
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

<style scoped>
/* Map Page Layout */
.map-page {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0 1.5rem 1rem 1.5rem;
  overflow: hidden;
}

/* 3D Map Frame */
.map-frame {
  position: relative;
  flex: 1;
  padding: 0.5rem;
  background: var(--color-btn-shade-e);
  border: 3px solid var(--color-btn-shade-a);
  border-radius: 1.25rem;
  box-shadow:
    0 0 0 3px var(--color-btn-shade-b),
    0 0.5em 0 0 var(--color-btn-shade-a);
}

/* Map Container */
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 0.75rem;
  background: var(--color-btn-shade-d);
}

/* Map Element */
.map-element {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 5.5rem - 2rem - 1rem - 10px);
  /* 100vh - navbar(5.5rem) - frame padding(2rem) - page padding(1rem) - extra(10px) */
  outline: none;
  border-radius: inherit;
}

/* Floating animation for welcome card */
@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-5px);
  }
}

@keyframes float-gentle {
  0%,
  100% {
    transform: translate(-50%, 0px);
  }
  50% {
    transform: translate(-50%, -4px);
  }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}

.animate-float-gentle {
  animation: float-gentle 4s ease-in-out infinite;
}

/* Delay utilities for sparkle animation */
.delay-100 {
  animation-delay: 0.1s;
}
.delay-200 {
  animation-delay: 0.2s;
}

/* 3D Search Results Badge */
.search-results-badge {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.625rem 0.625rem 1.25rem;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 2rem;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.3em 0 0 var(--color-btn-shade-a);
  animation: float-gentle 4s ease-in-out infinite;
}

.badge-text {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-btn-shade-a);
}

.badge-text strong {
  color: var(--color-btn-accent-a);
  font-weight: 700;
}

.search-term {
  font-style: italic;
  color: var(--color-btn-brown-b);
}

/* 3D Clear Search Button */
.clear-search-btn {
  position: relative;
  width: 1.75rem;
  height: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-btn-accent-e);
  border: 2px solid var(--color-btn-accent-a);
  border-radius: 50%;
  color: var(--color-btn-accent-a);
  cursor: pointer;
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.clear-search-btn::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-accent-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-accent-b),
    0 0.2em 0 0 var(--color-btn-accent-a);
  transform: translate3d(0, 0.2em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.clear-search-btn:hover {
  background: var(--color-btn-accent-d);
  transform: translate(0, 0.1em);
}

.clear-search-btn:active {
  transform: translate(0, 0.2em);
}

.clear-search-btn:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-accent-b),
    0 0.05em 0 0 var(--color-btn-accent-b);
}

.clear-search-btn svg {
  position: relative;
  z-index: 1;
}
</style>
