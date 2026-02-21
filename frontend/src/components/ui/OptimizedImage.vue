<script setup lang="ts">
/**
 * OptimizedImage Component
 *
 * Handles responsive images with:
 * - Lazy loading (via useImageLoader)
 * - srcset/sizes for responsive images
 * - Blur placeholder on load
 * - Error handling with fallback
 * - WebP support detection
 */
import { computed } from 'vue';
import { useImageLoader } from '@/composables/useImageLoader';

interface Props {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  sizes?: string;
  lazy?: boolean;
  placeholder?: string;
  aspectRatio?: string;
  objectFit?: 'cover' | 'contain' | 'fill' | 'none';
  fallbackSrc?: string;
}

const props = withDefaults(defineProps<Props>(), {
  lazy: true,
  objectFit: 'cover',
  sizes: '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw',
  fallbackSrc: '/placeholder-cat.svg',
});

const emit = defineEmits<{
  (e: 'load'): void;
  (e: 'error', error: Event): void;
}>();

// Use the composable for loading logic
const {
  isLoaded,
  hasError,
  isIntersecting,
  handleLoad: onInternalLoad,
  handleError: onInternalError,
  retry,
  imageRef,
} = useImageLoader({
  src: props.src,
  lazy: props.lazy,
});

// Event handlers
function handleLoad(): void {
  onInternalLoad();
  emit('load');
}

function handleError(event: Event): void {
  onInternalError(event);
  emit('error', event);
}

// Generate srcset for responsive images
const srcset = computed(() => {
  if (!props.src) return '';

  // Check if it's an external URL (CDN, S3, etc.)
  const isExternalUrl = props.src.startsWith('http');

  if (isExternalUrl) {
    const baseUrl = props.src.split('?')[0];
    const sizes = [320, 640, 960, 1280, 1920];

    return sizes.map((size) => `${baseUrl}?w=${size} ${size}w`).join(', ');
  }

  return props.src;
});

// Aspect ratio style
const aspectRatioStyle = computed(() => {
  if (props.aspectRatio) {
    return { aspectRatio: props.aspectRatio };
  }
  if (props.width && props.height) {
    return { aspectRatio: `${props.width} / ${props.height}` };
  }
  return {};
});
</script>

<template>
  <div ref="imageRef" class="relative overflow-hidden bg-gray-100" :style="aspectRatioStyle">
    <!-- Placeholder/Skeleton -->
    <div
      v-if="!isLoaded && !hasError"
      class="absolute inset-0 flex items-center justify-center z-10 transition-opacity duration-300 ease-out"
      :class="{ 'opacity-0': isLoaded }"
    >
      <img
        v-if="placeholder"
        :src="placeholder"
        class="w-full h-full object-cover blur-[20px] scale-110"
        alt=""
        aria-hidden="true"
      />
      <div
        v-else
        class="w-full h-full bg-[linear-gradient(90deg,#e5e7eb_25%,#f3f4f6_50%,#e5e7eb_75%)] bg-[length:200%_100%] animate-shimmer"
      ></div>
    </div>

    <!-- Actual Image -->
    <img
      v-if="isIntersecting && !hasError"
      :src="src"
      :srcset="srcset"
      :sizes="sizes"
      :alt="alt"
      :width="width"
      :height="height"
      :loading="lazy ? 'lazy' : 'eager'"
      :decoding="lazy ? 'async' : 'auto'"
      class="w-full h-full opacity-0 transition-opacity duration-300 ease-out"
      :class="{
        'opacity-100': isLoaded,
        [`object-${objectFit}`]: true,
      }"
      @load="handleLoad"
      @error="handleError"
    />

    <!-- Error State -->
    <div
      v-if="hasError"
      class="absolute inset-0 flex flex-col items-center justify-center bg-gray-50"
    >
      <img
        :src="fallbackSrc"
        :alt="`Failed to load: ${alt}`"
        class="w-1/2 max-w-[100px] opacity-50"
      />
      <button
        class="absolute bottom-2 right-2 p-2 bg-white rounded-full shadow-[0_2px_8px_rgba(0,0,0,0.15)] text-gray-500 transition-all duration-200 hover:bg-gray-100 hover:text-gray-700"
        aria-label="Retry loading image"
        @click="retry"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
      </button>
    </div>
  </div>
</template>
