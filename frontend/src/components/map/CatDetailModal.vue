<template>
  <transition
    enter-active-class="transition-all duration-300 ease-out"
    leave-active-class="transition-all duration-200 ease-in"
    enter-from-class="opacity-0 scale-95"
    leave-to-class="opacity-0 scale-95"
  >
    <div
      v-if="cat"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click="$emit('close')"
    >
      <div
        class="bg-white rounded-3xl max-w-sm w-full overflow-hidden shadow-2xl relative transform transition-all"
        @click.stop
      >
        <!-- Image with gradient overlay -->
        <div class="relative h-64">
          <img
            :src="cat.image_url"
            :alt="cat.location_name || 'Cat photo'"
            class="w-full h-full object-cover"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
          
          <!-- Close button (Top right) -->
          <button
            class="absolute top-4 right-4 w-8 h-8 rounded-full bg-black/20 backdrop-blur-md flex items-center justify-center text-white hover:bg-black/40 transition-all cursor-pointer border border-white/20"
            aria-label="Close"
            @click="$emit('close')"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>

          <!-- Location badge (Clean text only) -->
          <div class="absolute bottom-4 left-4">
            <span class="bg-white/95 backdrop-blur-md text-brown-dark text-sm font-bold px-4 py-1.5 rounded-full shadow-lg">
              {{ cat.location_name }}
            </span>
          </div>
        </div>

        <!-- Content -->
        <div class="p-6 pt-5">
          <div class="text-center mb-6">
            <h3 class="font-heading font-extrabold text-2xl text-brown mb-1">Cat Spotted!</h3>
            <p class="text-stone-600 text-sm font-medium">Click direction for navigation</p>
          </div>

          <!-- Description Box (No Border) -->
          <div class="bg-cream-light/50 rounded-2xl p-5 mb-6">
            <p class="text-brown-dark text-base leading-relaxed text-center font-medium">
              {{ cleanDescription || 'A lovely cat was spotted here.' }}
            </p>
          </div>

          <!-- Tags (displayed as pills) -->
          <div v-if="tags.length > 0" class="flex flex-wrap gap-2 justify-center mb-6">
            <button
              v-for="tag in tags"
              :key="tag"
              class="inline-flex items-center px-3 py-1 bg-sage-light/30 hover:bg-sage-light/50 text-sage-dark text-xs font-semibold rounded-full transition-colors cursor-pointer"
              @click="$emit('tag-click', tag)"
            >
              #{{ tag }}
            </button>
          </div>

          <!-- Action buttons -->
          <div class="flex flex-col gap-3 mt-4">
            <button 
              class="w-full py-4 rounded-2xl bg-gradient-to-r from-[#C97B49] to-[#A85D2E] text-white font-extrabold tracking-wide hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-300 active:scale-95 shadow-lg shadow-orange-500/20 cursor-pointer"
              @click="$emit('get-directions', cat)"
            >
              GET DIRECTIONS
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { CatLocation } from '@/types/api';
import { extractTags, getCleanDescription } from '@/store/cats';

const props = defineProps<{
  cat: CatLocation | null;
}>();

defineEmits<{
  (e: 'close'): void;
  (e: 'tag-click', tag: string): void;
  (e: 'get-directions', cat: CatLocation): void;
}>();

const cleanDescription = computed(() => {
  if (!props.cat) return '';
  const desc = getCleanDescription(props.cat.description);
  return desc !== '-' ? desc : '';
});

const tags = computed(() => {
  if (!props.cat) return [];
  return extractTags(props.cat.description);
});
</script>
