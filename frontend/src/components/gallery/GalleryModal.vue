<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <dialog
        v-if="image"
        class="modal-backdrop"
        :open="true"
        aria-modal="true"
        aria-labelledby="modal-title"
        @click="$emit('close')"
      >
        <div
          ref="modalContainer"
          class="modal-container"
          tabindex="-1"
          @click.stop
          @keydown="handleKeydown"
        >
          <div class="modal-card">
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
            <button class="mobile-close-btn" aria-label="Close" @click.stop="$emit('close')">
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
            <GalleryModalContent :image="image" @close="$emit('close')" />
          </div>
        </div>
      </dialog>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue';
import type { CatLocation } from '@/types/api';

import GalleryModalImageStage from '@/components/gallery/GalleryModalImageStage.vue';
import GalleryModalContent from '@/components/gallery/GalleryModalContent.vue';

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
}>();

const isLoaded = ref(false);
const hasError = ref(false);

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

// Keyboard navigation
function handleKeydown(e: KeyboardEvent): void {
  if (!props.image) return;

  switch (e.key) {
    case 'Escape':
      emit('close');
      break;
    case 'ArrowLeft':
      navigatePrev();
      break;
    case 'ArrowRight':
      navigateNext();
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

function setupListeners(): void {
  document.body.style.overflow = 'hidden';
  preloadAdjacentImages();
}

function cleanupListeners(): void {
  document.body.style.overflow = '';
}

function onImageLoad(): void {
  isLoaded.value = true;
}

function handleError(_event: Event): void {
  hasError.value = true;
  isLoaded.value = true;
}

const modalContainer = ref<HTMLElement | null>(null);

onMounted(() => {
  if (props.image) {
    setupListeners();
    // Focus for a11y
    nextTick(() => {
      modalContainer.value?.focus();
    });
  }
});

watch(
  () => props.image,
  (newVal) => {
    if (newVal) {
      isLoaded.value = false;
      hasError.value = false;
      setupListeners();
    } else {
      cleanupListeners();
    }
  }
);

watch(
  () => props.currentIndex,
  () => {
    preloadAdjacentImages();
  }
);

onUnmounted(() => {
  cleanupListeners();
});
</script>

<style scoped>
/* Modal Backdrop & Container Styles (Layout only) */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 12, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 0;
  border: none;
  margin: 0;
  width: 100vw;
  height: 100vh;
}

/* Tablet & Desktop: Add padding so it's not full edge-to-edge unless mobile */
@media (min-width: 640px) {
  .modal-backdrop {
    padding: 1.5rem;
  }
}

@media (min-width: 1024px) {
  .modal-backdrop {
    padding: 2.5rem;
  }
}

.modal-container {
  width: 100%;
  height: 100%;
  max-width: 1200px;
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
}

/* On non-mobile, constrain height */
@media (min-width: 640px) {
  .modal-container {
    height: auto;
    max-height: 90vh;
  }
}

.modal-card {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  width: 100%;
  height: 100%;
  overflow: hidden;
  position: relative;
  box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.5);
  /* Mobile: Square corners by default */
  border-radius: 0;
}

/* Tablet Portrait / Large Mobile: Card look, but vertical */
@media (min-width: 640px) {
  .modal-card {
    border-radius: 1.5rem;
    height: auto;
    min-height: 500px;
    max-height: 90vh;
    width: 600px; /* Constrain width on tablet so it's not too wide */
    max-width: 90vw;
  }
}

/* Desktop / Landscape Tablet: Row layout */
@media (min-width: 900px) {
  .modal-card {
    flex-direction: row;
    border-radius: 2rem;
    height: auto;
    min-height: 600px;
    max-height: 85vh;
    width: 100%; /* Reset width constraint for desktop flexible layout */
    max-width: 100%;
  }
}

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: all 0.3s ease-out;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}

@media (max-width: 639px) {
  .modal-fade-enter-from,
  .modal-fade-leave-to {
    opacity: 0;
    transform: translateY(100%); /* Slide up on mobile */
  }
}
/* Mobile Close Button */
.mobile-close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 50;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.mobile-close-btn:active {
  transform: scale(0.95);
  background: rgba(0, 0, 0, 0.6);
}

@media (min-width: 900px) {
  .mobile-close-btn {
    display: none;
  }
}
</style>
