<template>
  <div class="max-w-2xl mx-auto mt-8 p-8 bg-white rounded-xl shadow-md">
    <h2 class="text-center mb-8 text-gray-700 text-2xl font-semibold">
      Upload Your Cat's Photo
    </h2>

    <!-- Upload Form -->
    <form @submit.prevent="handleSubmit" v-if="!isUploading">
      <div class="mb-6">
        <label for="locationName" class="block mb-2 font-medium text-gray-700"
          >Location Name</label
        >
        <input
          id="locationName"
          v-model="locationName"
          type="text"
          placeholder="Enter location name"
          required
          class="w-full px-3 py-3 border border-gray-300 rounded-lg text-base transition-colors focus:outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
        />
      </div>
      <div class="mb-6">
        <label for="description" class="block mb-2 font-medium text-gray-700"
          >Description</label
        >
        <textarea
          id="description"
          v-model="description"
          placeholder="Enter description"
          rows="3"
          class="w-full px-3 py-3 border border-gray-300 rounded-lg text-base transition-colors resize-none focus:outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
        ></textarea>
      </div>

      <!-- GPS Coordinates -->
      <div class="mb-6">
        <label class="block mb-2 font-medium text-gray-700"
          >Select Location on Map</label
        >
        <div class="mb-3">
          <button
            type="button"
            @click="getCurrentLocation"
            :disabled="gettingLocation"
            class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{
              gettingLocation ? "Getting Location..." : "Use Current Location"
            }}
          </button>
        </div>

        <l-map
          style="
            height: 250px;
            width: 100%;
            border-radius: 0.75rem;
            overflow: hidden;
          "
          :zoom="mapZoom"
          :center="mapCenter"
          @update:center="onMapMove"
          @click="onMapClick"
        >
          <l-tile-layer :url="tileLayerUrl" :attribution="tileLayerAttr" />
          <l-marker
            :lat-lng="markerLatLng"
            :draggable="true"
            @update:lat-lng="onMarkerDrag"
            @moveend="onMarkerDrag"
          />
        </l-map>

        <p class="text-sm text-gray-600 mt-2">
          💡 คลิกบนแผนที่หรือลาก marker เพื่อเลือกตำแหน่ง
        </p>
      </div>

      <!-- File Upload Area -->
      <div
        class="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer transition-all mb-6 hover:border-emerald-500 hover:bg-green-50"
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
        <div v-if="previewUrl">
          <img
            :src="previewUrl"
            alt="Preview"
            class="max-w-full max-h-72 rounded-lg shadow-md mx-auto"
          />
          <p class="mt-4 text-gray-600">{{ file?.name }}</p>
          
          <!-- Cat Detection Loading -->
          <div v-if="isDetectingCats" class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div class="flex items-center justify-center">
              <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-3"></div>
              <span class="text-blue-700">🔍 กำลังตรวจสอบแมวในรูปภาพ...</span>
            </div>
          </div>
          
          <!-- Cat Detection Results -->
          <div v-if="showDetectionResults && catDetectionResult" class="mt-4">
            <!-- Success: Cat Found -->
            <div v-if="catDetectionResult.has_cats" class="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div class="flex items-center mb-2">
                <svg class="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                <span class="text-green-700 font-semibold">✅ พบแมวในรูปภาพ!</span>
              </div>
              <div class="text-sm text-green-600">
                <p>🐱 จำนวนแมว: {{ catDetectionResult.cat_count }} ตัว</p>
                <p>📊 ความมั่นใจ: {{ catDetectionResult.confidence }}%</p>
                <p>🏠 เหมาะสำหรับ Cat Spot: {{ catDetectionResult.suitable_for_cat_spot ? 'ใช่' : 'ไม่' }}</p>
                <p v-if="catDetectionResult.reasoning" class="mt-2 italic">💭 {{ catDetectionResult.reasoning }}</p>
                
                <!-- แสดงข้อมูลแมวที่พบ -->
                <div v-if="catDetectionResult.cats_detected && catDetectionResult.cats_detected.length > 0" class="mt-3">
                  <p class="font-semibold mb-2">รายละเอียดแมวที่พบ:</p>
                  <div v-for="(cat, index) in catDetectionResult.cats_detected" :key="index" class="bg-white p-2 rounded border mb-2">
                    <p><strong>คำอธิบาย:</strong> {{ cat.description }}</p>
                    <p><strong>พันธุ์ (คาดการณ์):</strong> {{ cat.breed_guess }}</p>
                    <p><strong>ตำแหน่ง:</strong> {{ cat.position }}</p>
                    <p><strong>ขนาด:</strong> {{ cat.size }}</p>
                  </div>
                </div>
              </div>
              
              <div v-if="catDetectionResult.note" class="mt-2 text-xs text-gray-500 italic">
                📝 {{ catDetectionResult.note }}
              </div>
            </div>
            
            <!-- Error: No Cat Found -->
            <div v-else class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div class="flex items-center mb-2">
                <svg class="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
                <span class="text-red-700 font-semibold">❌ ไม่พบแมวในรูปภาพ</span>
              </div>
              <div class="text-sm text-red-600">
                <p>📊 ความมั่นใจ: {{ catDetectionResult.confidence }}%</p>
                <p>📷 คุณภาพรูป: {{ catDetectionResult.image_quality }}</p>
                <p v-if="catDetectionResult.reasoning" class="mt-2 italic">💭 {{ catDetectionResult.reasoning }}</p>
              </div>
              <p class="text-sm text-red-700 mt-3 font-medium">
                กรุณาอัพโหลดรูปภาพที่มีแมวเท่านั้น
              </p>
            </div>
          </div>
        </div>
        <div v-else>
          <p class="mb-4 text-gray-500 text-lg">
            Drag and drop or click to upload
          </p>
          <button
            type="button"
            class="bg-emerald-500 text-white border-none px-4 py-2 rounded-md cursor-pointer transition-colors hover:bg-emerald-600"
          >
            Browse Files
          </button>
        </div>
      </div>

      <!-- Submit Button -->
      <div v-if="!authStore.isAuthenticated" class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded-lg mb-4">
        <div class="flex items-center">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
          </svg>
          <span>You must be logged in to upload photos.</span>
        </div>
      </div>
      <button
        type="submit"
        :disabled="!authStore.isAuthenticated || !file || isDetectingCats || (catDetectionResult && !catDetectionResult.has_cats)"
        class="w-full bg-emerald-500 text-white border-none py-3.5 px-6 rounded-lg text-lg font-medium cursor-pointer transition-colors hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span v-if="!authStore.isAuthenticated">Login to Upload</span>
        <span v-else-if="isDetectingCats">🔍 Detecting Cats...</span>
        <span v-else-if="catDetectionResult && !catDetectionResult.has_cats">❌ No Cat Detected</span>
        <span v-else>🐱 Upload Cat Photo</span>
      </button>
    </form>

    <!-- Upload Progress -->
    <div v-if="isUploading" class="text-center py-8">
      <div class="flex flex-col items-center">
        <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500 mb-4"></div>
        <h3 class="text-lg font-semibold text-gray-700 mb-2">🐱 กำลังอัปโหลดรูปแมว...</h3>
        <p class="text-sm text-gray-500">กรุณารอสักครู่ เราพยายามประมวลผลรูปภาพของคุณ</p>
      </div>
    </div>

    <!-- Success Message -->
    <div v-if="uploadSuccess" class="text-center">
      <div class="mb-4">
        <svg
          class="h-16 w-16 text-green-500 mx-auto"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 13l4 4L19 7"
          ></path>
        </svg>
      </div>
      <p class="text-green-600 text-lg mb-4">Photo uploaded successfully!</p>
    </div>

    <!-- Error Message -->
    <div
      v-if="error"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6"
    >
      <p class="font-bold">Error:</p>
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onErrorCaptured } from "vue";
import { useRouter } from "vue-router";
import { LMap, LTileLayer, LMarker } from "@vue-leaflet/vue-leaflet";
import "leaflet/dist/leaflet.css";
import { useUploadCat } from "../composables/useUploadCat";
import { authStore, isUserReady, getAuthHeader } from "../store/auth";
import { catDetectionService } from "../services/catDetectionService";

const router = useRouter();

// No authentication check on mount - allow access to upload page
onMounted(() => {
  // Initialize any necessary data
});

const locationName = ref("");
const description = ref("");
const latitude = ref("18.7883");
const longitude = ref("98.9853");
const file = ref(null);
const previewUrl = ref(null);
const fileInput = ref(null);
const uploadSuccess = ref(false);
const gettingLocation = ref(false);
const locationSuccess = ref(false);
const classificationLabel = ref(null);
const classificationConfidence = ref(null);
const isDetectingCats = ref(false);
const catDetectionResult = ref(null);
const showDetectionResults = ref(false);

// Use the upload composable
const { uploadCat, isUploading, error } = useUploadCat();

// Error handling for browser extension conflicts
onErrorCaptured((err) => {
  // Ignore extension-related errors
  if (err.message && err.message.includes("message channel closed")) {
    console.warn("Browser extension conflict detected, ignoring:", err.message);
    return false; // Prevent the error from propagating
  }
  return true; // Let other errors propagate normally
});

// Handle unhandled promise rejections (often from extensions)
onMounted(() => {
  window.addEventListener("unhandledrejection", (event) => {
    if (
      event.reason &&
      event.reason.message &&
      event.reason.message.includes("message channel closed")
    ) {
      console.warn("Prevented extension error:", event.reason.message);
      event.preventDefault();
    }
  });
});

// Map setup
const mapZoom = ref(13);
const mapCenter = ref([18.7883, 98.9853]); // Default: Chiang Mai
const markerLatLng = ref([18.7883, 98.9853]);
const tileLayerUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const tileLayerAttr =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

// Sync marker <-> input
watch([latitude, longitude], ([lat, lng]) => {
  if (lat && lng) {
    markerLatLng.value = [parseFloat(lat), parseFloat(lng)];
    mapCenter.value = [parseFloat(lat), parseFloat(lng)];
  }
});

function onMarkerDrag(newLatLng) {
  // Handle different possible data structures from Vue-Leaflet
  let lat, lng;

  if (Array.isArray(newLatLng)) {
    // Array format [lat, lng]
    lat = newLatLng[0];
    lng = newLatLng[1];
  } else if (newLatLng && typeof newLatLng === "object") {
    // Object format with lat/lng properties
    lat = newLatLng.lat || newLatLng.latitude;
    lng = newLatLng.lng || newLatLng.longitude;
  } else {
    console.error("Unexpected newLatLng format:", newLatLng);
    return;
  }

  if (lat !== undefined && lng !== undefined) {
    markerLatLng.value = [lat, lng];
    latitude.value = lat.toFixed(6);
    longitude.value = lng.toFixed(6);
    locationSuccess.value = true;
    setTimeout(() => (locationSuccess.value = false), 2000);
  }
}

function onMapMove(newCenter) {
  mapCenter.value = newCenter;
}

function onMapClick(event) {
  // Handle different possible event structures
  let lat, lng;

  if (event && event.latlng) {
    lat = event.latlng.lat;
    lng = event.latlng.lng;
  } else if (event && event.lat !== undefined && event.lng !== undefined) {
    lat = event.lat;
    lng = event.lng;
  } else {
    console.error("Unexpected event format:", event);
    return;
  }

  if (lat !== undefined && lng !== undefined) {
    latitude.value = lat.toFixed(6);
    longitude.value = lng.toFixed(6);
    markerLatLng.value = [lat, lng];
    locationSuccess.value = true;
    setTimeout(() => (locationSuccess.value = false), 1000);
  }
}

function getCurrentLocation() {
  gettingLocation.value = true;
  error.value = null;
  locationSuccess.value = false;

  if (!navigator.geolocation) {
    error.value = "Geolocation is not supported by your browser.";
    gettingLocation.value = false;
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      latitude.value = lat.toFixed(6);
      longitude.value = lng.toFixed(6);
      markerLatLng.value = [lat, lng];
      mapCenter.value = [lat, lng];

      locationSuccess.value = true;
      gettingLocation.value = false;

      // Hide success message after 2 seconds
      setTimeout(() => (locationSuccess.value = false), 2000);
    },
    (err) => {
      switch (err.code) {
        case err.PERMISSION_DENIED:
          error.value = "Permission denied. Please allow location access.";
          break;
        case err.POSITION_UNAVAILABLE:
          error.value = "Location information is unavailable.";
          break;
        case err.TIMEOUT:
          error.value = "The request to get user location timed out.";
          break;
        default:
          error.value = "An unknown error occurred while getting location.";
          break;
      }
      gettingLocation.value = false;
    }
  );
}

function triggerFileInput() {
  fileInput.value.click();
}

function handleFileChange(e) {
  const selected = e.target.files[0];
  if (selected && selected.type.startsWith("image/")) {
    file.value = selected;
    previewUrl.value = URL.createObjectURL(selected);
    error.value = null;
    
    // ตรวจจับแมวในรูปภาพที่เลือก
    detectCatsInImage(selected);
  }
}

function handleDrop(e) {
  const dropped = e.dataTransfer.files[0];
  if (dropped && dropped.type.startsWith("image/")) {
    file.value = dropped;
    previewUrl.value = URL.createObjectURL(dropped);
    error.value = null;
    
    // ตรวจจับแมวในรูปภาพที่ drop
    detectCatsInImage(dropped);
  }
}

async function detectCatsInImage(imageFile) {
  if (!imageFile) return;
  
  isDetectingCats.value = true;
  catDetectionResult.value = null;
  showDetectionResults.value = false;
  error.value = null;
  
  try {
    console.log('🔍 Starting cat detection for:', imageFile.name);
    
    // ใช้ test endpoint ที่ไม่ต้อง authentication
    const result = await catDetectionService.testDetectCats(imageFile);
    
    catDetectionResult.value = result;
    showDetectionResults.value = true;
    
    console.log('✅ Cat detection result:', result);
    
    // ตรวจสอบว่ามีแมวในรูปหรือไม่
    if (!result.has_cats || result.cat_count === 0) {
      error.value = `❌ ไม่พบแมวในรูปภาพนี้! กรุณาอัพโหลดรูปภาพที่มีแมว (Confidence: ${result.confidence}%)`;
      file.value = null;
      previewUrl.value = null;
      showDetectionResults.value = false;
    } else {
      console.log(`✅ พบแมว ${result.cat_count} ตัว! (Confidence: ${result.confidence}%)`);
    }
    
  } catch (error) {
    console.error('❌ Cat detection failed:', error);
    
    // ถ้า detection ล้มเหลว ให้ใช้ fallback
    error.value = `⚠️ ไม่สามารถตรวจสอบแมวได้: ${error.message}. คุณยังสามารถอัพโหลดได้`;
    catDetectionResult.value = {
      has_cats: true, // สมมติว่ามีแมว
      cat_count: 1,
      confidence: 50,
      note: "ไม่สามารถตรวจสอบได้ - กรุณาตรวจสอบด้วยตนเอง"
    };
    showDetectionResults.value = true;
  } finally {
    isDetectingCats.value = false;
  }
}

async function handleSubmit() {
  // Check authentication first - redirect to login if not authenticated
  if (!authStore.isAuthenticated || !authStore.user) {
    sessionStorage.setItem('redirectAfterAuth', '/upload');
    router.push('/login');
    return;
  }

  // Validation for authenticated users
  if (!file.value) {
    error.value = "Please select a file to upload.";
    return;
  }
  
  // ตรวจสอบว่ามีการตรวจจับแมวแล้วหรือยัง
  if (!catDetectionResult.value) {
    error.value = "กรุณารอให้ระบบตรวจสอบแมวในรูปภาพเสร็จสิ้น";
    return;
  }
  
  // ตรวจสอบว่ามีแมวในรูปหรือไม่
  if (!catDetectionResult.value.has_cats || catDetectionResult.value.cat_count === 0) {
    error.value = "ไม่สามารถอัพโหลดได้ เนื่องจากไม่พบแมวในรูปภาพนี้ กรุณาเลือกรูปภาพที่มีแมว";
    return;
  }
  
  if (
    !latitude.value ||
    !longitude.value ||
    latitude.value === "" ||
    longitude.value === ""
  ) {
    error.value =
      "Please select a location on the map by clicking, dragging the marker, or using your current location.";
    return;
  }
  if (!locationName.value.trim()) {
    error.value = "Please enter a location name.";
    return;
  }

  isUploading.value = true;
  error.value = null;
  uploadSuccess.value = false;
  
  const formData = new FormData();
  formData.append("file", file.value);
  formData.append("lat", latitude.value);
  formData.append("lng", longitude.value);
  formData.append("description", description.value.trim() || "");
  formData.append("location_name", locationName.value.trim());
  
  // เพิ่มข้อมูลการตรวจจับแมว
  formData.append("cat_detection_data", JSON.stringify({
    has_cats: catDetectionResult.value.has_cats,
    cat_count: catDetectionResult.value.cat_count,
    confidence: catDetectionResult.value.confidence,
    suitable_for_cat_spot: catDetectionResult.value.suitable_for_cat_spot,
    cats_detected: catDetectionResult.value.cats_detected || [],
    detection_timestamp: new Date().toISOString()
  }));
  
  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/upload/cat`, {
      method: "POST",
      headers: {
      ...getAuthHeader()
      },
      body: formData
    });
    let data = null;
    const text = await res.text();
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      data = {};
    }
    if (res.ok) {
      uploadSuccess.value = true;
      if (data && Array.isArray(data.classification)) {
        const catLabel = data.classification.find(
          (item) => typeof item === "string" && item.toLowerCase().includes("cat")
        );
        if (catLabel) {
          classificationLabel.value = catLabel;
          classificationConfidence.value = null;
        } else {
          classificationLabel.value = "No cat detected in this image";
          classificationLabel.value = "No cat detected in this image";
          classificationConfidence.value = null;
        }
      }
      // Automatically refresh to the upload page after a short delay
      setTimeout(() => {
        window.location.reload();
      }, 500);
      // Automatically refresh to the upload page after a short delay
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } else {
      // Handle auth errors
      if (res.status === 401) {
        sessionStorage.setItem('redirectAfterAuth', '/upload');
        router.push('/login');
        return;
      }
      error.value = (data && data.detail) || "Upload failed.";
    }
  } catch (err) {
    error.value = "An error occurred while uploading the photo.";
    console.error("Upload error:", err);
  } finally {
    isUploading.value = false;
  }
}

function resetForm() {
  locationName.value = "";
  description.value = "";
  latitude.value = "18.7883";
  longitude.value = "98.9853";
  file.value = null;
  previewUrl.value = null;
  uploadSuccess.value = false;
  gettingLocation.value = false;
  locationSuccess.value = false;
  classificationLabel.value = null;
  classificationConfidence.value = null;
}
</script>