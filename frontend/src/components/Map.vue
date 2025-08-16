<template>
  <div
    class="relative bg-gradient-to-br from-cyan-100 via-blue-50 to-white rounded-2xl shadow-2xl border border-blue-200 overflow-hidden"
  >
    <!-- Header -->
    <div
      class="bg-gradient-to-r from-cyan-700 to-blue-600 text-white px-8 py-7 flex flex-col md:flex-row md:items-center md:justify-between gap-3"
    >
      <div class="flex items-center gap-4">
        <span class="text-4xl drop-shadow-lg">🐾</span>
        <div>
          <h2 class="text-3xl font-extrabold tracking-tight">Purrfect Spots</h2>
          <p class="text-cyan-100 text-base mt-1">
            Find and share adorable cat locations near you!
          </p>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="flex flex-col items-center justify-center py-24"
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
        Loading the cat map...
      </h3>
      <p class="text-gray-500">Fetching all cat locations for you</p>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="bg-red-100/80 border border-red-300 rounded-xl mx-8 my-8 p-8 shadow flex flex-col items-center"
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

    <!-- Map -->
    <div v-if="!isLoading && !error" class="relative">
      <div id="map" class="h-[28rem] w-full z-[1] rounded-b-2xl"></div>
      <!-- Floating Stats Panel -->
      <div
        class="absolute top-5 right-5 bg-white/90 backdrop-blur-md rounded-xl shadow-lg px-6 py-3 border border-cyan-200 flex items-center gap-3"
      >
        <span
          class="inline-flex items-center justify-center w-6 h-6 bg-cyan-500 text-white rounded-full shadow text-lg"
          >🐾</span
        >
        <span class="text-base font-medium text-cyan-700">
          <span class="font-bold">{{ locations.length }}</span> cat spots
        </span>
      </div>
    </div>

    <!-- Cat Details Modal -->
    <transition name="fade">
      <div
        v-if="selectedCat"
        class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
        @click="closeModal"
      >
        <div
          class="bg-transition rounded-3xl max-w-lg w-full overflow-hidden shadow-2xl relative animate-fadeIn"
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
                <span class="text-white text-2xl font-bold"
                >×</span
              >
            </button>
            </div>
            <div class="p-8 bg-gradient-to-br from-cyan-100 via-blue-50 to-cyan-200">
            <h3
              class="font-extrabold text-xl md:text-2xl text-cyan-800 mb-3 flex items-center gap-3"
            >
              <span class="text-lg md:text-xl">🐱Location Cat :</span>
              <span class="text-base md:text-lg">{{ selectedCat.location_name }}</span>
            </h3>
            <p
              class="text-gray-700 text-sm md:text-base mb-6 leading-relaxed border-l-4 border-cyan-400 pl-4 bg-cyan-50/60 rounded"
            >
              {{ selectedCat.description }}
            </p>
            </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, onUnmounted, nextTick } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { getApiUrl } from "../utils/api";

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
let map: L.Map | null = null;
let markers: L.Marker[] = [];

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

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

    // Clear previous markers
    clearMarkers();
  } catch (err: unknown) {
    error.value = (err as Error).message;
  } finally {
    isLoading.value = false;
    await nextTick();
    initializeMap();
  }
};

const clearMarkers = () => {
  markers.forEach((m) => m.remove());
  markers = [];
};

const fitMapBounds = () => {
  if (!map || locations.value.length === 0) return;
  if (locations.value.length === 1) {
    map.setView(
      [locations.value[0].latitude, locations.value[0].longitude],
      13
    );
  } else {
    const group = L.featureGroup(
      locations.value.map((loc) => L.marker([loc.latitude, loc.longitude]))
    );
    map.fitBounds(group.getBounds().pad(0.1));
  }
};

const initializeMap = () => {
  const mapContainer = document.getElementById("map");
  if (!mapContainer) return;

  if (!map) {
    map = L.map(mapContainer).setView([18.7883, 98.9853], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);
  }

  clearMarkers();

  locations.value.forEach((loc) => {
    const marker = L.marker([loc.latitude, loc.longitude]).addTo(map!);
    marker.bindPopup(
      `<strong>${loc.location_name}</strong><br/>${loc.description || ""}`,
      { closeButton: false }
    );
    marker.on("mouseover", function () {
      marker.openPopup();
    });
    marker.on("mouseout", function () {
      marker.closePopup();
    });
    marker.on("click", () => (selectedCat.value = loc));
    markers.push(marker);
  });

  fitMapBounds();
};

const closeModal = () => {
  selectedCat.value = null;
};

onMounted(() => {
  loadCatLocations();
});

onUnmounted(() => {
  if (map) map.remove();
});
</script>
