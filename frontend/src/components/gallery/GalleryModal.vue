<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 max-sm:translate-y-full"
      leave-to-class="opacity-0 max-sm:translate-y-full"
    >
      <dialog
        v-if="image"
        class="fixed inset-0 flex items-center justify-center z-[1000] p-0 sm:p-3 min-[900px]:p-1 border-none m-0 w-screen h-screen overflow-hidden bg-transparent"
        :open="true"
        aria-modal="true"
        aria-labelledby="modal-title"
        @click="$emit('close')"
      >
        <!-- Ghibli-themed Blurred Backdrop -->
        <div class="absolute inset-0 z-[-1] overflow-hidden">
          <GhibliBackground />
          <div class="absolute inset-0 bg-[#0a0a0c]/60 backdrop-blur-[32px]"></div>
        </div>
        <div
          ref="modalContainer"
          class="w-full h-full flex items-center justify-center outline-none sm:h-auto sm:max-h-[96vh] overflow-hidden"
          tabindex="-1"
          @keydown="handleKeydown"
        >
          <div
            class="flex flex-col bg-white w-full h-full overflow-hidden relative shadow-[0_30px_60px_-12px_rgba(0,0,0,0.5)] rounded-none sm:rounded-3xl sm:h-auto sm:min-h-[670px] sm:max-h-[96vh] sm:w-[840px] sm:max-w-[97vw] min-[900px]:grid min-[900px]:grid-cols-[1fr_360px] min-[1200px]:grid-cols-[1fr_400px] min-[900px]:rounded-[2rem] min-[900px]:min-h-[820px] min-[900px]:max-h-[98vh] min-[900px]:w-full min-[900px]:max-w-full"
            @click.stop
          >
            <!-- Left Side: Image Stage -->
            <GalleryModalImageStage
              :image="image"
              :is-loaded="isLoaded"
              :has-error="hasError"
              :has-previous="hasPrevious"
              :has-next="hasNext"
              @close="$emit('close')"
              @navigate="handleNavigation"
              @image-load="onImageLoad"
              @image-error="handleError"
            />

            <!-- Mobile Close Button (Overlays Image) -->
            <button
              class="absolute top-4 right-4 z-50 w-10 h-10 rounded-full border-none bg-black/40 backdrop-blur-[4px] text-white flex items-center justify-center cursor-pointer transition-all duration-300 shadow-[0_4px_12px_rgba(0,0,0,0.2)] active:scale-95 hover:bg-black/60 hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 min-[900px]:hidden"
              aria-label="Close"
              @click.stop="$emit('close')"
            >
              <svg
                width="24"
                height="24"
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

            <!-- Right Side: Content -->
            <GalleryModalContent
              :image="image"
              @close="$emit('close')"
              @update:liked="$emit('update:liked', $event)"
              @update:likes-count="$emit('update:likesCount', $event)"
            />
          </div>
        </div>
      </dialog>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import type { CatLocation } from '@/types/api';
import { useModalFocus } from '@/composables/useModalFocus';

import GalleryModalImageStage from '@/components/gallery/GalleryModalImageStage.vue';
import GalleryModalContent from '@/components/gallery/GalleryModalContent.vue';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';

const props = defineProps<{
  image: CatLocation | null;
  images?: CatLocation[];
  currentIndex?: number;
  totalImages?: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'navigate', direction: 'prev' | 'next'): void;
  (e: 'deleted', id: string): void;
  (e: 'update:liked', val: boolean): void;
  (e: 'update:likesCount', val: number): void;
}>();

const isLoaded = ref(false);
const hasError = ref(false);
const modalContainer = ref<HTMLElement | null>(null);

const { handleKeydown: handleModalFocusKeydown } = useModalFocus(modalContainer, {
  onClose: () => emit('close'),
});

// Navigation computed properties
const hasPrevious = computed(() => {
  return props.currentIndex !== undefined && props.currentIndex > 0;
});

const hasNext = computed(() => {
  if (props.currentIndex === undefined) return false;
  if (props.totalImages !== undefined) {
    return props.currentIndex < props.totalImages - 1;
  }
  return props.images && props.currentIndex < props.images.length - 1;
});

function handleNavigation(direction: 'prev' | 'next'): void {
  emit('navigate', direction);
}

function navigatePrev(): void {
  if (hasPrevious.value) handleNavigation('prev');
}

function navigateNext(): void {
  if (hasNext.value) handleNavigation('next');
}

function handleKeydown(e: KeyboardEvent): void {
  if (!props.image) return;

  switch (e.key) {
    case 'ArrowLeft':
      navigatePrev();
      break;
    case 'ArrowRight':
      navigateNext();
      break;
    default:
      handleModalFocusKeydown(e);
      break;
  }
}

// Preload adjacent images
function preloadAdjacentImages(): void {
  if (!props.images || props.currentIndex === undefined) return;

  const preloadImage = (url: string): void => {
    const img = new Image();
    img.src = url;
  };

  // Preload next 2 images
  for (let i = 1; i <= 2; i++) {
    if (props.currentIndex + i < props.images.length) {
      preloadImage(props.images[props.currentIndex + i].image_url);
    }
  }

  // Preload previous 2 images
  for (let i = 1; i <= 2; i++) {
    if (props.currentIndex - i >= 0) {
      preloadImage(props.images[props.currentIndex - i].image_url);
    }
  }
}

function onImageLoad(): void {
  isLoaded.value = true;
}

function handleError(_event: Event): void {
  hasError.value = true;
  isLoaded.value = true;
}

onMounted(() => {
  if (props.image) {
    preloadAdjacentImages();
  }
});

watch(
  () => props.image,
  (newVal) => {
    if (newVal) {
      isLoaded.value = false;
      hasError.value = false;
      preloadAdjacentImages();
    }
  }
);

watch(
  () => props.currentIndex,
  () => {
    preloadAdjacentImages();
  }
);
</script>
