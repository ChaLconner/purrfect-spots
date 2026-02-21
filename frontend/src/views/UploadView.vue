<template>
  <div class="min-h-screen pt-12 pb-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
    <GhibliBackground />

    <div class="max-w-4xl mx-auto relative z-10">
      <!-- Header -->
      <div class="text-center mb-12">
        <h1 class="text-4xl md:text-5xl font-heading font-bold text-brown mb-4 tracking-tight">
          {{ t('upload.pageTitle') }}
        </h1>
        <p class="text-lg text-brown-light font-body max-w-2xl mx-auto leading-relaxed mb-6">
          {{ t('upload.pageSubtitle') }}
        </p>

        <!-- Quota Status -->
        <div v-if="isAuthenticated && quotaStatus" class="flex flex-col items-center gap-1.5 mb-2">
          <div
            class="group inline-flex items-center px-4 py-2 rounded-full bg-white/60 backdrop-blur-sm border border-brown/10 text-sm font-body text-brown-light shadow-sm hover:bg-white/80 transition-all"
            :title="t('upload.rollingNotice')"
          >
            <div class="flex items-center">
              <span class="mr-2 opacity-70">{{ t('upload.dailyQuota') }}</span>
              <span
                class="font-bold flex items-center"
                :class="quotaStatus.remaining === 0 ? 'text-red-500' : 'text-terracotta'"
              >
                <span class="text-xs mr-1 opacity-50 font-normal">{{ t('upload.used') }}:</span>
                {{ quotaStatus.used }} / {{ quotaStatus.limit }}
              </span>
            </div>
            <span
              v-if="!quotaStatus.is_pro"
              class="ml-3 pl-3 border-l border-brown/20 flex items-center"
            >
              <router-link
                to="/subscription"
                class="text-terracotta hover:text-terracotta-dark font-bold flex items-center gap-1"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-terracotta animate-pulse"></span>
                {{ t('upload.upgradeToPro') }}
              </router-link>
            </span>
          </div>
          <span
            class="text-[10px] text-brown/40 font-body uppercase tracking-widest flex items-center gap-1"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="w-3 h-3"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
              <path d="m12 7 0 5 3 2" />
            </svg>
            {{ t('upload.rollingNotice') }}
          </span>
        </div>
      </div>

      <!-- Main Content Card -->
      <div
        class="bg-white/80 backdrop-blur-md rounded-3xl shadow-xl overflow-hidden border border-white/50 relative"
      >
        <!-- Progress Bar -->
        <div v-if="currentStep < 4" class="h-2 bg-stone-100 w-full">
          <div
            class="h-full bg-gradient-to-r from-sage to-terracotta transition-all duration-500 ease-out"
            :style="{ width: `${(currentStep / 3) * 100}%` }"
          ></div>
        </div>

        <div class="p-6 sm:p-10">
          <ErrorBoundary>
            <!-- Step 1: Photo Upload -->
            <transition
              enter-active-class="transition-opacity duration-300 ease"
              enter-from-class="opacity-0"
              leave-active-class="transition-opacity duration-300 ease"
              leave-to-class="opacity-0"
              mode="out-in"
            >
              <div v-if="currentStep === 1">
                <UploadPhotoSection
                  :preview-url="uploadData.previewUrl"
                  :is-detecting-cats="isDetectingCats"
                  :cat-detection-result="uploadData.catDetectionResult"
                  :is-authenticated="isAuthenticated"
                  :is-quota-full="!canUpload"
                  @file-selected="handleFileSelected"
                  @check-auth="handleCheckAuth"
                />

                <div
                  v-if="uploadData.catDetectionResult?.has_cats && !isDetectingCats"
                  class="mt-8 flex justify-end fade-enter-active"
                >
                  <button
                    class="px-6 py-2 bg-terracotta text-white font-bold rounded-xl shadow-md hover:bg-terracotta-dark transition-all transform hover:-translate-y-0.5"
                    @click="currentStep = 2"
                  >
                    {{ t('common.next') }}
                  </button>
                </div>
              </div>
            </transition>

            <!-- Step 2: Details -->
            <transition
              enter-active-class="transition-opacity duration-300 ease"
              enter-from-class="opacity-0"
              leave-active-class="transition-opacity duration-300 ease"
              leave-to-class="opacity-0"
              mode="out-in"
            >
              <div v-if="currentStep === 2">
                <UploadDetailsSection
                  v-model:location-name="uploadData.locationName"
                  v-model:description="uploadData.description"
                  v-model:tags="uploadData.tags"
                  :is-authenticated="isAuthenticated"
                  @focus-auth="handleCheckAuth"
                />

                <div class="mt-8 flex justify-between">
                  <button
                    class="px-6 py-2 text-stone-500 hover:text-brown font-medium transition-colors"
                    @click="currentStep = 1"
                  >
                    {{ t('common.back') }}
                  </button>
                  <button
                    class="px-6 py-2 bg-terracotta text-white font-bold rounded-xl shadow-md hover:bg-terracotta-dark transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="!isStep2Valid"
                    @click="currentStep = 3"
                  >
                    {{ t('common.next') }}
                  </button>
                </div>
              </div>
            </transition>

            <!-- Step 3: Location -->
            <transition
              enter-active-class="transition-opacity duration-300 ease"
              enter-from-class="opacity-0"
              leave-active-class="transition-opacity duration-300 ease"
              leave-to-class="opacity-0"
              mode="out-in"
            >
              <div v-if="currentStep === 3">
                <UploadLocationSection
                  :is-authenticated="isAuthenticated"
                  :getting-location="gettingLocation"
                  :has-selected-location="!!uploadData.latitude"
                  @get-location="getCurrentLocation"
                  @check-auth="handleCheckAuth"
                />

                <div class="mt-8 flex justify-between">
                  <button
                    class="px-6 py-2 text-stone-500 hover:text-brown font-medium transition-colors"
                    @click="currentStep = 2"
                  >
                    {{ t('common.back') }}
                  </button>
                  <button
                    class="px-6 py-2 bg-terracotta text-white font-bold rounded-xl shadow-md hover:bg-terracotta-dark transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="!isStep3Valid || isSubmitting"
                    @click="submitUpload"
                  >
                    <span v-if="isSubmitting">{{ t('common.uploading') }}...</span>
                    <span v-else>{{ t('common.upload') }}</span>
                  </button>
                </div>

                <!-- Upload Progress Bar -->
                <div v-if="isSubmitting && uploadProgress > 0" class="mt-4">
                  <div class="flex items-center justify-between text-sm text-brown-light mb-1">
                    <span>{{ t('upload.uploadingProgress') }}</span>
                    <span class="font-bold text-terracotta">{{ uploadProgress }}%</span>
                  </div>
                  <div class="h-2.5 bg-stone-100 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-gradient-to-r from-sage to-terracotta rounded-full transition-all duration-300 ease-out"
                      :style="{ width: `${uploadProgress}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </transition>

            <!-- Step 4: Success -->
            <transition
              enter-active-class="transition-opacity duration-300 ease"
              enter-from-class="opacity-0"
              leave-active-class="transition-opacity duration-300 ease"
              leave-to-class="opacity-0"
              mode="out-in"
            >
              <UploadSuccess
                v-if="currentStep === 4"
                :result="uploadResult"
                @upload-another="resetForm"
                @view-map="router.push('/map')"
              />
            </transition>
          </ErrorBoundary>
        </div>
      </div>
    </div>

    <LoginRequiredModal
      :is-open="showLoginModal"
      @close="showLoginModal = false"
      @login="handleLoginParams"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/store/authStore';
import { showError, showSuccess } from '@/store/toast';
import { catDetectionService as CatDetectionService } from '@/services/catDetectionService';
import { loadGoogleMaps } from '@/utils/googleMapsLoader';
import { getEnvVar } from '@/utils/env';
import { useUploadCat } from '@/composables/useUploadCat';

// Components
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue';
import LoginRequiredModal from '@/components/ui/LoginRequiredModal.vue';
import UploadPhotoSection from '@/components/upload/UploadPhotoSection.vue';
import UploadDetailsSection from '@/components/upload/UploadDetailsSection.vue';
import UploadLocationSection from '@/components/upload/UploadLocationSection.vue';
import UploadSuccess from '@/components/upload/UploadSuccess.vue';

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();
const isAuthenticated = computed(() => authStore.isAuthenticated);

// State
const currentStep = ref(1);
const isDetectingCats = ref(false);
const isSubmitting = ref(false);
const showLoginModal = ref(false);
const gettingLocation = ref(false);
const map = ref<google.maps.Map | null>(null);
const marker = ref<google.maps.Marker | null>(null);

const uploadResult = ref<unknown>(null);

// Placeholder for quota - ideally fetched from API
const quotaStatus = ref<{
  used: number;
  limit: number;
  remaining: number;
  is_pro: boolean;
} | null>(null);

// Fetch real quota from API
const refreshQuota = async () => {
  if (isAuthenticated.value) {
    try {
      const quota = await getUploadQuota();
      if (quota) {
        quotaStatus.value = quota;
      }
    } catch (err) {
      console.warn('Could not fetch upload quota:', err);
    }
  }
};

onMounted(refreshQuota);

// Prevent selecting file if quota is full
const canUpload = computed(() => {
  if (!quotaStatus.value) return true;
  return quotaStatus.value.remaining > 0;
});

const uploadData = ref({
  file: null as File | null,
  previewUrl: null as string | null,
  catDetectionResult: null as unknown,
  locationName: '',
  description: '',
  tags: [] as string[],
  latitude: null as number | null,
  longitude: null as number | null,
});

// Computed Validation
const isStep2Valid = computed(() => {
  return uploadData.value.locationName.trim().length > 0;
});

const isStep3Valid = computed(() => {
  return uploadData.value.latitude !== null && uploadData.value.longitude !== null;
});

// Handlers
const handleCheckAuth = () => {
  if (!isAuthenticated.value) {
    showLoginModal.value = true;
  }
};

const handleLoginParams = () => {
  router.push({ path: '/login', query: { redirect: '/upload' } });
};

const handleFileSelected = async ({ file, url }: { file: File; url: string }) => {
  uploadData.value.file = file;
  uploadData.value.previewUrl = url;

  // Detect cats
  isDetectingCats.value = true;
  try {
    // Simulate or call real service
    const result = await CatDetectionService.detectCats(file);
    uploadData.value.catDetectionResult = result;

    if (result.has_cats) {
      setTimeout(() => {
        currentStep.value = 2;
      }, 1000);
    } else {
      showError(t('upload.noCatsDetected'), 'Detection Failed');
      if (uploadData.value.previewUrl) URL.revokeObjectURL(uploadData.value.previewUrl);
      uploadData.value.previewUrl = null;
      uploadData.value.file = null;
      uploadData.value.catDetectionResult = null;
    }
  } catch (error) {
    console.error(error);
    showError(t('upload.errorVerifyCat'), t('common.error'));
    if (uploadData.value.previewUrl) URL.revokeObjectURL(uploadData.value.previewUrl);
    uploadData.value.previewUrl = null;
    uploadData.value.file = null;
    uploadData.value.catDetectionResult = null;
  } finally {
    isDetectingCats.value = false;
  }
};

// Map Logic
watch(currentStep, (step) => {
  if (step === 3) {
    nextTick(() => initMap());
  }
});

const initMap = async () => {
  try {
    await loadGoogleMaps({ apiKey: getEnvVar('VITE_GOOGLE_MAPS_API_KEY') });

    const mapEl = document.getElementById('uploadMap');
    if (!mapEl) return;

    const defaultCenter = { lat: 13.7563, lng: 100.5018 }; // Bangkok default

    map.value = new google.maps.Map(mapEl, {
      center: defaultCenter,
      zoom: 12,
      disableDefaultUI: true,
      clickableIcons: false,
    });

    map.value.addListener('click', (e: google.maps.MapMouseEvent) => {
      if (e.latLng) {
        updateLocation(e.latLng.lat(), e.latLng.lng());
      }
    });
  } catch {
    showError(t('upload.errorMapLoad'), t('common.error'));
  }
};

const updateLocation = (lat: number, lng: number) => {
  uploadData.value.latitude = lat;
  uploadData.value.longitude = lng;

  if (marker.value) {
    marker.value.setPosition({ lat, lng });
  } else if (map.value) {
    marker.value = new google.maps.Marker({
      position: { lat, lng },
      map: map.value,
      animation: google.maps.Animation.DROP,
    });
  }
};

const getCurrentLocation = () => {
  if (!navigator.geolocation) {
    showError(t('upload.errorGeolocation'), t('common.error'));
    return;
  }

  gettingLocation.value = true;
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude } = pos.coords;
      updateLocation(latitude, longitude);
      if (map.value) {
        map.value.panTo({ lat: latitude, lng: longitude });
        map.value.setZoom(15);
      }
      gettingLocation.value = false;
    },
    (err) => {
      showError(err.message, 'Location Error');
      gettingLocation.value = false;
    }
  );
};

// Use Composable
const { uploadCatPhoto, isUploading, uploadProgress, getUploadQuota, error } = useUploadCat();

// Sync loading state for template compatibility
watch(isUploading, (val) => {
  isSubmitting.value = val;
});

const submitUpload = async () => {
  if (!uploadData.value.file) return;

  if (!uploadData.value.latitude || !uploadData.value.longitude) {
    showError(t('upload.locationRequired'), 'Validation Error');
    return;
  }

  try {
    const locationData = {
      lat: uploadData.value.latitude.toString(),
      lng: uploadData.value.longitude.toString(),
      location_name: uploadData.value.locationName,
      description: uploadData.value.description,
      tags: uploadData.value.tags,
    };

    const result = await uploadCatPhoto(
      uploadData.value.file,
      locationData,
      uploadData.value.catDetectionResult
    );

    if (result) {
      uploadResult.value = result;
      currentStep.value = 4;
      showSuccess(t('upload.successMessage'));
      refreshQuota(); // Refresh quota after success
    } else {
      // Use the specific error message from the composable if available
      showError(error.value || t('upload.uploadFailed'), t('common.error'));
    }
  } catch (err) {
    showError(t('upload.unexpectedError'), t('common.error'));
    console.error(err);
  }
};

const resetForm = () => {
  uploadData.value = {
    file: null,
    previewUrl: null,
    catDetectionResult: null,
    locationName: '',
    description: '',
    tags: [],
    latitude: null,
    longitude: null,
  };
  currentStep.value = 1;
};
</script>
