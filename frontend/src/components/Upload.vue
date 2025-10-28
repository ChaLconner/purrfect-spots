<template>
  <div class="max-w-4xl mx-auto mt-8 p-6 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl shadow-xl">
    <!-- Header with icon -->
    <div class="text-center mb-8">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mb-4">
        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
      </div>
      <h2 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600 mb-2">
        Share Your Cat's Favorite Spot
      </h2>
      <p class="text-gray-600">Help other cat lovers find purrfect places for their feline friends</p>
    </div>

    <!-- Upload Form -->
    <form @submit.prevent="handleSubmit" v-if="!isUploading && !uploadSuccess" class="space-y-8">
      <!-- Location Information Section -->
      <div class="bg-white rounded-xl p-6 shadow-md">
        <div class="flex items-center mb-4">
          <div class="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mr-3">
            <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-800">Location Information</h3>
        </div>
        
        <div class="grid md:grid-cols-2 gap-6">
          <div>
            <label for="locationName" class="mb-2 text-sm font-medium text-gray-700 flex items-center">
              <svg class="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Location Name
            </label>
            <input
              id="locationName"
              v-model="locationName"
              type="text"
              placeholder="e.g., Central Park Cat Garden"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg text-base transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          
          <div class="md:col-span-2">
            <label for="description" class="mb-2 text-sm font-medium text-gray-700 flex items-center">
              <svg class="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              Description
            </label>
            <textarea
              id="description"
              v-model="description"
              placeholder="Describe this location and why cats love it..."
              rows="3"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg text-base transition-all duration-200 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Map Section -->
      <div class="bg-white rounded-xl p-6 shadow-md">
        <div class="flex items-center mb-4">
          <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-3">
            <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-800">Location on Map</h3>
        </div>
        
        <div class="mb-4">
          <button
            type="button"
            @click="getCurrentLocation"
            :disabled="gettingLocation"
            class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-500 to-teal-500 text-white font-medium rounded-lg shadow-md hover:from-green-600 hover:to-teal-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="!gettingLocation" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
            <svg v-else class="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ gettingLocation ? "Getting Location..." : "Use Current Location" }}
          </button>
        </div>        
        
        <!-- Google Map Preview -->
        <div class="mt-4">
          <label class="block mb-2 text-sm font-medium text-gray-700">Location Preview</label>
          <div 
            v-show="!isUploading" 
            class="h-64 w-full rounded-xl overflow-hidden border-2 border-gray-200 shadow-inner"
          >
            <div id="uploadMap" class="w-full h-full rounded-xl"></div>
          </div>
          <div class="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p class="text-sm text-blue-700 flex items-start">
              <svg class="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
              </svg>
              Click on the map or drag the marker to select a location
            </p>
          </div>
        </div>
      </div>

      <!-- Photo Upload Section -->
      <div class="bg-white rounded-xl p-6 shadow-md">
        <div class="flex items-center mb-4">
          <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mr-3">
            <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-800">Cat Photo</h3>
        </div>
        
        <div
          class="relative border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer transition-all duration-200 hover:border-purple-400 hover:bg-purple-50"
          @dragover.prevent
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            @change="handleFileChange"
            class="hidden"
          />
          
          <div v-if="previewUrl" class="space-y-4">
            <div class="relative inline-block">
              <img
                :src="previewUrl"
                alt="Preview"
                class="max-w-full max-h-64 rounded-lg shadow-md mx-auto"
              />
            </div>
            
            <div class="bg-gray-50 rounded-lg p-3">
              <p class="text-sm text-gray-600 font-medium">{{ file?.name }}</p>
              <p v-if="file" class="text-xs text-gray-500 mt-1">{{ (file.size / 1024 / 1024).toFixed(2) }} MB</p>
            </div>
            
            <!-- Cat Detection Details -->
            <div v-if="catDetectionResult && !isDetectingCats && catDetectionResult.has_cats" 
                 class="bg-green-50 border border-green-200 rounded-lg p-3">
              <p class="text-sm text-green-700 font-medium flex items-center">
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                verify cat
              </p>
            </div>
          </div>
          
          <div v-else class="space-y-4">
            <div class="flex justify-center">
              <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
                <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
              </div>
            </div>
            <div>
              <p class="text-gray-600 font-medium mb-2">Drag and drop your cat photo here</p>
              <p class="text-gray-500 text-sm mb-4">or</p>
              <button
                type="button"
                class="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium rounded-lg shadow-md hover:from-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all duration-200 cursor-pointer"
              >
                Browse Files
              </button>
            </div>
            <p class="text-xs text-gray-500">Supported formats: JPG, PNG, GIF (Max 10MB)</p>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
        <div class="flex">
          <div class="ml-3">
            <p class="text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Authentication Warning -->
      <div v-if="!isAuthenticated" class="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-amber-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm text-amber-700 font-medium">Authentication required</p>
            <p class="text-sm text-amber-600 mt-1">You must be logged in to upload photos.</p>
          </div>
        </div>
      </div>
      
      <!-- Submit Button -->
      <button
        type="submit"
        :disabled="!canSubmit"
        class="w-full py-4 px-6 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white font-bold text-lg rounded-xl shadow-lg hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] disabled:hover:scale-100 cursor-pointer"
      >
        <span v-if="!isAuthenticated" class="flex items-center justify-center">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path>
          </svg>
          Login to Upload
        </span>
        <span v-else class="flex items-center justify-center">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
          </svg>
          Share Cat Location
        </span>
      </button>
    </form> 
    
    <!-- Upload Progress -->
    <div v-if="isUploading" class="bg-white rounded-xl p-8 shadow-md">
      <div class="text-center mb-6">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
          <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <h3 class="text-xl font-semibold text-gray-800 mb-2">Uploading your cat's photo...</h3>
        <p class="text-gray-600">Please wait while we process your submission</p>
      </div>
      
      <div class="w-full bg-gray-200 rounded-full h-4 mb-4">
        <div 
          class="bg-gradient-to-r from-blue-500 to-indigo-600 h-4 rounded-full transition-all duration-300 ease-out" 
          :style="{ width: `${uploadProgress}%` }"
        ></div>
      </div>
      
      <div class="flex justify-between text-sm text-gray-600">
        <span>Progress</span>
        <span class="font-medium">{{ uploadProgress }}%</span>
      </div>
    </div>
    
    <!-- Success Message -->
    <div v-if="uploadSuccess" class="bg-white rounded-xl p-8 shadow-md text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
        <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
      </div>
      <h3 class="text-2xl font-bold text-gray-800 mb-2">Upload Successful!</h3>
      <p class="text-gray-600 mb-6">Your cat's favorite spot has been shared with the community.</p>
      <div class="flex justify-center space-x-4">
        <button 
          @click="window.location.reload()" 
          class="px-6 py-2 bg-gradient-to-r from-green-500 to-teal-500 text-white font-medium rounded-lg shadow-md hover:from-green-600 hover:to-teal-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-all duration-200"
        >
          Upload Another Photo
        </button>
        <button 
          @click="router.push('/map')" 
          class="px-6 py-2 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg shadow-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-all duration-200"
        >
          View Map
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onErrorCaptured, nextTick, shallowRef, computed } from "vue";
import { useRouter } from "vue-router";
import { useUploadCat } from "../composables/useUploadCat";
import { authStore, getAuthHeader } from "../store/auth";
import { catDetectionService } from "../services/catDetectionService";
import { uploadFile, ApiError, ApiErrorTypes } from "../utils/api";
import { loadGoogleMaps, getGoogleMaps } from "../utils/googleMapsLoader";
import { isDev, getEnvVar } from "../utils/env";

const router = useRouter();

// Google Maps API Key from environment variables
const googleMapsApiKey = getEnvVar('VITE_GOOGLE_MAPS_API_KEY');

// Use shallowRef for objects to avoid deep reactivity
const locationName = ref("");
const description = ref("");
const latitude = ref("18.7883");
const longitude = ref("98.9853");
const file = ref(null);
const previewUrl = ref(null);
const fileInput = ref(null);
const uploadSuccess = ref(false);
const gettingLocation = ref(false);
const isDetectingCats = ref(false);
const catDetectionResult = ref(null);
const showDetectionResults = ref(false);

// Map center for Google Maps - use shallowRef for performance
const mapCenter = shallowRef({ lat: 18.7883, lng: 98.9853 });
const uploadMap = shallowRef(null);
const uploadMarker = shallowRef(null);

// Custom marker icon - cache to prevent recreation
const markerIcon = Object.freeze({
  url: "/location_10753796.png",
  scaledSize: { width: 32, height: 32 }
});

// Computed properties for frequently accessed values
const isAuthenticated = computed(() => authStore.isAuthenticated);
const canSubmit = computed(() =>
  isAuthenticated.value &&
  file.value &&
  !isDetectingCats.value &&
  catDetectionResult.value?.has_cats
);

const { uploadCatPhoto, isUploading, error, uploadProgress } = useUploadCat();

onMounted(async () => {
  // Initialize any necessary data
  if (!googleMapsApiKey) {
    error.value = "Map service is unavailable. Please contact support.";
    return;
  }
  
  // Wait for DOM to be fully ready
  await nextTick();
  
  // Add a small delay to ensure everything is rendered
  setTimeout(() => {
    initializeUploadMap();
  }, 100);
});

// Custom marker icon with hover effect - optimize by caching hover icon
const hoverIcon = Object.freeze({
  url: "/location_10753796.png",
  scaledSize: { width: 38, height: 38 }
});

const createMarkerWithHover = (position, title, map) => {
  const googleMaps = getGoogleMaps();
  if (!googleMaps) return null;
  
  const marker = new googleMaps.Marker({
    position,
    map,
    title,
    icon: markerIcon
  });
  
  // Add hover effect
  marker.addListener('mouseover', () => {
    marker.setIcon(hoverIcon);
    marker.setAnimation(googleMaps.Animation.BOUNCE);
  });
  
  marker.addListener('mouseout', () => {
    marker.setIcon(markerIcon);
    marker.setAnimation(null);
  });
  
  return marker;
};


onErrorCaptured((err) => {
  if (err.message && err.message.includes("message channel closed")) {
    return false;
  }
  if (err.message && err.message.includes("asynchronous response by returning true, but the message channel closed")) {
    return false;
  }
  return true;
  return true;
});

onMounted(() => {
  window.addEventListener("unhandledrejection", (event) => {
    if (
      event.reason &&
      event.reason.message &&
      (event.reason.message.includes("message channel closed") ||
       event.reason.message.includes("asynchronous response by returning true, but the message channel closed"))
    ) {
      event.preventDefault();
    }
  });
  
  // Also handle regular error events
  window.addEventListener("error", (event) => {
    if (
      event.message &&
      (event.message.includes("message channel closed") ||
       event.message.includes("asynchronous response by returning true, but the message channel closed"))
    ) {
      event.preventDefault();
    }
  });
});


function getCurrentLocation() {
  gettingLocation.value = true;
  error.value = null;

  if (!navigator.geolocation) {
    error.value = "Geolocation is not supported by your browser.";
    gettingLocation.value = false;
    return;
  }

  // Cache geolocation options to prevent recreation
  const geoOptions = Object.freeze({
    enableHighAccuracy: true,
    timeout: 15000,
    maximumAge: 0
  });

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      const latStr = lat.toFixed(6);
      const lngStr = lng.toFixed(6);
      
      latitude.value = latStr;
      longitude.value = lngStr;
      
      // Update map center - reuse object reference when possible
      const newCenter = { lat, lng };
      mapCenter.value = newCenter;
      
      // Debounce map update
      requestAnimationFrame(() => updateUploadMap());
      
      gettingLocation.value = false;
    },
    (err) => {
      // Cache error messages to prevent recreation
      const errorMessages = Object.freeze({
        [err.PERMISSION_DENIED]: "Permission denied. Please allow location access.",
        [err.POSITION_UNAVAILABLE]: "Location information is unavailable.",
        [err.TIMEOUT]: "The request to get user location timed out."
      });
      
      error.value = errorMessages[err.code] || "An unknown error occurred while getting location.";
      gettingLocation.value = false;
    },
    geoOptions
  );
}

// Handle map click to set coordinates - optimize by debouncing
let mapUpdateTimeout = null;
const updateCoordinates = (lat, lng) => {
  const latStr = lat.toFixed(6);
  const lngStr = lng.toFixed(6);
  
  latitude.value = latStr;
  longitude.value = lngStr;
  mapCenter.value = { lat, lng };
  
  // Debounce map updates
  if (mapUpdateTimeout) clearTimeout(mapUpdateTimeout);
  mapUpdateTimeout = setTimeout(() => updateUploadMap(), 16); // ~60fps
};

function handleMapClick(event) {
  const lat = event.latLng.lat();
  const lng = event.latLng.lng();
  updateCoordinates(lat, lng);
}

// Handle marker drag to update coordinates
function handleMarkerDrag(event) {
  const lat = event.latLng.lat();
  const lng = event.latLng.lng();
  updateCoordinates(lat, lng);
}

function triggerFileInput() {
  fileInput.value.click();
}

// Common file processing function to avoid code duplication
const processFile = (imageFile) => {
  if (!imageFile || !imageFile.type.startsWith("image/")) return;
  
  file.value = imageFile;
  previewUrl.value = URL.createObjectURL(imageFile);
  error.value = null;
  detectCatsInImage(imageFile);
};

function handleFileChange(e) {
  const selected = e.target.files[0];
  processFile(selected);
}

function handleDrop(e) {
  const dropped = e.dataTransfer.files[0];
  processFile(dropped);
}

async function detectCatsInImage(imageFile) {
  if (!imageFile) return;
  
  isDetectingCats.value = true;
  catDetectionResult.value = null;
  showDetectionResults.value = false;
  error.value = null;
  
  try {
    // Use the correct method name from the service
    const result = await catDetectionService.detectCats(imageFile);
    
    // Check the validity of the received data
    if (!result || typeof result.has_cats === 'undefined') {
      throw new Error('Invalid response from cat detection service');
    }
    
    catDetectionResult.value = result;
    showDetectionResults.value = true;
    
    // Cache confidence threshold
    const CONFIDENCE_THRESHOLD = 60;
    
    // Check if cats are found
    if (!result.has_cats || result.cat_count === 0) {
      error.value = `❌ No cats found in the image. Please upload an image with cats`;
      file.value = null;
      previewUrl.value = null;
      showDetectionResults.value = false;
    } else if (result.confidence < CONFIDENCE_THRESHOLD) {
      error.value = `⚠️ Cat detected but with low confidence (${result.confidence}%) Please upload a clearer image`;
      file.value = null;
      previewUrl.value = null;
      showDetectionResults.value = false;
    }
    
  } catch (error) {
    // Handle API errors specifically
    if (error instanceof ApiError) {
      let errorMessage = `⚠️ `;
      
      switch (error.type) {
        case ApiErrorTypes.NETWORK_ERROR:
          errorMessage += 'Unable to connect to cat detection service. Please check your internet connection';
          break;
        case ApiErrorTypes.AUTHENTICATION_ERROR:
          errorMessage += 'Authentication error. Please log in again';
          break;
        case ApiErrorTypes.SERVER_ERROR:
          errorMessage += 'Server error. Please try again later';
          break;
        default:
          errorMessage += error.message || 'Unable to check image';
      }
      
      error.value = errorMessage;
    } else {
      // Cache error patterns to avoid repeated string operations
      const errorPatterns = Object.freeze({
        'Failed to fetch': `⚠️ Unable to connect to cat detection service. Please check your internet connection`,
        'NetworkError': `⚠️ Unable to connect to cat detection service. Please check your internet connection`,
        'Authentication': `⚠️ Authentication error. Please log in again`,
        'Invalid response': `⚠️ Received invalid data from server. Please try again`
      });
      
      let errorMessage = `⚠️ Unable to check image: ${error.message}`;
      
      // Check for specific error types
      for (const [pattern, message] of Object.entries(errorPatterns)) {
        if (error.message.includes(pattern)) {
          errorMessage = message;
          break;
        }
      }
      
      error.value = errorMessage;
    }
    
    // Do not allow upload if detection fails
    catDetectionResult.value = null;
    showDetectionResults.value = false;
  } finally {
    isDetectingCats.value = false;
  }
}

async function handleSubmit() {
  // Early return for unauthenticated users
  if (!isAuthenticated.value || !authStore.user) {
    sessionStorage.setItem('redirectAfterAuth', '/upload');
    router.push('/login');
    return;
  }

  // Cache validation threshold
  const CONFIDENCE_THRESHOLD = 60;
  
  // Validate file and detection result
  if (!file.value) {
    error.value = "Please select an image file";
    return;
  }
  
  if (!catDetectionResult.value) {
    error.value = "Please wait for image verification to complete";
    return;
  }
  
  if (!catDetectionResult.value.has_cats || catDetectionResult.value.cat_count === 0) {
    error.value = "❌ No cats found in the image. Please select an image with cats";
    return;
  }
  
  if (catDetectionResult.value.confidence < CONFIDENCE_THRESHOLD) {
    error.value = `⚠️ Cat detection confidence too low (${catDetectionResult.value.confidence}%) Please upload a clearer image`;
    return;
  }
  
  // Validate coordinates
  if (!latitude.value || !longitude.value || latitude.value === "" || longitude.value === "") {
    error.value = "Please select coordinates on the map. Click on the map or use current location";
    return;
  }
  
  // Validate location name
  if (!locationName.value.trim()) {
    error.value = "Please enter a location name";
    return;
  }

  // Prepare cat detection data
  const catDetectionData = {
    has_cats: catDetectionResult.value.has_cats,
    cat_count: catDetectionResult.value.cat_count,
    confidence: catDetectionResult.value.confidence,
    suitable_for_cat_spot: catDetectionResult.value.suitable_for_cat_spot,
    cats_detected: catDetectionResult.value.cats_detected || [],
    detection_timestamp: new Date().toISOString()
  };
  
  // Prepare location data
  const locationData = {
    lat: latitude.value,
    lng: longitude.value,
    description: description.value.trim() || "",
    location_name: locationName.value.trim()
  };
  
  try {
    const data = await uploadCatPhoto(file.value, locationData, catDetectionData);
    
    if (data) {
      uploadSuccess.value = true;
      // Show success message for longer before reloading
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    }
    
  } catch (err) {
    // Error is already handled by useUploadCat composable
    if (isDev()) {
      console.error('Upload failed:', err);
    }
  }
}

// Initialize upload map - optimize with caching
let mapInitializationAttempts = 0;
const MAX_MAP_INIT_ATTEMPTS = 3;

const initializeUploadMap = async () => {
  try {
    // Check if map element exists before loading script
    const mapElement = document.getElementById("uploadMap");
    
    if (!mapElement) {
      throw new Error("Upload map element not found");
    }
    
    // Load Google Maps API using the centralized loader
    await loadGoogleMaps({
      apiKey: googleMapsApiKey,
      libraries: "places",
      version: "weekly"
    });
    
    const googleMaps = getGoogleMaps();
    
    if (!googleMaps) {
      throw new Error("Google Maps API not loaded properly");
    }
    
    // Cache map options
    const mapOptions = Object.freeze({
      center: mapCenter.value,
      zoom: 13,
      disableDefaultUI: true,
      zoomControl: true,
      mapTypeId: "roadmap",
    });
    
    uploadMap.value = new googleMaps.Map(mapElement, mapOptions);
    
    // Cache initial position
    const initialPosition = {
      lat: parseFloat(latitude.value),
      lng: parseFloat(longitude.value)
    };
    
    // Add initial marker with hover effect
    uploadMarker.value = createMarkerWithHover(
      initialPosition,
      'Selected Location',
      uploadMap.value
    );
    
    if (uploadMarker.value) {
      uploadMarker.value.setDraggable(true);
    }
    
    // Add event listeners
    uploadMap.value.addListener('click', handleMapClick);
    uploadMarker.value.addListener('dragend', handleMarkerDrag);
    
  } catch (err) {
    // Limit retry attempts to prevent infinite loops
    if (mapInitializationAttempts < MAX_MAP_INIT_ATTEMPTS) {
      mapInitializationAttempts++;
      setTimeout(() => {
        initializeUploadMap().catch(retryErr => {
          // Show user-friendly error message
          error.value = "Unable to load map. Please refresh the page and try again.";
        });
      }, 2000);
    } else {
      error.value = "Unable to load map. Please refresh the page and try again.";
    }
  }
};

// Update upload map when coordinates change - optimize with debouncing
let mapUpdateDebounce = null;
const updateUploadMap = () => {
  if (!uploadMap.value || !uploadMarker.value) return;
  
  // Clear existing timeout
  if (mapUpdateDebounce) clearTimeout(mapUpdateDebounce);
  
  // Debounce map updates to improve performance
  mapUpdateDebounce = setTimeout(() => {
    const position = {
      lat: parseFloat(latitude.value),
      lng: parseFloat(longitude.value)
    };
    uploadMap.value.setCenter(position);
    uploadMarker.value.setPosition(position);
  }, 16); // ~60fps
};

// Watch for coordinate changes - optimize with immediate execution for first change
let firstCoordinateChange = true;
watch([latitude, longitude], () => {
  if (latitude.value && longitude.value) {
    if (firstCoordinateChange) {
      firstCoordinateChange = false;
      updateUploadMap(); // Immediate update for first change
    } else {
      updateUploadMap(); // Debounced update for subsequent changes
    }
  }
});
</script>
