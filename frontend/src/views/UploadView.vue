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
        <UploadSuccess
          v-else-if="uploadSuccess"
          @upload-another="globalThis.location.reload()"
          @view-map="router.push('/map')"
        />

        <!-- Upload Form -->
        <form v-else class="p-6 md:p-10 space-y-12" @submit.prevent="handleSubmit">
          <!-- Section 1: Photo -->
          <UploadPhotoSection
            :preview-url="previewUrl"
            :is-detecting-cats="isDetectingCats"
            :cat-detection-result="catDetectionResult"
            :is-authenticated="true"
            @file-selected="handleFileSelected"
            @check-auth="handleCheckAuth"
          />

          <!-- Section 2: Details -->
          <UploadDetailsSection
            v-model:location-name="locationName"
            v-model:description="description"
            v-model:tags="tags"
            :is-authenticated="true"
          />

          <!-- Section 3: Location -->
          <UploadLocationSection
            map-id="uploadMap"
            :is-authenticated="true"
            :getting-location="gettingLocation"
            :has-selected-location="hasSelectedLocation"
            @get-location="handleGetLocation"
            @check-auth="handleCheckAuth"
          />

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
import { showError } from '../store/toast';
import { catDetectionService } from '../services/catDetectionService';
import { isDev, getEnvVar } from '../utils/env';
import GhibliBackground from '../components/ui/GhibliBackground.vue';
import GhibliLoader from '../components/ui/GhibliLoader.vue';
import LoginRequiredModal from '../components/ui/LoginRequiredModal.vue';
import UploadSuccess from '@/components/upload/UploadSuccess.vue';
import UploadPhotoSection from '@/components/upload/UploadPhotoSection.vue';
import UploadDetailsSection from '@/components/upload/UploadDetailsSection.vue';
import UploadLocationSection from '@/components/upload/UploadLocationSection.vue';
import { useSeo } from '../composables/useSeo';

const router = useRouter();
const authStore = useAuthStore();
const { setMetaTags, resetMetaTags } = useSeo();

const locationName = ref('');
const description = ref('');
const tags = ref<string[]>([]);
const file = ref<File | null>(null);
const previewUrl = ref<string | null>(null);
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
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  cleanupLocationPicker();
  resetMetaTags(); // Reset SEO meta tags
});

const checkAuth = (): boolean => {
  if (!isAuthenticated.value) {
    showLoginModal.value = true;
    return false;
  }
  return true;
};

const handleCheckAuth = (): void => {
  checkAuth();
};

const handleLoginRedirect = (): void => {
  sessionStorage.setItem('redirectAfterAuth', '/upload');
  router.push('/login');
};

const handleAuthProtection = (e: Event): void => {
  // Auth check removed to allow form interaction
};

const handleGetLocation = (): void => {
  getCurrentLocation();
};

const resetImageSelection = (): void => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  file.value = null;
  previewUrl.value = null;
  catDetectionResult.value = null;
};

// Handle file selection from component
function handleFileSelected(payload: { file: File; url: string }): void {
  // Cleanup old if exists
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);

  file.value = payload.file;
  previewUrl.value = payload.url;

  detectCatsInImage(payload.file);
}

async function detectCatsInImage(imageFile: File): Promise<void> {
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

async function handleSubmit(): Promise<void> {
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
