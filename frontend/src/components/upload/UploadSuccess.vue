<template>
  <div class="p-4 sm:p-10 text-center flex flex-col items-center justify-center min-h-[450px]">
    <!-- Success Icon with Animation -->
    <div
      class="w-20 h-20 sm:w-24 sm:h-24 bg-sage/10 rounded-full flex items-center justify-center mb-8 relative"
    >
      <div class="absolute inset-0 bg-sage/20 rounded-full animate-ping opacity-20"></div>
      <div
        class="w-16 h-16 sm:w-20 sm:h-20 bg-sage/20 rounded-full flex items-center justify-center text-sage-dark relative z-10"
      >
        <svg
          class="w-10 h-10 sm:w-12 sm:h-12 transform scale-0 animate-check-mark"
          style="animation-delay: 0.2s"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="3"
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>
    </div>

    <!-- Titles -->
    <h3 class="text-3xl sm:text-4xl font-heading font-bold text-brown mb-3 tracking-tight">
      {{ t('upload.success.title') }}
    </h3>
    <p class="text-brown-light mb-10 text-lg max-w-sm leading-relaxed">
      {{ t('upload.success.message') }}
    </p>

    <!-- Action Buttons -->
    <div class="flex flex-col-reverse sm:flex-row gap-4 justify-center w-full max-w-md">
      <button
        class="flex-1 px-8 py-4 bg-white border-2 border-brown/10 text-brown font-heading font-bold rounded-2xl hover:border-terracotta hover:text-terracotta transition-all duration-300 transform active:scale-95 flex items-center justify-center gap-2 group"
        @click="$emit('upload-another')"
      >
        <svg
          class="w-5 h-5 group-hover:rotate-180 transition-transform duration-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        {{ t('upload.success.uploadAnother') }}
      </button>
      <button
        class="flex-1 px-8 py-4 bg-terracotta text-white font-heading font-bold rounded-2xl shadow-lg shadow-terracotta/20 hover:shadow-xl hover:bg-terracotta-dark transition-all duration-300 transform hover:-translate-y-1 active:scale-95 flex items-center justify-center gap-2"
        @click="$emit('view-map')"
      >
        {{ t('upload.success.viewMap') }}
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

defineProps<{
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result: any;
}>();

defineEmits<{
  'upload-another': [];
  'view-map': [];
}>();

const { t } = useI18n();
</script>
