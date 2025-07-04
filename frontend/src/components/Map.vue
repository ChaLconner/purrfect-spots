<template>
  <div class="relative bg-gray-50 rounded-lg shadow-md overflow-hidden">
    <!-- Header -->
    <div class="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4">
      <h2 class="text-xl font-bold flex items-center gap-2">
        <span>🐱</span>
        <span>แผนที่จุดพบน้องแมว</span>
      </h2>
      <p class="text-purple-100 text-sm mt-1">
        ค้นหาน้องแมวน่ารักในพื้นที่ต่างๆ
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center p-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      <span class="ml-3 text-gray-600">กำลังโหลดข้อมูล...</span>
    </div>

    <!-- Error State -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg m-4 p-4">
      <div class="flex items-center gap-2 text-red-700">
        <span>⚠️</span>
        <span class="font-semibold">เกิดข้อผิดพลาด</span>
      </div>
      <p class="text-red-600 text-sm mt-1">{{ error }}</p>
      <button 
        @click="loadCatLocations" 
        class="mt-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
      >
        ลองใหม่อีกครั้ง
      </button>
    </div>

    <!-- Map Container -->
    <div v-if="!isLoading" class="relative">
      <div id="map" class="h-96 w-full"></div>
      
      <!-- Info Panel -->
      <div class="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3 max-w-xs z-[1000]">
        <div class="text-sm">
          <div class="font-semibold text-gray-800 mb-1">สถิติน้องแมว</div>
          <div class="text-gray-600">
            <span class="inline-block w-3 h-3 bg-purple-500 rounded-full mr-2"></span>
            จำนวนจุด: {{ locations.length }} แห่ง
          </div>
        </div>
      </div>
    </div>

    <!-- Selected Cat Info Modal -->
    <div v-if="selectedCat" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[2000]" @click="closeModal">
      <div class="bg-white rounded-lg max-w-md w-full mx-4 overflow-hidden" @click.stop>
        <div class="relative">
          <img 
            :src="selectedCat.image_url" 
            :alt="selectedCat.name"
            class="w-full h-48 object-cover"
            @error="handleImageError"
          >
          <button 
            @click="closeModal" 
            class="absolute top-2 right-2 bg-white bg-opacity-80 hover:bg-opacity-100 rounded-full p-2 transition-all"
          >
            <span class="text-gray-600 text-lg">×</span>
          </button>
        </div>
        <div class="p-4">
          <h3 class="font-bold text-lg text-gray-800 mb-2">{{ selectedCat.name }}</h3>
          <p class="text-gray-600 text-sm mb-3">{{ selectedCat.description }}</p>
          <div class="flex items-center justify-between text-xs text-gray-500">
            <span>📍 {{ selectedCat.latitude }}, {{ selectedCat.longitude }}</span>
            <span>🐾 รหัส: {{ selectedCat.id }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue';
import L from 'leaflet';

// Types
interface CatLocation {
  id: string;
  name: string;
  description: string;
  latitude: number;
  longitude: number;
  image_url: string;
}

// State
const isLoading = ref(false);
const error = ref<string | null>(null);
const locations = ref<CatLocation[]>([]);
const selectedCat = ref<CatLocation | null>(null);
let map: L.Map | null = null;

// Custom cat icon
const catIcon = L.divIcon({
  html: `
    <div class="relative">
      <div class="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center shadow-lg border-2 border-white">
        <span class="text-white text-lg">🐱</span>
      </div>
      <div class="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-purple-500"></div>
    </div>
  `,
  className: 'custom-cat-marker',
  iconSize: [32, 40],
  iconAnchor: [16, 40],
  popupAnchor: [0, -40]
});

// Load cat locations from backend
const loadCatLocations = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    const response = await fetch('/api/locations');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    locations.value = data.locations || [];
    
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'เกิดข้อผิดพลาดในการโหลดข้อมูล';
    console.error('Error loading cat locations:', err);
    // Set empty locations on error so map can still initialize
    locations.value = [];
  } finally {
    isLoading.value = false;
    // Always try to initialize map after loading is complete
    // Wait for next tick to ensure DOM is updated
    await new Promise(resolve => setTimeout(resolve, 100));
    initializeMap();
  }
};

// Initialize map
const initializeMap = () => {
  // Check if map container exists
  const mapContainer = document.getElementById('map');
  if (!mapContainer) {
    console.error('Map container not found');
    return;
  }

  if (map) {
    map.remove();
  }

  // Set initial view to first location or default to Chiang Mai
  const initialLocation = locations.value.length > 0 
    ? [locations.value[0].latitude, locations.value[0].longitude] as [number, number]
    : [18.7883, 98.9853] as [number, number]; // Chiang Mai coordinates

  map = L.map('map').setView(initialLocation, 13);

  // Add tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  // Add markers for each cat location
  locations.value.forEach(location => {
    L.marker([location.latitude, location.longitude], { icon: catIcon })
      .addTo(map!)
      .bindPopup(`
        <div class="p-2 min-w-[200px]">
          <div class="font-semibold text-sm mb-1">${location.name}</div>
          <div class="text-xs text-gray-600 mb-2">${location.description}</div>
          <button 
            onclick="window.showCatDetails('${location.id}')" 
            class="w-full bg-purple-500 text-white px-3 py-1 rounded text-xs hover:bg-purple-600 transition-colors"
          >
            ดูรายละเอียด
          </button>
        </div>
      `);
  });

  // Fit map to show all markers
  if (locations.value.length > 1) {
    const markers = locations.value.map(location => 
      L.marker([location.latitude, location.longitude])
    );
    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
  }
};

// Show cat details modal
const showCatDetails = (id: string) => {
  const cat = locations.value.find(location => location.id === id);
  if (cat) {
    selectedCat.value = cat;
  }
};

// Close modal
const closeModal = () => {
  selectedCat.value = null;
};

// Handle image error
const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement;
  target.src = 'https://via.placeholder.com/400x300/e5e7eb/6b7280?text=No+Image';
};

// Mount component
onMounted(async () => {
  // Make showCatDetails available globally for popup buttons
  (window as any).showCatDetails = showCatDetails;
  
  await loadCatLocations();
});

// Cleanup
onUnmounted(() => {
  if (map) {
    map.remove();
  }
  delete (window as any).showCatDetails;
});
</script>

<style scoped>
/* Custom marker styles */
:deep(.custom-cat-marker) {
  background: none;
  border: none;
}

/* Popup styles */
:deep(.leaflet-popup-content) {
  margin: 0;
  padding: 0;
}

:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

:deep(.leaflet-popup-tip) {
  background: white;
}

/* Loading animation */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
