<template>
  <div class="min-h-screen pt-12 pb-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
    <GhibliBackground />

    <div class="max-w-4xl mx-auto relative z-10">
      <!-- Header -->
      <div class="text-center mb-12">
        <h1 class="text-4xl md:text-5xl font-heading font-bold text-brown mb-4 tracking-tight">
          Share a Spot
        </h1>
        <p class="text-lg text-brown-light font-body max-w-2xl mx-auto leading-relaxed">
          Found a cozy corner where cats gather? Share it with the community and help others
          discover these purrfect places.
        </p>
      </div>

      <!-- Main Upload Card -->
      <div
        class="bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-white/50 overflow-hidden transition-all duration-500"
      >
        <!-- Loading / Progress State -->
        <div
          v-if="isUploading"
          class="p-16 text-center flex flex-col items-center justify-center min-h-[400px]"
        >
          <GhibliLoader text="Uploading..." class="mb-6" />
          <p class="text-brown-light mb-8">Saving your discovery to the map</p>
          <div class="w-full max-w-md h-2 bg-stone-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-terracotta transition-all duration-300 ease-out"
              :style="{ width: `${uploadProgress}%` }"
            ></div>
          </div>
        </div>

        <!-- Success State -->
        <div
          v-else-if="uploadSuccess"
          class="p-16 text-center flex flex-col items-center justify-center min-h-[400px]"
        >
          <div
            class="w-20 h-20 bg-sage/20 rounded-full flex items-center justify-center mb-6 text-sage-dark"
          >
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h3 class="text-3xl font-heading font-bold text-brown mb-4">Spot Added!</h3>
          <p class="text-brown-light mb-10 text-lg">Thank you for contributing to the map.</p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center w-full max-w-md">
            <button
              class="px-8 py-3 bg-white border-2 border-terracotta text-terracotta font-heading font-bold rounded-xl hover:bg-terracotta hover:text-white transition-all duration-300 transform hover:-translate-y-1"
              @click="globalThis.location.reload()"
            >
              Upload Another
            </button>
            <button
              class="px-8 py-3 font-heading font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
              style="background-color: #c97b49; color: white"
              @click="router.push('/map')"
            >
              View Map
            </button>
          </div>
        </div>

        <!-- Upload Form -->
        <form v-else class="p-6 md:p-10 space-y-12" @submit.prevent="handleSubmit">
          <!-- Section 1: Photo -->
          <div class="space-y-6">
            <div class="flex items-baseline justify-between border-b border-stone-200 pb-4">
              <h2 class="text-2xl font-heading font-bold text-brown flex items-center">
                01. The Photo
                <svg
                  v-if="!isAuthenticated"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 ml-2 text-stone-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  title="Login required"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </h2>
              <span class="text-sm font-medium text-stone-400 uppercase tracking-widest">Required</span>
            </div>

            <div
              class="group relative border-2 border-dashed rounded-2xl p-8 transition-all duration-300 min-h-[300px] flex flex-col items-center justify-center text-center cursor-pointer overflow-hidden bg-white/40 hover:bg-white/60"
              :class="[
                previewUrl
                  ? 'border-sage-dark/50 bg-white/60'
                  : 'border-stone-300 hover:border-terracotta/50',
                isDetectingCats ? 'cursor-wait opacity-80' : '',
                !isAuthenticated ? 'opacity-75' : '',
              ]"
              @dragover.prevent
              @drop.prevent="handleDrop"
              @click="handleFrameClick"
            >
              <label for="file-upload" class="sr-only">Upload Photo</label>
              <input
                id="file-upload"
                ref="fileInput"
                type="file"
                accept="image/*"
                class="hidden"
                @change="handleFileChange"
              />

              <!-- Preview State -->
              <div v-if="previewUrl" class="w-full h-full absolute inset-0 z-10 bg-stone-50">
                <img :src="previewUrl" class="w-full h-full object-contain" alt="Preview" />

                <!-- Verification Badge -->
                <div
                  v-if="catDetectionResult?.has_cats"
                  class="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-sage-dark text-white px-4 py-1.5 rounded-full text-sm font-bold shadow-lg flex items-center animate-fade-in-up"
                >
                  Verified Cat Photo
                </div>

                <!-- Click to change hint -->
                <div
                  v-if="catDetectionResult?.has_cats && !isDetectingCats"
                  class="absolute top-4 right-4 bg-white/80 text-stone-500 px-3 py-1.5 rounded-lg text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                >
                  Click to change
                </div>
              </div>

              <!-- Empty State -->
              <div v-else class="space-y-4 pointer-events-none">
                <div
                  class="w-20 h-20 bg-stone-100 rounded-full mx-auto flex items-center justify-center text-stone-300 mb-4 group-hover:scale-110 transition-transform duration-500"
                >
                  <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <div>
                  <p class="text-xl font-heading font-medium text-brown mb-1">
                    Drag and drop photo
                  </p>
                  <p class="text-stone-500 text-sm">or click to browse from your device</p>
                </div>
              </div>

              <!-- Detecting State Overlay -->
              <div
                v-if="isDetectingCats"
                class="absolute inset-0 z-20 bg-white/90 flex flex-col items-center justify-center"
              >
                <div
                  class="w-10 h-10 border-2 border-terracotta border-t-transparent rounded-full animate-spin mb-3"
                ></div>
                <p class="text-terracotta font-medium tracking-wide text-sm uppercase">
                  Verifying Cat Content...
                </p>
              </div>
            </div>
          </div>

          <!-- Section 2: Details -->
          <div class="space-y-6">
            <div class="flex items-baseline justify-between border-b border-stone-200 pb-4">
              <h2 class="text-2xl font-heading font-bold text-brown flex items-center">
                02. Details
                <svg
                  v-if="!isAuthenticated"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 ml-2 text-stone-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  title="Login required"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </h2>
              <span class="text-sm font-medium text-stone-400 uppercase tracking-widest">Info</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div class="space-y-2">
                <label
                  for="place-name"
                  class="block text-xs font-bold text-brown-light uppercase tracking-wider pl-1"
                >Name of Place</label>
                <input
                  id="place-name"
                  v-model="locationName"
                  type="text"
                  placeholder="e.g. Sunny Window Bench"
                  class="w-full px-4 py-3 bg-white/70 border-2 border-stone-200 rounded-xl focus:outline-none focus:border-terracotta focus:ring-4 focus:ring-terracotta/10 transition-all font-medium text-brown placeholder-stone-400"
                  required
                  @focus="handleAuthProtection"
                />
              </div>

              <div class="space-y-2">
                <label
                  for="place-description"
                  class="block text-xs font-bold text-brown-light uppercase tracking-wider pl-1"
                >Description</label>
                <textarea
                  id="place-description"
                  v-model="description"
                  rows="1"
                  placeholder="What makes this spot special?"
                  class="w-full px-4 py-3 bg-white/70 border-2 border-stone-200 rounded-xl focus:outline-none focus:border-terracotta focus:ring-4 focus:ring-terracotta/10 transition-all font-medium text-brown placeholder-stone-400 min-h-[52px]"
                  @focus="handleAuthProtection"
                ></textarea>
              </div>

              <div class="space-y-2 md:col-span-2">
                <label
                  for="tags-input"
                  class="block text-xs font-bold text-brown-light uppercase tracking-wider pl-1"
                >Tags (Optional)</label>
                <TagsInput
                  id="tags-input"
                  v-model="tags"
                  placeholder="Add tag (press Enter)"
                  :max-tags="20"
                  :max-tag-length="50"
                  :disabled="!isAuthenticated"
                  @focus="handleAuthProtection"
                />
              </div>
            </div>
          </div>

          <!-- Section 3: Location -->
          <div class="space-y-6">
            <div class="flex items-baseline justify-between border-b border-stone-200 pb-4">
              <h2 class="text-2xl font-heading font-bold text-brown flex items-center">
                03. Location
                <svg
                  v-if="!isAuthenticated"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 ml-2 text-stone-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  title="Login required"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </h2>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  :disabled="gettingLocation"
                  class="text-xs font-bold uppercase tracking-wider text-terracotta hover:text-terracotta-dark transition-colors disabled:opacity-50 cursor-pointer"
                  @click="handleGetLocation"
                >
                  {{ gettingLocation ? 'Locating...' : 'Use My Location' }}
                </button>
              </div>
            </div>

            <div
              class="relative rounded-2xl overflow-hidden border-2 border-white shadow-sm h-[300px] bg-stone-100 group"
            >
              <div
                id="uploadMap"
                class="w-full h-full opacity-90 transition-opacity duration-300"
              ></div>

              <!-- Login Overlay for Map -->
              <div
                v-if="!isAuthenticated"
                class="absolute inset-0 z-10 cursor-pointer bg-transparent"
                title="Login to use map"
                @click="checkAuth"
              ></div>

              <!-- Map Instruction Overlay -->
              <div
                class="absolute bottom-4 left-4 right-4 bg-white/80 backdrop-blur-sm p-3 rounded-lg text-xs text-brown text-center pointer-events-none border border-white/50 shadow-sm transition-all duration-300"
              >
                <span
                  v-if="!hasSelectedLocation"
                  class="flex items-center justify-center gap-2 animate-pulse"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  Tap or click on map to pin location
                </span>
                <span v-else> Drag marker to pinpoint exact location </span>
              </div>
            </div>
          </div>

          <!-- Submit Action -->
          <div class="pt-8">
            <button
              type="submit"
              :disabled="!canSubmit"
              class="w-full py-4 px-6 bg-gradient-to-r from-terracotta to-terracotta-dark text-white font-heading font-bold text-lg rounded-xl shadow-lg shadow-terracotta/30 hover:shadow-xl hover:shadow-terracotta/50 hover:scale-[1.02] hover:from-terracotta-dark hover:to-terracotta transition-all duration-300 disabled:bg-stone-300 disabled:bg-none disabled:text-stone-500 disabled:shadow-none disabled:cursor-not-allowed disabled:transform-none disabled:opacity-80"
            >
              Share This Spot
            </button>
          </div>
        </form>
      </div>
    </div>

    <LoginRequiredModal
      :is-open="showLoginModal"
      @close="showLoginModal = false"
      @login="handleLoginRedirect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useUploadCat } from '../composables/useUploadCat';
import { useLocationPicker } from '../composables/useLocationPicker';
import { useAuthStore } from '../store/authStore';
const authStore = useAuthStore();
import { showError } from '../store/toast';
import { catDetectionService } from '../services/catDetectionService';
import { isDev, getEnvVar } from '../utils/env';
import { DEFAULT_COORDINATES } from '../utils/constants';
import GhibliBackground from '../components/ui/GhibliBackground.vue';
import GhibliLoader from '../components/ui/GhibliLoader.vue';
import LoginRequiredModal from '../components/ui/LoginRequiredModal.vue';
import TagsInput from '../components/ui/TagsInput.vue';
import { useSeo } from '../composables/useSeo';

const router = useRouter();
const { setMetaTags, resetMetaTags } = useSeo();

const locationName = ref('');
const description = ref('');
const tags = ref<string[]>([]);
const file = ref<File | null>(null);
const previewUrl = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const uploadSuccess = ref(false);
const isDetectingCats = ref(false);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const catDetectionResult = ref<any>(null);
const showDetectionResults = ref(false);
const showLoginModal = ref(false);

const googleMapsApiKey = getEnvVar('VITE_GOOGLE_MAPS_API_KEY');

// Initialize Location Picker
const {
  latitude,
  longitude,
  gettingLocation,
  hasSelectedLocation,
  initializeMap,
  getCurrentLocation,
  cleanup: cleanupLocationPicker,
} = useLocationPicker({
  mapElementId: 'uploadMap',
});

const isAuthenticated = computed(() => authStore.isAuthenticated);
const canSubmit = computed(
  () =>
    isAuthenticated.value &&
    file.value &&
    !isDetectingCats.value &&
    catDetectionResult.value?.has_cats &&
    hasSelectedLocation.value
);

const { uploadCatPhoto, isUploading, error, uploadProgress } = useUploadCat();

onMounted(async () => {
  // Set SEO meta tags
  setMetaTags({
    title: 'Upload | Purrfect Spots',
    description: 'Share your cat photos and help others discover cat-friendly spots.',
    type: 'website',
  });

  if (!googleMapsApiKey) {
    showError('Map service is unavailable. Please contact support.');
    return;
  }
  await nextTick();
  setTimeout(() => {
    initializeMap();
    // Auto-detect location on load (silent mode)
    getCurrentLocation(true);
  }, 100);
});

// Cleanup on unmount
onUnmounted(() => {
  // Revoke object URL to prevent memory leak
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  cleanupLocationPicker();
  resetMetaTags(); // Reset SEO meta tags
});

const checkAuth = () => {
  if (!isAuthenticated.value) {
    showLoginModal.value = true;
    return false;
  }
  return true;
};

const handleLoginRedirect = () => {
  sessionStorage.setItem('redirectAfterAuth', '/upload');
  router.push('/login');
};

const handleAuthProtection = (e: Event) => {
  if (!checkAuth()) {
    (e.target as HTMLElement)?.blur?.();
  }
};

const handleGetLocation = () => {
  if (checkAuth()) {
    getCurrentLocation();
  }
};

function triggerFileInput() {
  if (!checkAuth()) return;
  fileInput.value?.click();
}

function handleFrameClick() {
  if (isDetectingCats.value) return; // Don't allow click while detecting

  // Allow click to change photo if verified cat, or if no preview yet
  if (!previewUrl.value || catDetectionResult.value?.has_cats) {
    triggerFileInput();
  }
}

const resetImageSelection = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  file.value = null;
  previewUrl.value = null;
  catDetectionResult.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const processFile = (imageFile: File) => {
  if (!imageFile || !imageFile.type.startsWith('image/')) return;

  // Revoke old URL to prevent memory leak
  resetImageSelection();

  file.value = imageFile;
  previewUrl.value = URL.createObjectURL(imageFile);
  detectCatsInImage(imageFile);
};

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  const selected = target.files?.[0];
  if (selected) processFile(selected);
}

function handleDrop(e: DragEvent) {
  if (!checkAuth()) return;
  const dropped = e.dataTransfer?.files[0];
  if (dropped) processFile(dropped);
}

async function detectCatsInImage(imageFile: File) {
  if (!imageFile) return;

  isDetectingCats.value = true;
  catDetectionResult.value = null;
  showDetectionResults.value = false;

  try {
    const result = await catDetectionService.detectCats(imageFile);

    if (!result || result.has_cats === undefined) {
      throw new Error('Invalid response from cat detection service');
    }

    catDetectionResult.value = result;
    showDetectionResults.value = true;

    const CONFIDENCE_THRESHOLD = 60;

    if (!result.has_cats || result.cat_count === 0) {
      showError('No cats detected. Please upload a real cat photo.', 'Invalid Image');
      resetImageSelection();
    } else if (result.confidence < CONFIDENCE_THRESHOLD) {
      showError('Cat detection weak. Ensure the cat is visible.', 'Low Confidence');
    } else {
      // showSuccess('Cat detected successfully!'); // Removed redundant toast
    }
  } catch (error) {
    if (isDev()) console.error('Cat detection error:', error);
    // SECURITY FIX: Reset selection on error - do NOT auto-approve
    showError(
      'Unable to verify image. Please try again with a different photo.',
      'Verification Failed'
    );
    resetImageSelection();
  } finally {
    isDetectingCats.value = false;
  }
}

async function handleSubmit() {
  if (!isAuthenticated.value || !authStore.user) {
    sessionStorage.setItem('redirectAfterAuth', '/upload');
    router.push('/login');
    return;
  }

  if (!file.value) {
    showError('Please select an image');
    return;
  }
  if (!catDetectionResult.value?.has_cats) {
    showError('Please wait for verification');
    return;
  }

  // Frontend validation - matches backend limits
  const trimmedName = locationName.value.trim();
  if (!trimmedName) {
    showError('Please enter a location name');
    return;
  }
  if (trimmedName.length < 3) {
    showError('Location name must be at least 3 characters');
    return;
  }
  if (trimmedName.length > 100) {
    showError('Location name must be under 100 characters');
    return;
  }

  const trimmedDescription = description.value.trim();
  if (trimmedDescription.length > 1000) {
    showError('Description is too long (max 1000 characters)');
    return;
  }

  const catDetectionData = {
    has_cats: catDetectionResult.value.has_cats,
    cat_count: catDetectionResult.value.cat_count,
    confidence: catDetectionResult.value.confidence,
    suitable_for_cat_spot: catDetectionResult.value.suitable_for_cat_spot,
    cats_detected: catDetectionResult.value.cats_detected || [],
    detection_timestamp: new Date().toISOString(),
    requires_server_verification: catDetectionResult.value.requires_server_verification || false,
  };

  const locationData = {
    lat: latitude.value,
    lng: longitude.value,
    description: trimmedDescription,
    location_name: trimmedName,
    tags: tags.value,
  };

  try {
    const data = await uploadCatPhoto(file.value, locationData, catDetectionData);
    if (data) {
      uploadSuccess.value = true;
    }
  } catch (err: unknown) {
    if (isDev()) console.error('Upload failed:', err);
    let msg = (err as Error).message || error.value || 'Upload failed. Please try again.';

    // Sanitize technical errors
    if (msg.includes('status code 413')) msg = 'Image is too large. Please choose a smaller file.';
    if (msg.includes('status code')) msg = 'Server error. Please try again later.';

    showError(msg);
  }
}
</script>

<style scoped>
/* Blob animations restored */

/* Custom scrollbar for better aesthetic in specific containers if needed */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(166, 93, 55, 0.2);
  border-radius: 10px;
}

/* Firefox compatibility */
* {
  scrollbar-width: thin;
  scrollbar-color: rgba(166, 93, 55, 0.2) transparent;
}
</style>
