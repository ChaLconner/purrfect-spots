<template>
  <div class="relative h-full flex flex-col bg-[#EAF6F3]">
    <!-- Map Container - Full width, no padding -->
    <div class="relative flex-1 overflow-hidden rounded-card shadow-card group">
      <div
        v-if="isLoading"
        class="absolute inset-0 flex flex-col items-center justify-center bg-white/90 backdrop-blur-sm z-20"
      >
        <GhibliLoader text="Finding cute cats..." />
      </div>

      <!-- Error State -->
      <div
        v-if="error && !isLoading"
        class="absolute inset-0 flex flex-col items-center justify-center bg-black/60 backdrop-blur-md z-20 p-6"
      >
        <ErrorState :message="error" @retry="loadCatLocations" />
      </div>

      <!-- Google Map -->
      <div id="map" class="w-full h-full min-h-[500px] outline-none"></div>

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
          <div
            class="bg-white/90 backdrop-blur-md rounded-full shadow-lg shadow-sage/10 border border-white/60 pl-5 pr-2 py-2 flex items-center gap-3 animate-float-gentle"
          >
            <span class="text-sm text-brown-dark font-medium">
              Found <strong class="text-terracotta">{{ displayedLocations.length }}</strong> cats
              for "<span class="italic text-brown">{{ searchQuery }}</span>"
            </span>
            <button
              class="w-7 h-7 rounded-full bg-sage-light/20 hover:bg-terracotta hover:text-white flex items-center justify-center text-xs text-sage-dark transition-all duration-300"
              @click="clearSearch"
            >
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
import { ghibliMapStyle } from '../theme/mapStyles';
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
  // Ensure we don't have artificial delays that hurt LCP

  if (!isGoogleMapsLoaded()) {
    try {
      const apiKey = getEnvVar('VITE_GOOGLE_MAPS_API_KEY');
      if (!apiKey) {
        throw new Error('Google Maps API key is missing.');
      }

      await loadGoogleMaps({
        apiKey,
        libraries: 'places',
        version: 'weekly',
      });
    } catch (err: unknown) {
      error.value = (err as Error).message;
      showError(error.value);
      return;
    }
  }

  try {
    let mapElement = document.getElementById('map');

    // Ensure map container exists
    if (!mapElement) {
      // Just one check, if it's not there, something is wrong with the template
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
    map.value = new google.maps.Map(mapElement, {
      zoom: MAP_CONFIG.DEFAULT_ZOOM,
      center: defaultCenter,
      disableDefaultUI: true,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      zoomControl: false,
      styles: ghibliMapStyle,
    });

    // Listeners
    map.value.addListener('idle', () => {
      debouncedViewportFetch();
    });

    // Initial Render
    if (userLocation.value) {
      updateUserMarker(userLocation.value);
    }

    updateMarkers(displayedLocations.value, selectCat);
  } catch (err: unknown) {
    const message = (err as Error).message;
    error.value = `Failed to initialize map: ${message}`;
    // showError(error.value); // Removed: ErrorState component handles this
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
  { deep: false }
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
</style>
