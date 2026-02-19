<template>
  <div
    class="rounded-3xl p-8 flex flex-col transition-all duration-300 relative h-full"
    :class="[
      isPremium
        ? 'bg-white shadow-2xl border-2 border-terracotta transform hover:scale-[1.02] z-10'
        : 'bg-glass shadow-lg border border-white/40',
      { 'bg-stone-50': disabled },
    ]"
  >
    <!-- Badge -->
    <div
      v-if="badge"
      class="absolute -top-4 right-8 bg-terracotta text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-lg tracking-widest uppercase"
    >
      {{ badge }}
    </div>

    <!-- Header -->
    <h3 class="text-2xl font-bold mb-2" :class="isPremium ? 'text-terracotta' : 'text-brown'">
      {{ title }}
    </h3>
    <p class="text-stone-500 mb-6 text-sm">{{ subtitle }}</p>

    <!-- Features -->
    <ul class="space-y-4 mb-8 text-brown-light flex-grow">
      <li v-for="(feature, index) in features" :key="index" class="flex items-start">
        <svg
          class="h-5 w-5 mr-3 mt-0.5 flex-shrink-0"
          :class="isPremium ? 'text-terracotta' : 'text-sage-dark'"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 13l4 4L19 7"
          />
        </svg>
        <span class="text-sm sm:text-base">{{ feature }}</span>
      </li>
    </ul>

    <!-- Price -->
    <div class="text-center pt-6 border-t border-stone-100 mb-8 mt-auto">
      <span class="block text-4xl font-extrabold text-brown mb-1">{{ price }}</span>
      <span class="text-stone-400 text-sm font-medium">{{ period }}</span>
    </div>

    <!-- Actions -->
    <div class="w-full">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

defineProps<{
  title: string;
  subtitle: string;
  price: string;
  period: string;
  features: string[];
  isPremium?: boolean;
  badge?: string;
  disabled?: boolean;
}>();
</script>

<style scoped>
/* Glass effect duplication - should be global utility ideally */
.bg-glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
}
</style>
