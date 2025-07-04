<template>
  <div
    id="map"
    class="h-[500px] w-full max-w-3xl mx-auto my-10 rounded-lg shadow-lg"
  />
</template>

<script setup>
import { onMounted, ref } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Custom cat icon
const catIcon = L.icon({
  iconUrl:
    "https://img.icons8.com/?size=100&id=xgvj7yYHIcxn&format=png&color=000000",
  iconSize: [38, 38],
  iconAnchor: [19, 38],
  popupAnchor: [0, -38],
});

const map = ref(null);
const markers = ref([]);
const locations = ref([]);
const loading = ref(true);

// Backend API URL
const API_URL = 'http://localhost:5000';

// Fetch locations from backend
async function fetchLocations() {
  try {
    const response = await fetch(`${API_URL}/locations`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch locations');
    }
    
    const data = await response.json();
    locations.value = data.locations || [];
    
    // Add markers to map
    locations.value.forEach((location) => {
      const popupContent = `
        <div class="text-center">
          <h3 class="font-bold text-lg mb-2">${location.name}</h3>
          <p class="text-sm text-gray-600 mb-2">${location.description}</p>
          <img src="${location.image_url}" alt="${location.name}" class="w-48 h-32 object-cover rounded mx-auto" />
        </div>
      `;
      
      const marker = L.marker([location.latitude, location.longitude], { icon: catIcon })
        .addTo(map.value)
        .bindPopup(popupContent, { maxWidth: 200 });
      markers.value.push(marker);
    });
    
  } catch (error) {
    console.error('Error fetching locations:', error);
    // Fallback to mock data if backend fails
    useMockData();
  } finally {
    loading.value = false;
  }
}

// Fallback mock data
function useMockData() {
  const mockLocations = [
    { id: 1, name: "วัดพระสิงห์ แมวพระราช", lat: 18.7883, lng: 98.9853, description: "แมวสีส้มน่ารักที่วัดพระสิงห์" },
    { id: 2, name: "ถนนคนเดิน แมวน่ารัก", lat: 18.7869, lng: 98.9856, description: "แมวขาวดำที่ถนนคนเดิน" },
    { id: 3, name: "วัดเจดีย์หลวง แมววัด", lat: 18.7880, lng: 98.9916, description: "แมวสีเทาที่วัดเจดีย์หลวง" },
    { id: 4, name: "ประตูท่าแพ Cat Cafe", lat: 18.7844, lng: 98.9944, description: "แมวสีน้ำตาลที่ประตูท่าแพ" },
  ];

  mockLocations.forEach((loc) => {
    const marker = L.marker([loc.lat, loc.lng], { icon: catIcon })
      .addTo(map.value)
      .bindPopup(`<b>${loc.name}</b><br/>${loc.description}`);
    markers.value.push(marker);
  });
}

onMounted(() => {
  // Focus on Chiang Mai old city center
  map.value = L.map("map").setView([18.7883, 98.9853], 14);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(map.value);

  // Fetch locations from backend
  fetchLocations();
});
</script>
