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
          <div class="absolute inset-0 bg-stone-900/60 backdrop-blur-2xl"></div>
        </div>
        <div
          ref="modalContainer"
          class="w-full h-full flex items-center justify-center outline-none sm:h-auto sm:max-h-[96vh] overflow-hidden"
          tabindex="-1"
          @keydown="handleKeydown"
        >
          <div
            class="flex flex-col bg-white w-full h-full overflow-hidden relative shadow-2xl rounded-none sm:rounded-3xl sm:h-auto sm:min-h-[550px] sm:max-h-[90vh] sm:w-[840px] sm:max-w-[95vw] lg:grid lg:grid-cols-[1fr_420px] xl:grid-cols-[1fr_440px] lg:rounded-3xl lg:h-[640px] lg:max-h-[88vh] lg:w-[1020px] lg:max-w-[90vw] font-body"
            @click.stop
          >
            <!-- Left Side: Image Stage -->
            <GalleryModalImageStage
              :image="image"
              :is-loaded="isLoaded"
              :has-error="hasError"
              :has-previous="hasPrevious ?? false"
              :has-next="hasNext ?? false"
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
              <CloseIcon />
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
import CloseIcon from '@/components/icons/CloseIcon.vue';

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

  const connection = (navigator as Navigator & {
    connection?: { saveData?: boolean; effectiveType?: string };
  }).connection;
  if (connection?.saveData || connection?.effectiveType === '2g') return;

  const preloadImage = (url: string): void => {
    const img = new Image();
    img.src = url;
  };

  // Preload only immediate neighbors; full prefetch floods mobile connections.
  for (let i = 1; i <= 1; i++) {
    if (props.currentIndex + i < props.images.length) {
      preloadImage(props.images[props.currentIndex + i].image_url);
    }
  }

  for (let i = 1; i <= 1; i++) {
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
