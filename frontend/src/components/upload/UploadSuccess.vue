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

    <!-- Upload Summary Card -->
    <div
      v-if="result"
      class="bg-white/50 backdrop-blur-sm rounded-3xl p-6 mb-10 w-full max-w-md text-left border border-white/60 shadow-lg shadow-brown/5 group hover:shadow-xl transition-all duration-500"
    >
      <div class="flex justify-between items-start mb-6">
        <div class="space-y-1">
          <h4 class="font-heading font-bold text-brown text-xl leading-tight">
            {{ result.photo?.location_name || t('upload.success.newSpot') }}
          </h4>
          <div
            class="flex items-center text-stone-400 text-xs font-medium uppercase tracking-wider"
          >
            <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            {{ new Date().toLocaleDateString() }}
          </div>
        </div>
        <div
          v-if="result.cat_detection?.has_cats"
          class="inline-flex items-center bg-sage/10 text-sage-dark text-[10px] px-2.5 py-1 rounded-full font-bold uppercase tracking-widest border border-sage/20"
        >
          <span class="w-1.5 h-1.5 bg-sage-dark rounded-full mr-2 animate-pulse"></span>
          {{ t('upload.success.verified') }}
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div
          class="bg-stone-50/50 p-4 rounded-2xl border border-stone-100 group-hover:bg-white group-hover:shadow-sm transition-all"
        >
          <p class="text-stone-400 text-[10px] uppercase tracking-widest font-bold mb-2">
            {{ t('upload.success.catsDetected') }}
          </p>
          <div class="flex items-end gap-1">
            <span class="text-brown font-heading font-bold text-3xl tabular-nums">{{
              result.cat_detection?.cat_count || 0
            }}</span>
            <span class="text-brown-light text-sm font-body mb-1">{{ t('cats.cats') }}</span>
          </div>
        </div>
        <div
          class="bg-stone-50/50 p-4 rounded-2xl border border-stone-100 group-hover:bg-white group-hover:shadow-sm transition-all"
        >
          <p class="text-stone-400 text-[10px] uppercase tracking-widest font-bold mb-2">
            {{ t('upload.success.confidence') }}
          </p>
          <div class="flex items-end gap-1">
            <span class="text-brown font-heading font-bold text-3xl tabular-nums">{{
              Math.round((result.cat_detection?.confidence || 0) * 100)
            }}</span>
            <span class="text-brown-light text-sm font-body mb-1">%</span>
          </div>
        </div>
      </div>
    </div>

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

<style scoped>
@keyframes check-mark {
  0% {
    transform: scale(0) rotate(-45deg);
    opacity: 0;
  }
  50% {
    transform: scale(1.2) rotate(0deg);
  }
  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

.animate-check-mark {
  animation: check-mark 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
  animation-delay: 0.2s;
}

@keyframes bounce-slow {
  0%,
  100% {
    transform: translateY(-5%);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: translateY(0);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
}

.animate-bounce-slow {
  animation: bounce-slow 3s infinite;
}
</style>
