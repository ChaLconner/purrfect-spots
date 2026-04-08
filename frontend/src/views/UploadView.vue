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

        <!-- Quota Status Detailed -->
        <div v-if="isAuthenticated" class="max-w-md mx-auto mb-8 bg-white/80 backdrop-blur-md p-5 rounded-2xl border border-white min-w-[300px] shadow-sm relative overflow-hidden group">
<template v-if="quotaStatus">
          <div v-if="quotaStatus.is_pro" class="absolute -top-6 -right-6 w-24 h-24 bg-gradient-to-br from-yellow-400 to-amber-600 rounded-full opacity-10 blur-xl group-hover:opacity-20 transition-opacity"></div>
          
          <div class="flex justify-between items-center mb-2 relative z-10">
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-bold text-brown">{{ t('upload.dailyQuota') }}</span>
                <span v-if="quotaStatus.is_pro" class="bg-gradient-to-r from-yellow-400 to-amber-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-sm uppercase tracking-wider shadow-sm">
                  PRO
                </span>
                <router-link v-else to="/subscription" class="text-[10px] font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full hover:bg-amber-100 transition-colors">
                  Upgrade
                </router-link>
                <span class="text-[10px] text-brown-light/60 font-medium ml-1">({{ t('upload.rollingNotice') }})</span>
              </div>
            </div>
            <div class="text-right">
              <span class="text-2xl font-black" :class="quotaStatus.remaining === 0 ? 'text-red-500' : 'text-brown'">
                {{ quotaStatus.used }}
              </span>
              <span class="text-sm font-semibold text-brown-light">/{{ quotaStatus.limit }}</span>
            </div>
          </div>

          <!-- Progress bar -->
          <div class="h-3 w-full bg-stone-100 rounded-full overflow-hidden relative z-10 shadow-inner">
            <div 
              class="h-full rounded-full transition-all duration-700 ease-out relative"
              :class="[
                quotaStatus.remaining === 0 ? 'bg-red-500' : 
                quotaStatus.is_pro ? 'bg-gradient-to-r from-yellow-400 to-amber-500' : 'bg-gradient-to-r from-sage to-terracotta'
              ]"
              :style="{ width: `${Math.min((quotaStatus.used / (quotaStatus.limit || 1)) * 100, 100)}%` }"
            >
              <!-- Shimmer effect -->
              <div class="absolute inset-0 bg-white/20 w-full h-full -skew-x-12 translate-x-[-100%] animate-[shimmer_2s_infinite]"></div>
            </div>
          </div>
          
          <div v-if="quotaStatus.remaining === 0" class="mt-3 text-xs font-bold text-red-500 text-center animate-pulse">
            {{ t('upload.quota.exceeded') }}
          </div>

          <div v-if="quotaStatus.resets_at" class="mt-3 text-[10px] text-brown-light/60 text-center flex flex-col gap-0.5 border-t border-brown/5 pt-2">
            <div>
              {{ t('upload.quota.resetsAt', { time: formatResetTime(quotaStatus.resets_at) }) }}
            </div>
            <div v-if="quotaStatus.reset_type === 'first_upload_window'" class="italic">
              {{ t('upload.quota.firstUploadWindow') }}
            </div>
          </div>
          </template>

          <!-- Skeleton Loader -->
          <template v-else>
            <div class="flex justify-between items-end mb-2">
              <div>
                <div class="h-5 w-24 bg-stone-200 rounded animate-pulse mb-1"></div>
                <div class="h-3 w-32 bg-stone-100 rounded animate-pulse"></div>
              </div>
              <div class="text-right">
                <div class="h-8 w-16 bg-stone-200 rounded animate-pulse"></div>
              </div>
            </div>
            <!-- Progress bar skeleton -->
            <div class="h-3 w-full bg-stone-100 rounded-full overflow-hidden relative shadow-inner">
               <div class="absolute inset-0 bg-stone-200 translate-x-[-100%] animate-[shimmer_1.5s_infinite]"></div>
            </div>
          </template>
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
import { useUploadCat } from '@/composables/useUploadCat';
import { useUploadMap } from '@/composables/useUploadMap';
import { format } from 'date-fns';
import { th, enUS } from 'date-fns/locale';

// Components
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue';
import LoginRequiredModal from '@/components/ui/LoginRequiredModal.vue';
import UploadPhotoSection from '@/components/upload/UploadPhotoSection.vue';
import UploadDetailsSection from '@/components/upload/UploadDetailsSection.vue';
import UploadLocationSection from '@/components/upload/UploadLocationSection.vue';
import UploadSuccess from '@/components/upload/UploadSuccess.vue';

// const { t } = useI18n(); // Removed duplicate
const router = useRouter();
const authStore = useAuthStore();
const { t, locale } = useI18n();
const isAuthenticated = computed(() => authStore.isAuthenticated);

// State
const currentStep = ref(1);
const isDetectingCats = ref(false);
const isSubmitting = ref(false);
const showLoginModal = ref(false);

const uploadResult = ref<unknown>(null);

// Placeholder for quota - ideally fetched from API
const quotaStatus = ref<{
  used: number;
  limit: number;
  remaining: number;
  is_pro: boolean;
  resets_at: string | null;
  reset_type: string | null;
} | null>(null);

// Fetch real quota from API
const refreshQuota = async (): Promise<void> => {
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

// Refresh quota when auth initializes (important for F5 refresh)
watch(
  () => authStore.isInitialized,
  (isInit) => {
    if (isInit) {
      refreshQuota();
    }
  }
);

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

const formatResetTime = (isoString: string): string => {
  if (!isoString) return '';
  try {
    const date = new Date(isoString);
    const dateLocale = locale.value === 'th' ? th : enUS;
    return format(date, 'd MMM, HH:mm', { locale: dateLocale });
  } catch {
    return isoString;
  }
};

// Computed Validation
const isStep2Valid = computed(() => {
  return uploadData.value.locationName.trim().length > 0;
});

const isStep3Valid = computed(() => {
  return uploadData.value.latitude !== null && uploadData.value.longitude !== null;
});

// Handlers
const handleCheckAuth = (): void => {
  if (!isAuthenticated.value) {
    showLoginModal.value = true;
  }
};

const handleLoginParams = (): void => {
  router.push({ path: '/login', query: { redirect: '/upload' } });
};

const handleFileSelected = async ({ file, url }: { file: File; url: string }): Promise<void> => {
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

// Use Composables
const { uploadCatPhoto, isUploading, uploadProgress, getUploadQuota, error } = useUploadCat();

const { gettingLocation, initMap, getCurrentLocation } = useUploadMap({
  onLocationUpdate: (lat, lng) => {
    uploadData.value.latitude = lat;
    uploadData.value.longitude = lng;
  },
});

// Sync loading state for template compatibility
// Sync Map watch
watch(currentStep, (step) => {
  if (step === 3) {
    nextTick(() => initMap());
  }
});

watch(isUploading, (val) => {
  isSubmitting.value = val;
});

const submitUpload = async (): Promise<void> => {
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

const resetForm = (): void => {
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
