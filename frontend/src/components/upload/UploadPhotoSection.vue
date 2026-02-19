<template>
  <div class="space-y-6">
    <div class="flex items-baseline justify-between border-b border-stone-200 pb-4">
      <h2 class="text-2xl font-heading font-bold text-brown flex items-center">
        {{ t('upload.photoSection.title') }}
        <svg
          v-if="!isAuthenticated"
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5 ml-2 text-stone-500"
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
      <span class="text-sm font-medium text-stone-500 uppercase tracking-widest">{{
        t('upload.photoSection.required')
      }}</span>
    </div>

    <div
      class="group relative border-2 border-dashed rounded-2xl p-8 transition-all duration-300 min-h-[300px] flex flex-col items-center justify-center text-center cursor-pointer overflow-hidden bg-white/40 hover:bg-white/60"
      :class="[
        previewUrl
          ? 'border-sage-dark/50 bg-white/60'
          : 'border-stone-300 hover:border-terracotta/50',
        isDetectingCats ? 'cursor-wait opacity-80' : '',
        !isAuthenticated ? 'opacity-75' : '',
        isQuotaFull ? 'cursor-not-allowed opacity-75 grayscale' : '',
      ]"
      @dragover.prevent
      @drop.prevent="!isQuotaFull && handleDrop($event)"
      @click="!isQuotaFull && handleFrameClick()"
    >
      <label for="file-upload" class="sr-only">{{ t('upload.photoSection.uploadPhoto') }}</label>
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
          {{ t('upload.photoSection.verifiedCatPhoto') }}
        </div>

        <!-- Click to change hint -->
        <div
          v-if="catDetectionResult?.has_cats && !isDetectingCats"
          class="absolute top-4 right-4 bg-white/80 text-stone-500 px-3 py-1.5 rounded-lg text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        >
          {{ t('upload.photoSection.clickToChange') }}
        </div>
      </div>

      <!-- Quota Full State -->
      <div v-else-if="isQuotaFull" class="space-y-4">
        <div
          class="w-16 h-16 bg-red-50 rounded-full mx-auto flex items-center justify-center text-red-500 mb-4"
        >
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <div>
          <p class="text-xl font-heading font-medium text-red-600 mb-1">Quota Limit Reached</p>
          <p class="text-stone-500 text-sm">
            Please wait for your rolling window to reset or upgrade to Pro.
          </p>
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
            {{ t('upload.photoSection.dragAndDrop') }}
          </p>
          <p class="text-stone-500 text-sm">{{ t('upload.photoSection.orClickToBrowse') }}</p>
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
          {{ t('upload.photoSection.verifyingCatContent') }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { showError } from '@/store/toast';
import { validateImageFile } from '@/utils/imageUtils';

const { t } = useI18n();

const props = defineProps<{
  previewUrl: string | null;
  isDetectingCats: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  catDetectionResult: any;
  isAuthenticated: boolean;
  isQuotaFull?: boolean;
}>();

const emit = defineEmits<{
  'file-selected': [payload: { file: File; url: string }];
  'check-auth': [];
}>();

const fileInput = ref<HTMLInputElement | null>(null);

watch(
  () => props.previewUrl,
  (newVal) => {
    if (!newVal && fileInput.value) {
      fileInput.value.value = '';
    }
  }
);

function triggerFileInput(): void {
  if (!checkAuthProps()) return;
  fileInput.value?.click();
}

function checkAuthProps(): boolean {
  if (!props.isAuthenticated) {
    emit('check-auth');
    return false;
  }
  return true;
}

function handleFrameClick(): void {
  if (props.isDetectingCats) return; // Don't allow click while detecting

  // Allow click to change photo if verified cat, or if no preview yet
  if (!props.previewUrl || props.catDetectionResult?.has_cats) {
    triggerFileInput();
  }
}

function handleFileChange(e: Event): void {
  const target = e.target as HTMLInputElement;
  const selected = target.files?.[0];
  if (selected) processFile(selected);
}

function handleDrop(e: DragEvent): void {
  if (!checkAuthProps()) return;
  const dropped = e.dataTransfer?.files[0];
  if (dropped) processFile(dropped);
}

const processFile = (imageFile: File): void => {
  // Validate file using shared utility (type and size)
  const validation = validateImageFile(imageFile);
  if (!validation.valid) {
    showError(validation.error || t('upload.invalidImage'), 'Upload Error');
    return;
  }

  // Create temp object URL for validation
  const tempUrl = URL.createObjectURL(imageFile);
  const img = new Image();
  img.onload = (): void => {
    const ratio = img.width / img.height;
    // Allow some flexibility but reject extreme panoramas or skyscrapers
    // Standard 4:3 is 1.33, 1:1 is 1.0. 16:9 is 1.77.
    // We want to avoid thin strips.
    if (ratio < 0.5 || ratio > 2.0) {
      showError(
        t('upload.photoSection.aspectRatioMessage'),
        t('upload.photoSection.invalidAspectRatio')
      );
      URL.revokeObjectURL(tempUrl);
      return;
    }

    // If valid, emit
    emit('file-selected', { file: imageFile, url: tempUrl });
  };
  img.onerror = (): void => {
    showError(t('upload.invalidImage'), 'Load Error');
    URL.revokeObjectURL(tempUrl);
  };
  img.src = tempUrl;
};
</script>

<style scoped>
/* Scoped styles */
</style>
