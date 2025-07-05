<template>
  <div class="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
    <!-- Header -->
    <div class="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6">
      <h2 class="text-2xl font-bold flex items-center gap-3">
        <span class="text-3xl">🐱</span>
        <span>แผนที่จุดพบน้องแมว</span>
      </h2>
      <p class="text-purple-100 text-sm mt-2">ค้นหาน้องแมวน่ารักในพื้นที่ต่างๆ</p>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center p-12">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-purple-200 border-t-purple-600"></div>
      <span class="ml-4 text-gray-700 font-medium">กำลังโหลดข้อมูล...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg m-6 p-6">
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
      <div id="map" class="h-96 w-full"></div>
      
      <!-- Stats Panel -->
      <div class="absolute bottom-4 left-4 bg-white bg-opacity-90 backdrop-blur-sm rounded-lg shadow-md p-4 border border-gray-200">
        <div class="flex items-center gap-3">
          <div class="w-4 h-4 bg-purple-500 rounded-full"></div>
          <span class="text-sm font-medium text-gray-700">
            จำนวนจุด: <span class="font-bold text-purple-600">{{ locations.length }}</span> แห่ง
          </span>
        </div>
      </div>
    </div>

    <!-- Cat Details Modal -->
    <div v-if="selectedCat" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click="closeModal">
      <div class="bg-white rounded-2xl max-w-md w-full overflow-hidden shadow-2xl transform transition-all" @click.stop>
        <div class="relative">
          <img 
            :src="selectedCat.image_url" 
            :alt="selectedCat.name" 
            class="w-full h-48 object-cover"
          >
          <button 
            @click="closeModal" 
            class="absolute top-3 right-3 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-full p-2 transition-all shadow-md"
          >
            <span class="text-gray-600 text-xl font-bold">×</span>
          </button>
        </div>
        <div class="p-6">
          <h3 class="font-bold text-xl text-gray-800 mb-3">{{ selectedCat.name }}</h3>
          <p class="text-gray-600 text-sm mb-4 leading-relaxed">{{ selectedCat.description }}</p>
          <div class="flex items-center justify-between text-xs text-gray-500 mb-4">
            <span class="flex items-center gap-1">
              <span>📍</span>
              <span>{{ selectedCat.latitude.toFixed(4) }}, {{ selectedCat.longitude.toFixed(4) }}</span>
            </span>
          </div>
          <button 
            @click="closeModal" 
            class="w-full px-4 py-3 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors"
          >
            ปิด
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue';
import L from 'leaflet';

// Import Leaflet CSS
import 'leaflet/dist/leaflet.css';

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

// Fix default marker icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Load cat locations
const loadCatLocations = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    const response = await fetch('/api/locations');
    if (!response.ok) throw new Error('ไม่สามารถโหลดข้อมูลได้');
    
    const data = await response.json();
    locations.value = data.locations || [];
    
  } catch (err) {
    console.warn('API not available, using sample data');
    // Use sample data when API is not available
    locations.value = [
      {
        id: 'sample-1',
        name: 'วัดพระสิงห์ - แมวพระราช',
        description: 'แมวสีส้มน่ารักที่วัดพระสิงห์ ชอบนอนใต้ต้นไผ่',
        latitude: 18.7883,
        longitude: 98.9853,
        image_url: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400&h=300&fit=crop'
      },
      {
        id: 'sample-2',
        name: 'ถนนคนเดิน - แมวนักเดินทาง',
        description: 'แมวขาวดำที่ถนนคนเดิน มักเดินไปมาหาของกิน',
        latitude: 18.7869,
        longitude: 98.9856,
        image_url: 'https://images.unsplash.com/photo-1571566882372-1598d88abd90?w=400&h=300&fit=crop'
      },
      {
        id: 'sample-3',
        name: 'วัดเจดีย์หลวง - แมววัด',
        description: 'แมวสีเทาที่วัดเจดีย์หลวง เป็นแมวเก่าแก่ของวัด',
        latitude: 18.7880,
        longitude: 98.9916,
        image_url: 'https://images.unsplash.com/photo-1533743983669-94fa5c4338ec?w=400&h=300&fit=crop'
      }
    ];
  } finally {
    isLoading.value = false;
    // Always initialize map after loading
    setTimeout(initializeMap, 100);
  }
};

// Initialize map
const initializeMap = () => {
  console.log('Initializing map...');
  const mapContainer = document.getElementById('map');
  console.log('Map container:', mapContainer);
  
  if (!mapContainer) {
    console.error('Map container not found!');
    return;
  }

  if (map) {
    console.log('Removing existing map...');
    map.remove();
  }

  // Default to Chiang Mai if no locations
  const center = locations.value.length > 0 
    ? [locations.value[0].latitude, locations.value[0].longitude] as [number, number]
    : [18.7883, 98.9853] as [number, number];

  console.log('Creating map with center:', center);
  console.log('Locations:', locations.value);

  try {
    map = L.map('map').setView(center, 13);
    console.log('Map created successfully');

    // Add map tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    console.log('Tiles added');

    // Add cat markers
    locations.value.forEach((location, index) => {
      console.log(`Adding marker ${index}:`, location);
      L.marker([location.latitude, location.longitude])
        .addTo(map!)
        .bindPopup(`
          <div class="p-3 min-w-[200px]">
            <div class="font-bold text-base mb-2">${location.name}</div>
            <div class="text-sm text-gray-600 mb-3">${location.description}</div>
            <button onclick="window.showCatDetails('${location.id}')" 
                    class="w-full bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              ดูรายละเอียด
            </button>
          </div>
        `);
    });
    console.log('All markers added');

    // Fit map to show all markers if multiple locations
    if (locations.value.length > 1) {
      const group = L.featureGroup(
        locations.value.map(location => 
          L.marker([location.latitude, location.longitude])
        )
      );
      map.fitBounds(group.getBounds().pad(0.1));
      console.log('Map bounds fitted');
    }
  } catch (error) {
    console.error('Error initializing map:', error);
  }
};

// Show cat details
const showCatDetails = (id: string) => {
  selectedCat.value = locations.value.find(location => location.id === id) || null;
};

// Close modal
const closeModal = () => {
  selectedCat.value = null;
};

// Component lifecycle
onMounted(() => {
  console.log('Component mounted');
  (window as any).showCatDetails = showCatDetails;
  loadCatLocations();
});

onUnmounted(() => {
  console.log('Component unmounted');
  if (map) map.remove();
  delete (window as any).showCatDetails;
});
</script>

<style scoped>
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Ensure map container has proper styling */
#map {
  z-index: 1;
}

/* Custom popup styling */
:deep(.leaflet-popup-content-wrapper) {
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

:deep(.leaflet-popup-tip) {
  background: white;
  border: 1px solid #e5e7eb;
}

:deep(.leaflet-popup-content) {
  margin: 0;
  padding: 0;
}

/* Backdrop blur support */
@supports (backdrop-filter: blur(4px)) {
  .backdrop-blur-sm {
    backdrop-filter: blur(4px);
  }
}
</style>
