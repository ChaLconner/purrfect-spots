<template>
  <div class="text-center mb-8 relative z-10">
    <div class="mb-8">
      <h1 class="font-heading text-4xl font-bold text-text-primary mb-2">
        {{ $t('galleryPage.header.title') }}
      </h1>
      <p class="font-body text-base text-text-secondary font-medium max-w-xl mx-auto">
        {{ $t('galleryPage.header.subtitle') }}
      </p>
    </div>

    <!-- Search Bar with Debounce -->
    <div class="flex justify-center max-w-xl mx-auto mt-8">
      <div class="w-full">
        <div
          class="flex items-center gap-3 bg-white/40 backdrop-blur-xl rounded-full px-6 py-4 shadow-[0_8px_32px_rgba(0,0,0,0.1)] transition-all duration-300 border border-white/40 hover:shadow-[0_8px_32px_rgba(0,0,0,0.15)] hover:bg-white/50 focus-within:bg-white/60 focus-within:ring-2 focus-within:ring-primary/30"
          role="search"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="text-gray-400"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            v-model="localSearchQuery"
            type="text"
            :placeholder="$t('galleryPage.header.searchPlaceholder')"
            class="w-full bg-transparent border-none outline-none font-body text-lg text-text-primary placeholder-gray-400"
            :aria-label="$t('galleryPage.header.searchAriaLabel')"
            autocomplete="off"
            @input="handleSearchInput"
          />
          <button
            v-if="localSearchQuery"
            class="flex items-center justify-center p-1 rounded-full bg-secondary/20 text-text-secondary hover:bg-secondary/40 transition-colors"
            aria-label="Clear search"
            @click="clearSearch"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useCatsStore } from '@/store';
import { ANIMATION_CONFIG } from '@/utils/constants';

const catsStore = useCatsStore();

// Local search state for debouncing
const localSearchQuery = ref(catsStore.gallerySearchQuery);

// Debounce timer
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// Sync from store on mount
onMounted(() => {
  localSearchQuery.value = catsStore.gallerySearchQuery;
});

// Watch store changes to sync local state
watch(
  () => catsStore.gallerySearchQuery,
  (newVal) => {
    if (localSearchQuery.value !== newVal) {
      localSearchQuery.value = newVal;
    }
  }
);

// Debounced search handler
function handleSearchInput(): void {
  // Clear existing timer
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  // Set new timer with debounce delay
  debounceTimer = setTimeout(() => {
    catsStore.setGallerySearchQuery(localSearchQuery.value);
  }, ANIMATION_CONFIG.DEBOUNCE_DELAY_MS);
}

// Clear search immediately
function clearSearch(): void {
  localSearchQuery.value = '';
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  catsStore.setGallerySearchQuery('');
}

// Cleanup timer on unmount
onUnmounted(() => {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
});
</script>
