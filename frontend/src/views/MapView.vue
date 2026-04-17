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

        <!-- Data Loading State (Subtle) -->
        <transition
          enter-active-class="transition-opacity duration-300"
          leave-active-class="transition-opacity duration-200"
          enter-from-class="opacity-0"
          leave-to-class="opacity-0"
        >
          <div
            v-if="isLoading && !isInitialLoading"
            class="absolute bottom-6 right-6 flex items-center gap-3 bg-white/90 backdrop-blur-md px-4 py-2 rounded-2xl shadow-lg z-20 border border-white/50 animate-bounce-subtle"
          >
            <GhibliLoader size="small" :text="$t('map.findingCats')" />
          </div>
        </transition>

        <!-- Error State -->
        <div
          v-if="error && !isLoading && !isInitialLoading"
          class="absolute inset-0 flex flex-col items-center justify-center bg-black/60 backdrop-blur-md z-20 p-6 rounded-xl"
        >
          <ErrorState :message="error" @retry="fetchLocationsInViewport" />
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

        <!-- Cat Counter Badge: Bottom Right Positioning -->
        <transition
          enter-active-class="transition-all duration-500 ease-out"
          leave-active-class="transition-all duration-300 ease-in"
          enter-from-class="opacity-0 translate-y-4 scale-95"
          leave-to-class="opacity-0 translate-y-4 scale-95"
        >
          <div
            v-if="!isInitialLoading && !error"
            class="absolute top-6 right-6 flex items-center gap-2.5 px-3 py-1.5 bg-white/80 backdrop-blur-md rounded-2xl border-2 border-[var(--color-btn-shade-a)] shadow-lg z-20 group transition-all duration-300 hover:shadow-xl hover:translate-y-[2px]"
          >
            <!-- Icon Container (Compact) -->
            <div
              class="w-8 h-8 flex items-center justify-center group-hover:scale-110 transition-transform duration-300"
            >
              <img :src="catIcon" alt="Cat count icon" class="w-6 h-6 object-contain" />
            </div>

            <!-- Labels (Refined Typography) -->
            <div class="flex flex-col justify-center leading-none text-left pr-1">
              <span
                class="font-accent font-bold text-[0.85rem] text-[var(--color-btn-shade-a)] tracking-tight uppercase"
              >
                {{ catsStore.searchQuery ? (catsStore.galleryCount || visibleCount) : visibleCount }} {{ $t('cats.cats') }}
              </span>
              <span
                class="font-accent text-[0.65rem] font-bold text-[var(--color-btn-shade-a)]/70 mt-0.5"
              >
                {{ $t('cats.spottedNearby') }}
              </span>
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
import type { LocationQueryRaw, LocationQueryValue } from 'vue-router';
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
import { openTrustedExternalUrl } from '../utils/security';
import { useCatsStore } from '../store';
import type { CatLocation } from '../store';

// Composables
import { useGeolocation } from '../composables/useGeolocation';
import { useMapMarkers } from '../composables/useMapMarkers';
import { useSeo } from '../composables/useSeo';

const catIcon = '/cat-icon.webp';
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

const getQueryString = (
  value: LocationQueryValue | LocationQueryValue[] | undefined
): string => {
  const firstValue = Array.isArray(value) ? value[0] : value;
  return firstValue ?? '';
};

// Search Query
const searchQuery = computed(() => catsStore.searchQuery);
const displayedLocations = computed(() => catsStore.filteredLocations);

// Viewport fetch logic
// Using ref for proper cleanup
const isViewportFetching = ref(false);
const latestImageRequestId = ref(0);
const viewportFetchTimer = ref<ReturnType<typeof setTimeout> | null>(null);

// Map bounds tracking for visible counter
const mapBounds = ref<google.maps.LatLngBounds | null>(null);

/**
 * Filter markers to only those visible in the current viewport
 * Used for the "Spotted Nearby" badge to ensure the number matches what the user sees
 */
const visibleCount = computed(() => {
  if (!map.value || !mapBounds.value) return displayedLocations.value.length;
  
  const currentBounds = mapBounds.value;
  return displayedLocations.value.filter((loc: CatLocation): boolean => {
    try {
      // Use Google Maps LatLngBounds.contains API for accurate geometric check
      return currentBounds.contains({ lat: loc.latitude, lng: loc.longitude });
    } catch {
      // Fallback to inclusion if geometric check fails
      return true;
    }
  }).length;
});

// ==========================================
// Handlers
// ==========================================

const searchByTag = (tag: string): void => {
  const query: LocationQueryRaw = { ...route.query, search: `#${tag}` };
  delete query.image;
  router.push({ query });
  catsStore.setSearchQuery(`#${tag}`);
};

const clearSearch = (): void => {
  catsStore.clearSearch();
  const query: LocationQueryRaw = { ...route.query };
  delete query.search;
  router.push({ query });
};

const selectCat = (cat: CatLocation): void => {
  const query: LocationQueryRaw = { ...route.query, image: cat.id };
  router.push({ query });
};

const closeModal = (): void => {
  const query: LocationQueryRaw = { ...route.query };
  delete query.image;
  router.push({ query });
};

// ==========================================
// Map Logic
// ==========================================

const initializeMap = async (): Promise<void> => {
  await nextTick();

  // Progressive loading: Start map initialization in background
  // Don't block the UI - show skeleton immediately

  if (!isGoogleMapsLoaded()) {
    try {
      const apiKey = getEnvVar('VITE_GOOGLE_MAPS_API_KEY');
      if (!apiKey) {
        throw new Error('Google Maps API key is missing.');
      }

      await loadGoogleMaps({
        apiKey,
        libraries: MAP_CONFIG.LIBRARIES,
        version: MAP_CONFIG.VERSION,
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
    if (!mapElement) {
      await nextTick();
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

    // Initialize bounds immediately
    mapBounds.value = map.value.getBounds() || null;

    // Listeners with requestAnimationFrame for smooth performance
    map.value.addListener('idle', (): void => {
      if (map.value) {
        mapBounds.value = map.value.getBounds() || null;
      }
      
      // Don't trigger fetch if we're already fetching or if fitting bounds is in progress
      if (!isViewportFetching.value && !isLoading.value) {
        requestAnimationFrame(() => {
          debouncedViewportFetch();
        });
      }
    });

    // Initial Render - use RAF for smooth transition
    requestAnimationFrame((): void => {
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

const fetchLocationsInViewport = async (): Promise<void> => {
  if (!map.value || isViewportFetching.value) return;

  const bounds = map.value.getBounds();
  const zoom = map.value.getZoom();

  if (!bounds || (zoom !== undefined && zoom < MAP_CONFIG.MIN_ZOOM_FOR_VIEWPORT_FETCH)) {
    return;
  }

  isViewportFetching.value = true;
  // Don't show full loading if we already have some data (better UX)
  if (displayedLocations.value.length === 0) {
    isLoading.value = true;
  }
  error.value = null;

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

    // Use store action to merge locations (handles duplicates and updates)
    catsStore.appendLocations(locations);

    // sync state from URL if needed
    syncStateFromUrl();
  } catch {
    const msg = t('map.errorLoadingLocations');
    error.value = msg;
    catsStore.setError(msg);
  } finally {
    isViewportFetching.value = false;
    isLoading.value = false;
  }
};

const debouncedViewportFetch = (): void => {
  if (viewportFetchTimer.value) clearTimeout(viewportFetchTimer.value);
  viewportFetchTimer.value = setTimeout(
    fetchLocationsInViewport,
    MAP_CONFIG.VIEWPORT_FETCH_DEBOUNCE_MS
  );
};

// ==========================================
// Watchers
// ==========================================

// 1. Update markers when data changes (ISOLATED from map movement)
watch(
  displayedLocations,
  (locations): void => {
    updateMarkers(locations, selectCat);
  },
  { deep: false, immediate: true }
);

// 2. ONLY Fit bounds when searching (Manual trigger via searchQuery change)
const hasFittedForCurrentSearch = ref(false);
const getDisplayedLocationCount = (): number => displayedLocations.value.length;
watch(searchQuery, (): void => {
  hasFittedForCurrentSearch.value = false;
});

// Fit bounds only when (search changed AND we have new data AND we haven't fitted yet)
watch(
  [getDisplayedLocationCount],
  ([count]: [number]): void => {
    if (
      searchQuery.value &&
      map.value &&
      count > 0 &&
      !hasFittedForCurrentSearch.value
    ) {
      const locations = displayedLocations.value;
      if (locations.length > 1) {
        const bounds = new google.maps.LatLngBounds();
        locations.forEach((loc: CatLocation): void => {
          bounds.extend({ lat: loc.latitude, lng: loc.longitude });
        });

        // Use a temporary flag to prevent the 'idle' listener from refetching immediately
        isViewportFetching.value = true;
        map.value.fitBounds(bounds, MAP_CONFIG.FIT_BOUNDS_PADDING);
        hasFittedForCurrentSearch.value = true;

        // Release the lock after animation roughly finishes
        setTimeout((): void => {
          isViewportFetching.value = false;
        }, 1000);
      } else if (locations.length === 1) {
        map.value.panTo({ lat: locations[0].latitude, lng: locations[0].longitude });
        map.value.setZoom(15);
        hasFittedForCurrentSearch.value = true;
      }
    }
  },
  { immediate: false }
);

// Watch user location
watch(userLocation, (pos, oldPos): void => {
  updateUserMarker(pos);

  // Auto-pan to user's location if newly detected and map is ready
  // Only if no search is active (don't disrupt user's current view if they are searching)
  if (pos && !oldPos && map.value && !searchQuery.value && !route.query.image) {
    map.value.panTo(pos);
    map.value.setZoom(15);
  }
});

// Watch Map Instance - Fix for race condition where data loads before map
watch(map, (newMap): void => {
  if (newMap && displayedLocations.value.length > 0) {
    updateMarkers(displayedLocations.value, selectCat);
  }
});

// Watch Search from URL - ensure store syncs even when query is removed
watch(
  () => route.query.search,
  (newSearch): void => {
    const query = getQueryString(newSearch);
    if (query !== catsStore.searchQuery) {
      catsStore.setSearchQuery(query);
    }
  },
  { immediate: true }
);

// Watch selected image from URL to sync state
watch(
  (): LocationQueryValue | LocationQueryValue[] | undefined => route.query.image,
  (): void => {
    syncStateFromUrl();
  }
);

const syncStateFromUrl = async (): Promise<void> => {
  const requestId = ++latestImageRequestId.value;
  const imageId = getQueryString(route.query.image);

  if (!imageId) {
    selectedCat.value = null;
    return;
  }

  // 1. Try to find in currently displayed locations (fastest) for immediate panning/preview
  let found = displayedLocations.value.find((loc: CatLocation): boolean => loc.id.toString() === imageId);

  // 2. If present, set it immediately (optimistic UI)
  if (found) {
    selectedCat.value = found;
  }

  // 3. Fetch canonical fresh details (for liked status, full description, etc.)
  try {
    const fullCat = await GalleryService.getPhotoById(imageId);

    // Guard against race conditions
    if (requestId !== latestImageRequestId.value) return;

    if (fullCat) {
      selectedCat.value = fullCat;
      found = fullCat;
      catsStore.appendLocations([fullCat]);
    }
  } catch (err) {
    if (requestId !== latestImageRequestId.value) return;
    console.warn(`Could not fetch details for cat ${imageId}:`, err);
    if (!found) {
      const q: LocationQueryRaw = { ...route.query };
      delete q.image;
      router.replace({ query: q });
      return;
    }
  }

  // 4. Pan to location if found
  if (found && map.value) {
    map.value.panTo({ lat: found.latitude, lng: found.longitude });
    const currentZoom = map.value.getZoom();
    if (currentZoom !== undefined && currentZoom < 15) {
      map.value.setZoom(15);
    }
  }
};

// ==========================================
// Control Handlers
// ==========================================

const openDirections = (cat: CatLocation): void => {
  let url = `${EXTERNAL_URLS.GOOGLE_MAPS_DIRECTIONS}`;
  if (userLocation.value) url += `&origin=${userLocation.value.lat},${userLocation.value.lng}`;
  url += `&destination=${cat.latitude},${cat.longitude}`;
  if (cat.location_name) url += `&destination_place_id=`;
  url += `&travelmode=walking`;
  openTrustedExternalUrl(url);
  closeModal();
};

// ==========================================
// Lifecycle
// ==========================================

onMounted((): void => {
  // Set SEO meta tags
  setMetaTags({
    title: `${t('map.metaTitle')} | Purrfect Spots`,
    description: t('map.metaDescription'),
    type: 'website',
  });

  // Start with a single low-cost location lookup so the first render stays responsive.
  void getCurrentPosition({
    enableHighAccuracy: false,
    timeout: 3000,
    maximumAge: 5 * 60 * 1000,
  });

  // Start map initialization immediately to improve LCP
  initializeMap();

  // Continuous tracking is useful, but it does not need to compete with the
  // initial map render and first viewport fetch.
  const startDeferredTracking = (): void => {
    void startWatchingPosition({
      enableHighAccuracy: false,
      timeout: 10000,
      maximumAge: 30000,
    });
  };

  if ('requestIdleCallback' in globalThis) {
    (
      globalThis as unknown as {
        requestIdleCallback: (cb: () => void, options?: { timeout: number }) => void;
      }
    ).requestIdleCallback(startDeferredTracking, { timeout: 2000 });
  } else {
    globalThis.setTimeout(startDeferredTracking, 1000);
  }
});

onUnmounted((): void => {
  stopWatchingPosition();
  if (viewportFetchTimer.value) {
    clearTimeout(viewportFetchTimer.value);
  }
  clearMarkers(); // Clean up all map objects
  map.value = null;
  resetMetaTags(); // Reset SEO meta tags
});
</script>
