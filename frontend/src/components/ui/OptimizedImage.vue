<script setup lang="ts">
/**
 * OptimizedImage Component
 * 
 * Handles responsive images with:
 * - Lazy loading
 * - srcset/sizes for responsive images
 * - Blur placeholder on load
 * - Error handling with fallback
 * - WebP support detection
 */
import { ref, computed, onMounted } from 'vue';

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
  fallbackSrc: '/placeholder-cat.svg'
});

const emit = defineEmits<{
  (e: 'load'): void;
  (e: 'error', error: Event): void;
}>();

const imageRef = ref<HTMLImageElement | null>(null);
const isLoaded = ref(false);
const hasError = ref(false);
const isIntersecting = ref(!props.lazy);

// Generate srcset for responsive images
// Assumes backend can serve different sizes via query params or has pre-generated sizes
const srcset = computed(() => {
  if (!props.src) return '';
  
  // Check if it's an external URL (CDN, S3, etc.)
  const isExternalUrl = props.src.startsWith('http');
  
  if (isExternalUrl) {
    // For S3/CDN images, we can use Cloudinary-style or similar transforms
    // Or just return original if no transform service is available
    // Many CDNs support width parameter
    const baseUrl = props.src.split('?')[0];
    const sizes = [320, 640, 960, 1280, 1920];
    
    return sizes
      .map(size => `${baseUrl}?w=${size} ${size}w`)
      .join(', ');
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

// Setup intersection observer for lazy loading
onMounted(() => {
  if (!props.lazy || !imageRef.value) {
    isIntersecting.value = true;
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          isIntersecting.value = true;
          observer.disconnect();
        }
      });
    },
    {
      rootMargin: '200px', // Start loading before it's in view
      threshold: 0.01
    }
  );

  observer.observe(imageRef.value);
});

function handleLoad() {
  isLoaded.value = true;
  emit('load');
}

function handleError(event: Event) {
  hasError.value = true;
  emit('error', event);
}

// Retry loading
function retry() {
  hasError.value = false;
  isLoaded.value = false;
  // Force re-render by toggling intersection
  isIntersecting.value = false;
  setTimeout(() => {
    isIntersecting.value = true;
  }, 100);
}
</script>

<template>
  <div 
    ref="imageRef"
    class="optimized-image-container"
    :style="aspectRatioStyle"
  >
    <!-- Placeholder/Skeleton -->
    <div 
      v-if="!isLoaded && !hasError"
      class="image-placeholder"
      :class="{ 'fade-out': isLoaded }"
    >
      <img 
        v-if="placeholder" 
        :src="placeholder" 
        class="placeholder-image"
        alt=""
        aria-hidden="true"
      />
      <div v-else class="skeleton-placeholder animate-pulse" />
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
      class="optimized-image"
      :class="{ 
        'is-loaded': isLoaded,
        [`object-${objectFit}`]: true
      }"
      @load="handleLoad"
      @error="handleError"
    />

    <!-- Error State -->
    <div v-if="hasError" class="image-error">
      <img 
        :src="fallbackSrc" 
        :alt="`Failed to load: ${alt}`"
        class="fallback-image"
      />
      <button 
        @click="retry"
        class="retry-button"
        aria-label="Retry loading image"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.optimized-image-container {
  position: relative;
  overflow: hidden;
  background-color: #f3f4f6;
}

.image-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  transition: opacity 0.3s ease-out;
}

.image-placeholder.fade-out {
  opacity: 0;
}

.placeholder-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(20px);
  transform: scale(1.1);
}

.skeleton-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.optimized-image {
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: opacity 0.3s ease-out;
}

.optimized-image.is-loaded {
  opacity: 1;
}

.object-cover { object-fit: cover; }
.object-contain { object-fit: contain; }
.object-fill { object-fit: fill; }
.object-none { object-fit: none; }

.image-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
}

.fallback-image {
  width: 50%;
  max-width: 100px;
  opacity: 0.5;
}

.retry-button {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  padding: 0.5rem;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  color: #6b7280;
  transition: all 0.2s;
}

.retry-button:hover {
  background: #f3f4f6;
  color: #374151;
}
</style>
