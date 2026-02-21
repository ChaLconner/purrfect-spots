<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
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
  <div
    ref="imageStageRef"
    class="group relative bg-[#1a1a1a] h-[72vh] overflow-hidden flex items-center justify-center z-1 sm:max-[899px]:h-[85vh] min-[900px]:h-auto"
  >
    <!-- Loading State -->
    <div v-if="!isLoaded" class="absolute inset-0 z-10">
      <SkeletonLoader width="100%" height="100%" border-radius="0" />
    </div>

    <!-- Blurred Background for gaps -->
    <div
      v-if="image"
      class="absolute -inset-5 bg-cover bg-center blur-[40px] brightness-90 saturate-[1.2] opacity-80 z-[-1] scale-110"
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
      class="w-full h-full object-contain relative z-2 drop-shadow-[0_10px_20px_rgba(0,0,0,0.3)] scale-[1.2]"
      @load="$emit('image-load')"
      @error="$emit('image-error', $event)"
    />

    <!-- Gradient Overlay (Bottom) -->
    <div
      class="absolute bottom-0 left-0 w-full h-[120px] bg-gradient-to-t from-black/60 to-transparent pointer-events-none"
    ></div>

    <button
      v-if="hasPrevious"
      class="absolute top-1/2 -translate-y-1/2 left-6 w-10 h-10 md:w-12 md:h-12 rounded-full bg-white/15 backdrop-blur-md border border-white/20 text-white flex items-center justify-center cursor-pointer transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] z-20 opacity-100 md:opacity-0 group-hover:opacity-100 hover:bg-white hover:text-[#1a1a1a] hover:scale-110 hover:shadow-[0_4px_12px_rgba(0,0,0,0.2)] focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 active:scale-95"
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
      class="absolute top-1/2 -translate-y-1/2 right-6 w-10 h-10 md:w-12 md:h-12 rounded-full bg-white/15 backdrop-blur-md border border-white/20 text-white flex items-center justify-center cursor-pointer transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] z-20 opacity-100 md:opacity-0 group-hover:opacity-100 hover:bg-white hover:text-[#1a1a1a] hover:scale-110 hover:shadow-[0_4px_12px_rgba(0,0,0,0.2)] focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 active:scale-95"
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
