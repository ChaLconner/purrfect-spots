<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import type { Toast } from '../../types/toast';
import { removeToast } from '../../store/toast';

const props = defineProps<{
  toast: Toast;
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
        iconColor: '#6D8B6A',
        titleColor: '#2F3E2F',
      };
    case 'error':
      return {
        wrapper: 'bg-[#FFF5F5] shadow-md',
        iconColor: '#C75B5B',
        titleColor: '#5C2B2B',
      };
    case 'warning':
      return {
        wrapper: 'bg-[#FFF9F5] shadow-md',
        iconColor: '#C97B49',
        titleColor: '#5C3A2B',
      };
    case 'info':
    default:
      return {
        wrapper: 'bg-[#F4EBD0] shadow-md',
        iconColor: '#95A792',
        titleColor: '#3A4439',
      };
  }
});
</script>

<template>
  <div
    class="pointer-events-auto w-full max-w-sm rounded-[1.5rem] shadow-xl overflow-hidden transition-all duration-500 cubic-bezier(0.68, -0.55, 0.265, 1.55)"
    :class="[
      styles.wrapper,
      isVisible
        ? 'translate-x-0 opacity-100 mb-4 scale-100'
        : 'translate-x-full opacity-0 mb-0 scale-90',
    ]"
    role="alert"
  >
    <div class="p-4 flex items-center relative overflow-hidden">
      <!-- Background Texture Overlay -->
      <div
        class="absolute inset-0 opacity-[0.03] pointer-events-none"
        style="
          background-image: url(&quot;data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='1'/%3E%3C/svg%3E&quot;);
        "
      ></div>

      <div class="flex-1 relative z-10">
        <p
          v-if="toast.title"
          class="text-sm font-bold tracking-wide"
          :class="[
            toast.type === 'success'
              ? 'text-[#2F3E2F]'
              : toast.type === 'error'
                ? 'text-[#5C2B2B]'
                : toast.type === 'warning'
                  ? 'text-[#5C3A2B]'
                  : 'text-[#3A4439]',
          ]"
        >
          {{ toast.title }}
        </p>
        <p class="text-xs mt-0.5 text-brown-dark opacity-80 font-medium leading-relaxed">
          {{ toast.message }}
        </p>
      </div>

      <div class="ml-4 flex items-center shrink-0 space-x-2 relative z-10">
        <!-- Action Button -->
        <button
          v-if="toast.action"
          class="px-3 py-1 text-[10px] font-bold rounded-full transition-all duration-200 hover:brightness-95 active:scale-95 shadow-sm text-white"
          :class="[
            toast.type === 'success'
              ? 'bg-[#6D8B6A]'
              : toast.type === 'error'
                ? 'bg-[#C75B5B]'
                : toast.type === 'warning'
                  ? 'bg-[#C97B49]'
                  : 'bg-[#95A792]',
          ]"
          @click="toast.action.onClick"
        >
          {{ toast.action.label }}
        </button>

        <!-- Close Button -->
        <button
          class="inline-flex rounded-full bg-transparent p-1 text-brown/50 hover:text-brown hover:bg-black/5 focus:outline-none transition-all"
          @click="close"
        >
          <span class="sr-only">Close</span>
          <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path
              d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
