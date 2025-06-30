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

// Mockup: simulate real-time cat spot data in Chiang Mai
const mockLocations = [
  { id: 1, name: "วัดพระสิงห์ แมวพระราช", lat: 18.7883, lng: 98.9853 },
  { id: 2, name: "ถนนคนเดิน แมวน่ารัก", lat: 18.7869, lng: 98.9856 },
  { id: 3, name: "วัดเจดีหลวง แมววัด", lat: 18.788, lng: 98.9916 },
  { id: 4, name: "ประตูท่าแพ Cat Cafe", lat: 18.7844, lng: 98.9944 },
];

// Simulate real-time updates by randomly adding a new spot every 5 seconds
function addUserSpot(name, lat, lng, callback) {
  const newSpot = {
    id: Date.now(),
    name,
    lat,
    lng,
  };
  callback(newSpot);
}

onMounted(() => {
  // Focus on Chiang Mai old city center
  map.value = L.map("map").setView([18.7883, 98.9853], 14);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(map.value);

  // Add initial mock locations
  mockLocations.forEach((loc) => {
    const marker = L.marker([loc.lat, loc.lng], { icon: catIcon })
      .addTo(map.value)
      .bindPopup(`<b>${loc.name}</b>`);
    markers.value.push(marker);
  });
});
</script>
