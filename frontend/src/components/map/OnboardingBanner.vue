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
            class="font-bold text-lg text-[var(--color-text-primary)] font-['Fredoka'] tracking-wide flex items-center gap-2"
          >
            Welcome to Purrfect Spots!
          </h3>
          <button
            @click="dismiss"
            class="text-gray-400 hover:text-gray-600 transition-colors p-1"
            aria-label="Close"
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
        <div class="text-sm text-gray-700 leading-relaxed space-y-2">
          <p>Discover and share your favorite cat hangouts!</p>
          <div class="bg-amber-100/50 p-3 rounded-lg border border-amber-200">
            <div class="flex items-center gap-2 font-bold text-amber-800 mb-1">
              <span class="text-xl"></span> Earn Treats!
            </div>
            <p class="text-xs text-amber-900 leading-tight">
              Upload photos to earn Treats. Use Treats to unlock exclusive badges and premium
              features. Become the ultimate cat spotter in your neighborhood!
            </p>
          </div>
        </div>
        <button
          @click="dismiss"
          class="mt-2 w-full py-2 bg-[var(--color-bg-primary)] hover:bg-[#d8e4d6] text-[var(--color-text-primary)] font-semibold rounded-lg border border-[var(--color-btn-shade-b)] shadow-sm transition-colors text-sm font-['Fredoka'] tracking-wide"
        >
          Got it, let's explore!
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

const dismiss = () => {
  isVisible.value = false;
  localStorage.setItem(STORAGE_KEY, 'true');
};
</script>
