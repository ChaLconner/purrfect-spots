<template>
  <div class="mx-auto px-4 max-w-6xl h-full flex flex-col">
    <!-- Header -->
    <div
      class="bg-gradient-to-r from-cyan-700 to-blue-600 text-white px-3 py-2 flex-col md:flex-row md:items-center md:justify-between gap-2 w-full h-min-content rounded-2xl hidden md:flex"
    >
      <div class="flex items-center gap-2">
        <span class="text-2xl drop-shadow-lg animate-bounce">🐾</span>
        <div>
          <h2 class="text-xl font-extrabold tracking-tight">Purrfect Spots</h2>
          <p class="text-cyan-100 text-xs mt-0">
            Find and share adorable cat locations near you!
          </p>
        </div>
      </div>
    </div>
    
    <div
      class="relative bg-gradient-to-br from-cyan-100 via-blue-50 to-white rounded-2xl shadow-2xl border border-blue-200 overflow-hidden flex-1 flex flex-col"
    >
      <!-- Loading -->
      <div
        v-if="isLoading"
        class="flex flex-col items-center justify-center flex-1 h-min-content p-6"
      >
        <div class="relative mb-6">
          <div
            class="animate-spin rounded-full h-20 w-20 border-t-4 border-cyan-400 border-opacity-60"
          ></div>
          <span class="absolute inset-0 flex items-center justify-center text-4xl"
            >🐱</span
          >
        </div>
        <h3 class="text-xl font-bold text-cyan-700 mb-1">
          Loading cat locations...
        </h3>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="bg-red-100/80 border border-red-300 rounded-xl mx-8 my-4 p-6 shadow flex flex-col items-center flex-1 content-center"
      >
        <div class="flex items-center gap-3 mb-2">
          <span class="text-3xl">😿</span>
          <h3 class="text-red-800 font-bold text-lg">
            Oops! Something went wrong
          </h3>
        </div>
        <p class="text-red-700 mb-4 text-center">{{ error }}</p>
        <button
          @click="loadCatLocations"
          class="px-8 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white rounded-lg font-semibold shadow transition"
        >
          Try Again
        </button>
      </div>

      <!-- Map View -->
      <div v-if="!isLoading && !error" class="flex-1 relative">
        <div id="map" class="w-full h-full min-h-[550px] md:min-h-[500px]"></div>
      </div>
    </div>

    <!-- Cat Details Modal -->
    <transition
      enter-active-class="transition-opacity duration-300 ease"
      leave-active-class="transition-opacity duration-300 ease"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="selectedCat"
        class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
        @click="closeModal"
      >
        <div
          class="bg-white rounded-3xl max-w-lg w-full overflow-hidden shadow-2xl relative animate-[fadeIn_0.3s_ease-in-out]"
          @click.stop
        >
          <div class="relative">
            <img
              :src="selectedCat.image_url"
              :alt="selectedCat.location_name"
              class="w-full h-56 object-cover object-center rounded-t-3xl"
            />
            <button
              @click="closeModal"
              class="absolute top-2 right-2 rounded-full px-3 py-2 transition"
            >
                <span class="text-white text-2xl font-bold cursor-pointer"
                >×</span
                >
            </button>
          </div>
          <div class="p-8 bg-gradient-to-br from-cyan-100 via-blue-50 to-cyan-200">
            <h3
              class="font-extrabold text-xl md:text-2xl text-cyan-800 mb-3 flex items-center gap-3"
            >
              <span class="text-lg md:text-xl">🐱 Location Cat :</span>
              <span class="text-base md:text-lg">{{ selectedCat.location_name }}</span>
            </h3>
            <p>
              {{ selectedCat.description || '-' }}
            </p>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, nextTick } from "vue";
import { getApiUrl } from "../utils/api";
import { loadGoogleMaps, isGoogleMapsLoaded } from "../utils/googleMapsLoader";
import { getEnvVar } from "../utils/env";

interface CatLocation {
  id: string;
  location_name: string;
  description: string;
  latitude: number;
  longitude: number;
  image_url: string;
}

const isLoading = ref(false);
const error = ref<string | null>(null);
const locations = ref<CatLocation[]>([]);
const selectedCat = ref<CatLocation | null>(null);
const map = ref<any>(null);
const markers = ref<any[]>([]);

const loadCatLocations = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    const apiUrl = getApiUrl("/locations");

    const response = await fetch(apiUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to connect to server (${response.status})`);
    }

    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error("Invalid data format (not JSON)");
    }

    const json = await response.json();

    if (!Array.isArray(json)) {
      throw new Error("Invalid data format");
    }

    locations.value = json as CatLocation[];
    
    // Initialize map after loading locations
    if (locations.value.length > 0) {
      // Add delay to ensure DOM is fully rendered
      setTimeout(() => {
        initializeMap();
      }, 200);
    }
  } catch (err: unknown) {
    error.value = (err as Error).message;
  } finally {
    isLoading.value = false;
  }
};

const initializeMap = async () => {
  // Wait for the DOM to be updated multiple times to ensure rendering
  await nextTick();
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // Check if Google Maps is already loaded
  if (!isGoogleMapsLoaded()) {
    try {
      // Load Google Maps API
      const apiKey = getEnvVar('VITE_GOOGLE_MAPS_API_KEY');
      if (!apiKey) {
        throw new Error("Google Maps API key is missing. Please set VITE_GOOGLE_MAPS_API_KEY in your .env file.");
      }
      
      await loadGoogleMaps({
        apiKey,
        libraries: "places",
        version: "weekly"
      });
    } catch (err: any) {
      error.value = err.message;
      return;
    }
  }

  try {
    // Get the map container element with retry logic
    let mapElement = document.getElementById("map");
    let retries = 0;
    const maxRetries = 10;
    
    while (!mapElement && retries < maxRetries) {
      await new Promise(resolve => setTimeout(resolve, 100));
      mapElement = document.getElementById("map");
      retries++;
    }
    
    if (!mapElement) {
      throw new Error("Map container not found after multiple attempts");
    }

    // Ensure the map container has proper dimensions
    if (mapElement.offsetWidth === 0 || mapElement.offsetHeight === 0) {
      // Force a reflow to ensure proper dimensions
      mapElement.style.height = '400px';
      mapElement.style.width = '100%';
    }

    // Create the map
    const google = (window as any).google;
    map.value = new google.maps.Map(mapElement, {
      zoom: 12,
      center: { lat: 13.7563, lng: 100.5018 }, // Default to Bangkok
      mapTypeControl: true,
      streetViewControl: true,
      fullscreenControl: true,
    });

    // Add markers for each cat location
    addMarkers();
  } catch (err: any) {
    error.value = `Failed to initialize map: ${err.message}`;
  }
};

const addMarkers = () => {
  // Clear existing markers
  markers.value.forEach(marker => marker.setMap(null));
  markers.value = [];

  if (!map.value || locations.value.length === 0) return;

  const google = (window as any).google;

  // Create bounds to fit all markers
  const bounds = new google.maps.LatLngBounds();

  locations.value.forEach(location => {
    const marker = new google.maps.Marker({
      position: { lat: location.latitude, lng: location.longitude },
      map: map.value,
      title: location.location_name,
      animation: google.maps.Animation.DROP,
      icon: {
        url: '/location_10753796.png',
        scaledSize: new google.maps.Size(32, 32)
      }
    });

    // Add click listener to marker
    marker.addListener("click", () => {
      selectCat(location);
    });

    markers.value.push(marker);
    bounds.extend({ lat: location.latitude, lng: location.longitude });
  });

  // Fit map to show all markers
  if (locations.value.length > 1) {
    map.value.fitBounds(bounds);
  } else if (locations.value.length === 1) {
    // If only one location, center on it with appropriate zoom
    map.value.setCenter({ lat: locations.value[0].latitude, lng: locations.value[0].longitude });
    map.value.setZoom(15);
  }
};


const selectCat = (cat: CatLocation) => {
  selectedCat.value = cat;
};

const closeModal = () => {
  selectedCat.value = null;
};

onMounted(() => {
  loadCatLocations();
});
</script>

<style scoped>
/* No custom styles needed - all converted to Tailwind CSS */
</style>