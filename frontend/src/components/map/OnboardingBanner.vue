<template>
  <transition
    enter-active-class="transition-all duration-500 ease-out"
    leave-active-class="transition-all duration-300 ease-in"
    enter-from-class="opacity-0 translate-y-8"
    leave-to-class="opacity-0 translate-y-8"
  >
    <div
      v-if="isVisible"
      class="absolute bottom-6 left-6 right-6 md:left-auto md:right-6 md:w-96 bg-white/95 backdrop-blur-md border-2 border-[var(--color-btn-shade-a)] rounded-xl shadow-xl z-30 overflow-hidden"
    >
      <div class="p-4 flex flex-col gap-3">
        <div class="flex justify-between items-start">
          <h3
            class="font-bold text-lg text-brown font-heading tracking-wide flex items-center gap-2"
          >
            {{ $t('onboarding.title') }}
          </h3>
          <button
            class="text-stone-400 hover:text-stone-600 transition-colors p-1 cursor-pointer"
            :aria-label="$t('accessibility.closeModal')"
            @click="dismiss"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <div class="text-sm text-stone-700 leading-relaxed space-y-2 font-body">
          <p>{{ $t('onboarding.subtitle') }}</p>
          <div class="bg-amber-50 p-3 rounded-xl border border-amber-200">
            <div class="flex items-center gap-2 font-bold text-amber-800 mb-1 font-heading">
              <span class="text-xl"></span> {{ $t('onboarding.earnTreatsTitle') }}
            </div>
            <p class="text-xs text-amber-900 leading-tight">
              {{ $t('onboarding.earnTreatsDesc') }}
            </p>
          </div>
        </div>
        <button
          class="mt-2 w-full py-2 bg-cream hover:bg-sage/20 text-brown font-semibold rounded-xl border border-sage/30 shadow-sm transition-colors text-sm font-heading tracking-wide cursor-pointer"
          @click="dismiss"
        >
          {{ $t('onboarding.exploreButton') }}
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const isVisible = ref(false);
const STORAGE_KEY = 'purrfect_spots_onboarding_dismissed';

onMounted(() => {
  // Check if user has dismissed the banner before
  const hasDismissed = localStorage.getItem(STORAGE_KEY) === 'true';

  // Show it with a slight delay if they haven't seen it
  if (!hasDismissed) {
    setTimeout(() => {
      isVisible.value = true;
    }, 1500);
  }
});

const dismiss = (): void => {
  isVisible.value = false;
  localStorage.setItem(STORAGE_KEY, 'true');
};
</script>
