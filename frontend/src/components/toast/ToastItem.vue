<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import type { Toast } from '../../types/toast';
import { removeToast } from '../../store/toast';

const props = defineProps<{
  toast: Toast
}>();

const isVisible = ref(false);

onMounted(() => {
  // Small delay to allow enter transition
  requestAnimationFrame(() => {
    isVisible.value = true;
  });

  if (props.toast.duration > 0) {
    setTimeout(() => {
      close();
    }, props.toast.duration);
  }
});

function close() {
  isVisible.value = false;
  // Wait for transition to finish before removing from store
  setTimeout(() => {
    removeToast(props.toast.id);
  }, 400);
}

// Map types to Ghibli theme colors - Updated for "Cuter" Look
const styles = computed(() => {
  switch (props.toast.type) {
    case 'success': 
      return {
        wrapper: 'bg-[#FAF6EC] shadow-md', 
        iconWrapper: 'text-[#6D8B6A]',
        titleColor: '#2F3E2F'
      };
    case 'error': 
      return {
        wrapper: 'bg-[#FFF5F5] shadow-md', 
        iconWrapper: 'text-[#C75B5B]',
        titleColor: '#5C2B2B'
      };
    case 'warning': 
      return {
        wrapper: 'bg-[#FFF9F5] shadow-md', 
        iconWrapper: 'text-[#C97B49]',
        titleColor: '#5C3A2B'
      };
    case 'info':
    default: 
      return {
        wrapper: 'bg-[#F4EBD0] shadow-md', 
        iconWrapper: 'text-[#95A792]',
        titleColor: '#3A4439'
      };
  }
});
</script>

<template>
  <div 
    class="pointer-events-auto w-full max-w-sm rounded-3xl shadow-xl overflow-hidden transition-all duration-500 cubic-bezier(0.68, -0.55, 0.265, 1.55)"
    :class="[
      styles.wrapper, 
      isVisible ? 'translate-x-0 opacity-100 mb-4 scale-100' : 'translate-x-full opacity-0 mb-0 scale-90'
    ]"
    role="alert"
  >
    <div class="p-4 flex items-center relative overflow-hidden">
      <!-- Background Texture Overlay -->
      <div
        class="absolute inset-0 opacity-[0.03] pointer-events-none" 
        style="background-image: url('data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noiseFilter\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.85\' numOctaves=\'3\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noiseFilter)\' opacity=\'1\'/%3E%3C/svg%3E')"
      >
      </div>

      <div class="shrink-0">
        <div class="w-10 h-10 rounded-full flex items-center justify-center" :class="styles.iconWrapper">
          <!-- Cute Cat/Paw Icon replacement or standard rounded icons -->
          
          <!-- Success: Paw -->
          <svg v-if="toast.type === 'success'" class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z" />
          </svg>

          <!-- Error: Round Close -->
          <svg v-else-if="toast.type === 'error'" class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.47 2 2 6.47 2 12C2 17.53 6.47 22 12 22C17.53 22 22 17.53 22 12C22 6.47 17.53 2 12 2ZM17 15.59L15.59 17L12 13.41L8.41 17L7 15.59L10.59 12L7 8.41L8.41 7L12 10.59L15.59 7L17 8.41L13.41 12L17 15.59Z" />
          </svg>

          <!-- Warning: Round Exclamation -->
          <svg v-else-if="toast.type === 'warning'" class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" />
          </svg>

          <!-- Info: Round Info -->
          <svg v-else class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V11H13V17ZM13 9H11V7H13V9Z" />
          </svg>
        </div>
      </div>

      <div class="ml-4 w-0 flex-1">
        <p v-if="toast.title" class="text-sm font-bold tracking-wide" :style="{ color: styles.titleColor }">{{ toast.title }}</p>
        <p class="text-sm mt-0.5 text-brown-dark opacity-80 font-medium leading-relaxed">
          {{ toast.message }}
        </p>
      </div>

      <div class="ml-2 flex shrink-0">
        <button 
          class="inline-flex rounded-full bg-transparent p-1 text-brown/50 hover:text-brown hover:bg-black/5 focus:outline-none transition-all"
          @click="close"
        >
          <span class="sr-only">Close</span>
          <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Optional: Adding more specific styles if needed */
</style>
