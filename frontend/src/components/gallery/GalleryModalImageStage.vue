<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
import type { CatLocation } from '@/types/api';

const props = defineProps<{
  image: CatLocation | null;
  isLoaded: boolean;
  hasError: boolean;
  hasPrevious: boolean;
  hasNext: boolean;
}>();

const emit = defineEmits<{
  close: [];
  navigate: [direction: 'prev' | 'next'];
  'image-load': [];
  'image-error': [event: Event];
}>();

const imageStageRef = ref<HTMLDivElement | null>(null);

// Touch swipe state
const touchStartX = ref(0);
const touchStartY = ref(0);
const isSwiping = ref(false);
const SWIPE_THRESHOLD = 50;

function handleTouchStart(e: TouchEvent): void {
  const touch = e.touches[0];
  touchStartX.value = touch.clientX;
  touchStartY.value = touch.clientY;
  isSwiping.value = true;
}

function handleTouchMove(e: TouchEvent): void {
  if (!isSwiping.value) return;

  const touch = e.touches[0];
  const deltaX = touch.clientX - touchStartX.value;
  const deltaY = Math.abs(touch.clientY - touchStartY.value);

  // Only allow horizontal swipe if moving more horizontally than vertically
  if (Math.abs(deltaX) > deltaY) {
    e.preventDefault();
  }
}

function handleTouchEnd(e: TouchEvent): void {
  if (!isSwiping.value) return;
  isSwiping.value = false;

  const touch = e.changedTouches[0];
  const deltaX = touch.clientX - touchStartX.value;
  const deltaY = Math.abs(touch.clientY - touchStartY.value);

  // Only trigger swipe if horizontal movement is significant and more than vertical
  if (Math.abs(deltaX) > SWIPE_THRESHOLD && Math.abs(deltaX) > deltaY) {
    if (deltaX > 0 && props.hasPrevious) {
      emit('navigate', 'prev');
    } else if (deltaX < 0 && props.hasNext) {
      emit('navigate', 'next');
    }
  }
}

onMounted(() => {
  if (imageStageRef.value) {
    imageStageRef.value.addEventListener('touchstart', handleTouchStart, { passive: true });
    imageStageRef.value.addEventListener('touchmove', handleTouchMove, { passive: false });
    imageStageRef.value.addEventListener('touchend', handleTouchEnd, { passive: true });
  }
});

onUnmounted(() => {
  if (imageStageRef.value) {
    imageStageRef.value.removeEventListener('touchstart', handleTouchStart);
    imageStageRef.value.removeEventListener('touchmove', handleTouchMove);
    imageStageRef.value.removeEventListener('touchend', handleTouchEnd);
  }
});
</script>

<template>
  <div ref="imageStageRef" class="modal-image-stage">
    <!-- Loading State -->
    <div v-if="!isLoaded" class="loading-skeleton">
      <SkeletonLoader width="100%" height="100%" border-radius="0" />
    </div>

    <!-- Blurred Background for gaps -->
    <div
      v-if="image"
      class="blurred-bg"
      :style="{ backgroundImage: `url(${image.image_url})` }"
    ></div>

    <!-- Error State -->
    <div
      v-if="hasError"
      class="error-state flex flex-col items-center justify-center p-8 text-center text-white/60"
    >
      <img class="w-48 h-auto opacity-40 mb-4 grayscale" />
      <p class="font-heading text-xl">{{ $t('galleryPage.modal.imageNotFound') }}</p>
      <p class="text-sm mt-2 opacity-70">{{ $t('galleryPage.modal.imageHiding') }}</p>
    </div>

    <!-- Main Image -->
    <img
      v-else-if="image"
      :src="image.image_url"
      :alt="
        image.location_name
          ? $t('galleryPage.modal.aCatAt', { location: image.location_name })
          : $t('galleryPage.modal.aCat')
      "
      class="main-image"
      @load="$emit('image-load')"
      @error="$emit('image-error', $event)"
    />

    <!-- Gradient Overlay (Bottom) -->
    <div class="image-overlay"></div>

    <!-- Navigation Arrows (Floating) -->
    <button
      v-if="hasPrevious"
      class="nav-btn prev-btn"
      :aria-label="$t('galleryPage.modal.previous')"
      @click.stop="$emit('navigate', 'prev')"
    >
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
      >
        <path d="M15 18L9 12L15 6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>

    <button
      v-if="hasNext"
      class="nav-btn next-btn"
      :aria-label="$t('galleryPage.modal.next')"
      @click.stop="$emit('navigate', 'next')"
    >
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
      >
        <path d="M9 18L15 12L9 6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
/* Image Stage */
.modal-image-stage {
  position: relative;
  background: #1a1a1a;
  height: 38vh;
  flex-shrink: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1; /* Ensure it stays below content if overlapping */
}

@media (min-width: 640px) and (max-width: 899px) {
  .modal-image-stage {
    height: 55vh; /* Taller image on tablets */
  }
}

@media (min-width: 900px) {
  .modal-image-stage {
    flex: 1.6;
    height: auto;
  }
}

.loading-skeleton {
  position: absolute;
  inset: 0;
  z-index: 10;
}

.main-image {
  width: 100%;
  height: 100%;
  object-fit: contain; /* Show full image without cropping */
  position: relative;
  z-index: 2;
  filter: drop-shadow(0 10px 20px rgba(0, 0, 0, 0.3)); /* Add depth */
}

.blurred-bg {
  position: absolute;
  inset: -20px;
  background-size: cover;
  background-position: center;
  filter: blur(40px) brightness(0.9) saturate(1.2); /* Brighter, more vibrant */
  opacity: 0.8; /* Make it more prominent */
  z-index: -1; /* Behind main image */
  transform: scale(1.1);
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 120px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.6), transparent);
  pointer-events: none;
}

/* Nav Buttons on Image */
.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 20;
  opacity: 0; /* Hidden by default for cleaner look, shown on hover */
}

.modal-image-stage:hover .nav-btn {
  opacity: 1;
}

/* On mobile always show */
@media (max-width: 768px) {
  .nav-btn {
    opacity: 1;
    width: 40px;
    height: 40px;
  }
}

.nav-btn:hover {
  background: white;
  color: #1a1a1a;
  transform: translateY(-50%) scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.prev-btn {
  left: 1.5rem;
}
.next-btn {
  right: 1.5rem;
}

.error-state {
  position: relative;
  z-index: 2;
}
</style>
