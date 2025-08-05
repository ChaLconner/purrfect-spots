<template>
  <div
    class="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200"
  >
    <!-- Header -->
    <div class="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6">
      <h2 class="text-2xl font-bold flex items-center gap-3">
        <span class="text-3xl">🐱</span>
        <span>แผนที่จุดพบน้องแมว</span>
      </h2>
      <p class="text-purple-100 text-sm mt-2">
        ค้นหาน้องแมวน่ารักในพื้นที่ต่างๆ
      </p>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center p-12">
      <div class="flex flex-col items-center">
        <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mb-4"></div>
        <h3 class="text-lg font-semibold text-gray-700 mb-2">🗺️ กำลังโหลดแผนที่...</h3>
        <p class="text-sm text-gray-500">เรากำลังค้นหาตำแหน่งแมวทั้งหมดให้คุณ</p>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="bg-red-50 border border-red-200 rounded-lg m-6 p-6"
    >
      <div class="flex items-center gap-3 mb-3">
        <span class="text-2xl">⚠️</span>
        <h3 class="text-red-800 font-semibold">เกิดข้อผิดพลาด</h3>
      </div>
      <p class="text-red-700 mb-4">{{ error }}</p>
      <button
        @click="loadCatLocations"
        class="px-6 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
      >
        ลองใหม่อีกครั้ง
      </button>
    </div>

    <!-- Map -->
    <div v-if="!isLoading && !error" class="relative">
      <div id="map" class="h-96 w-full z-[1]"></div>

      <!-- Stats Panel -->
      <div
        class="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-md p-4 border border-gray-200"
      >
        <div class="flex items-center gap-3">
          <div class="w-4 h-4 bg-purple-500 rounded-full"></div>
          <span class="text-sm font-medium text-gray-700">
            จำนวนจุด:
            <span class="font-bold text-purple-600">{{
              locations.length
            }}</span>
            แห่ง
          </span>
        </div>
      </div>
    </div>

    <!-- Cat Details Modal -->
    <div
      v-if="selectedCat"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click="closeModal"
    >
      <div
        class="bg-white rounded-2xl max-w-md w-full overflow-hidden shadow-2xl transform transition-all"
        @click.stop
      >
        <div class="relative">
          <img
            :src="selectedCat.image_url"
            :alt="selectedCat.location_name"
            class="w-full h-48 object-cover"
          />
          <button
            @click="closeModal"
            class="absolute top-3 right-3 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-full p-2 transition-all shadow-md"
          >
            <span class="text-gray-600 text-xl font-bold">×</span>
          </button>
        </div>
        <div class="p-6">
          <h3 class="font-bold text-xl text-gray-800 mb-3">
            {{ selectedCat.location_name }}
          </h3>
          <p class="text-gray-600 text-sm mb-4 leading-relaxed">
            {{ selectedCat.description }}
          </p>
          <div
            class="flex items-center justify-between text-xs text-gray-500 mb-4"
          >
            <span class="flex items-center gap-1">
              <span>📍</span>
              <span
                >{{ selectedCat.latitude.toFixed(4) }},
                {{ selectedCat.longitude.toFixed(4) }}</span
              >
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, onUnmounted, nextTick } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { getApiUrl } from '../utils/api';

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
    const response = await fetch(getApiUrl('/locations'), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) throw new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่สำเร็จ");

    const json = await response.json();
    if (!Array.isArray(json)) throw new Error("รูปแบบข้อมูลไม่ถูกต้อง");
    locations.value = json as CatLocation[];

    // Clear previous markers
    clearMarkers();
  } catch (err: unknown) {
    console.warn("ดึงข้อมูลไม่สำเร็จ:", err);
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
      `<strong>${loc.location_name}</strong><br/>${loc.description}`
    );
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
