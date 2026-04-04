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
          :title="t('auth.signInRequired')"
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
      @click="isQuotaFull ? handleQuotaFullClick() : handleFrameClick()"
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

        <!-- Click to change hint -->
        <div
          v-if="catDetectionResult?.has_cats && !isDetectingCats"
          class="absolute top-4 right-4 bg-white/80 backdrop-blur-sm text-brown px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300 border border-brown/5 flex items-center gap-2"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
          {{ t('upload.photoSection.clickToChange') }}
        </div>

        <!-- Cat Detected Info Overlay -->
        <div
          v-if="catDetectionResult?.has_cats && !isDetectingCats"
          class="absolute bottom-4 left-4 right-4 bg-white/90 backdrop-blur-md p-3 rounded-xl border border-sage/20 shadow-lg animate-fade-in-up"
        >
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-sage/20 rounded-lg flex items-center justify-center text-sage-dark shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="text-left">
              <p class="text-xs font-bold text-sage-dark uppercase tracking-wider mb-0.5">
                {{ t('upload.photoSection.catDetected') }}
              </p>
              <p class="text-xs text-brown font-medium">
                {{ t('upload.photoSection.foundCats', { count: catDetectionResult.cat_count }) }} • 
                {{ Math.round(catDetectionResult.confidence * 100) }}% {{ t('upload.photoSection.confidence') }}
              </p>
            </div>
          </div>
        </div>

        <!-- No Cat Detected State -->
        <div
          v-if="catDetectionResult && !catDetectionResult.has_cats && !isDetectingCats"
          class="absolute inset-0 bg-red-50/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center animate-fade-in"
        >
          <div class="w-14 h-14 bg-red-100 rounded-2xl flex items-center justify-center text-red-500 mb-4 shadow-sm">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h4 class="text-red-700 font-heading font-bold text-lg mb-2">
            {{ t('upload.photoSection.noCatDetected') }}
          </h4>
          <p class="text-red-600/80 text-sm mb-6 max-w-[240px] leading-relaxed">
            {{ t('upload.photoSection.noCatMessage') }}
          </p>
          <button
            class="px-5 py-2.5 bg-red-500 text-white font-bold rounded-xl shadow-md shadow-red-200 hover:bg-red-600 transition-all transform active:scale-95 flex items-center gap-2"
            @click="triggerFileInput"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {{ t('upload.photoSection.tryAnother') }}
          </button>
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
          <p class="text-xl font-heading font-medium text-red-600 mb-1">
            {{ t('upload.quota.exceeded') }}
          </p>
          <p class="text-stone-500 text-sm">
            {{ t('upload.quota.upgradePrompt') }}
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
import type { CatDetectionResult } from '@/types/upload';

const { t } = useI18n();

const props = defineProps<{
  previewUrl: string | null;
  isDetectingCats: boolean;
  catDetectionResult: CatDetectionResult | null;
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

function handleQuotaFullClick(): void {
  showError(t('upload.quota.exceeded'), t('upload.dailyQuota'));
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
