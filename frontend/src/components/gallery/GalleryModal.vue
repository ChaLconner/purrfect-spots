<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="image"
        class="modal-backdrop"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        @click="$emit('close')"
      >
        <div class="modal-container" @click.stop>
          <div class="modal-card">
            <!-- Left Side: Image Stage -->
            <div ref="imageStageRef" class="modal-image-stage">
              <!-- Loading State -->
              <div v-if="!isLoaded" class="loading-skeleton">
                <SkeletonLoader width="100%" height="100%" border-radius="0" />
              </div>

              <!-- Main Image -->
              <img
                :src="image.image_url"
                :alt="image.location_name || 'Cat photo'"
                class="main-image"
                :class="{ 'is-visible': isLoaded }"
                @load="onImageLoad"
                @error="handleError"
              />

              <!-- Gradient Overlay (Bottom) -->
              <div class="image-overlay"></div>

              <!-- Navigation Arrows (Floating) -->
              <button
                v-if="hasPrevious"
                class="nav-btn prev-btn"
                aria-label="Previous image"
                @click.stop="navigatePrev"
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
                aria-label="Next image"
                @click.stop="navigateNext"
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

            <!-- Right Side: Content -->
            <div class="modal-content">
              <!-- Header -->
              <div class="content-header">
                <div>
                  <h3 id="modal-title" class="cat-title">Cat Details</h3>
                  <div class="cat-meta">
                    <span v-if="image.location_name" class="location-badge">
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.5"
                        class="mr-1"
                      >
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                        <circle cx="12" cy="10" r="3" />
                      </svg>
                      {{ image.location_name }}
                    </span>
                    <span v-if="dateFormatted" class="date-text">{{ dateFormatted }}</span>
                  </div>
                </div>

                <button
                  ref="closeButtonRef"
                  class="close-btn"
                  aria-label="Close"
                  @click="$emit('close')"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>

              <!-- Body -->
              <div class="content-body">
                <div class="description-section">
                  <p v-if="cleanDescription" class="description-text">
                    {{ cleanDescription }}
                  </p>
                  <p v-else class="description-placeholder">
                    No description available for this spot.
                  </p>
                </div>

                <!-- Tags -->
                <div v-if="imageTags.length > 0" class="tags-section">
                  <p class="section-label">Discover More</p>
                  <div class="tags-list">
                    <button
                      v-for="tag in imageTags"
                      :key="tag"
                      class="tag-chip"
                      @click="searchByTag(tag)"
                    >
                      #{{ tag }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Footer Actions -->
              <div class="content-footer">
                <button class="action-btn primary" @click="openDirections">
                  Get Directions
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                    class="ml-2"
                  >
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
import { useCatsStore } from '@/store';
import { extractTags, getCleanDescription } from '@/store/catsStore';
import type { CatLocation } from '@/types/api';
import { IMAGE_CONFIG } from '@/utils/constants';

const props = defineProps<{
  image: CatLocation | null;
  images?: CatLocation[];
  currentIndex?: number;
  totalImages?: number; // Total count for accurate navigation
}>();

const emit = defineEmits<{
  close: [];
  navigate: [direction: 'prev' | 'next'];
}>();

const router = useRouter();
const catsStore = useCatsStore();
const closeButtonRef = ref<HTMLButtonElement | null>(null);
const imageStageRef = ref<HTMLDivElement | null>(null);
const isLoaded = ref(false);

// Touch swipe state
const touchStartX = ref(0);
const touchStartY = ref(0);
const isSwiping = ref(false);
const SWIPE_THRESHOLD = 50;

// Navigation computed properties
const hasPrevious = computed(() => {
  return props.currentIndex !== undefined && props.currentIndex > 0;
});

const hasNext = computed(() => {
  if (props.currentIndex === undefined) return false;

  // Use totalImages if provided (more accurate for full navigation)
  if (props.totalImages !== undefined) {
    return props.currentIndex < props.totalImages - 1;
  }

  // Fallback to images array length
  return props.images && props.currentIndex < props.images.length - 1;
});

// Clean description
const cleanDescription = computed(() => {
  if (!props.image?.description) return '';
  return getCleanDescription(props.image.description);
});

// Filtered tags
const imageTags = computed(() => {
  if (!props.image?.description) return [];
  return extractTags(props.image.description);
});

// Formatted Date
const dateFormatted = computed(() => {
  if (!props.image?.uploaded_at) return '';
  try {
    return new Date(props.image.uploaded_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return '';
  }
});

// Navigation functions
function navigatePrev() {
  if (hasPrevious.value) {
    emit('navigate', 'prev');
  }
}

function navigateNext() {
  if (hasNext.value) {
    emit('navigate', 'next');
  }
}

// Search by tag
function searchByTag(tag: string) {
  catsStore.setSearchQuery(`#${tag}`);
  emit('close');
  router.push({ path: '/map', query: { search: `#${tag}` } });
}

// Open Google Maps Directions
function openDirections() {
  if (!props.image) return;
  const lat = props.image.latitude;
  const lng = props.image.longitude;
  const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
  window.open(url, '_blank');
}

// Keyboard navigation
function handleKeydown(e: KeyboardEvent) {
  if (!props.image) return;

  switch (e.key) {
    case 'Escape':
      emit('close');
      break;
    case 'ArrowLeft':
      if (hasPrevious.value) navigatePrev();
      break;
    case 'ArrowRight':
      if (hasNext.value) navigateNext();
      break;
  }
}

// Touch swipe handlers for mobile
function handleTouchStart(e: TouchEvent) {
  const touch = e.touches[0];
  touchStartX.value = touch.clientX;
  touchStartY.value = touch.clientY;
  isSwiping.value = true;
}

function handleTouchMove(e: TouchEvent) {
  if (!isSwiping.value) return;

  const touch = e.touches[0];
  const deltaX = touch.clientX - touchStartX.value;
  const deltaY = Math.abs(touch.clientY - touchStartY.value);

  // Only allow horizontal swipe if moving more horizontally than vertically
  if (Math.abs(deltaX) > deltaY) {
    e.preventDefault();
  }
}

function handleTouchEnd(e: TouchEvent) {
  if (!isSwiping.value) return;
  isSwiping.value = false;

  const touch = e.changedTouches[0];
  const deltaX = touch.clientX - touchStartX.value;
  const deltaY = Math.abs(touch.clientY - touchStartY.value);

  // Only trigger swipe if horizontal movement is significant and more than vertical
  if (Math.abs(deltaX) > SWIPE_THRESHOLD && Math.abs(deltaX) > deltaY) {
    if (deltaX > 0 && hasPrevious.value) {
      navigatePrev();
    } else if (deltaX < 0 && hasNext.value) {
      navigateNext();
    }
  }
}

// Preload adjacent images for smooth navigation
function preloadAdjacentImages() {
  if (!props.images || props.currentIndex === undefined) return;

  const preloadImage = (url: string) => {
    const img = new Image();
    img.src = url;
  };

  // Preload next image
  if (props.currentIndex < props.images.length - 1) {
    preloadImage(props.images[props.currentIndex + 1].image_url);
  }

  // Preload previous image
  if (props.currentIndex > 0) {
    preloadImage(props.images[props.currentIndex - 1].image_url);
  }
}

onMounted(() => {
  if (props.image) {
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', handleKeydown);

    // Setup touch events for swipe
    if (imageStageRef.value) {
      imageStageRef.value.addEventListener('touchstart', handleTouchStart, { passive: true });
      imageStageRef.value.addEventListener('touchmove', handleTouchMove, { passive: false });
      imageStageRef.value.addEventListener('touchend', handleTouchEnd, { passive: true });
    }

    setTimeout(() => {
      closeButtonRef.value?.focus();
    }, 100);

    preloadAdjacentImages();
  }
});

watch(
  () => props.image,
  (newVal, oldVal) => {
    if (newVal) {
      // Only reset loading state on initial open or if we want to show loading state
      // For navigation, we keep the previous image visible until the new one loads (no flicker)
      if (!oldVal) {
        isLoaded.value = false;
      }
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', handleKeydown);

      // Setup touch events for swipe
      if (imageStageRef.value) {
        imageStageRef.value.addEventListener('touchstart', handleTouchStart, { passive: true });
        imageStageRef.value.addEventListener('touchmove', handleTouchMove, { passive: false });
        imageStageRef.value.addEventListener('touchend', handleTouchEnd, { passive: true });
      }

      setTimeout(() => {
        closeButtonRef.value?.focus();
      }, 100);

      // Preload adjacent images
      preloadAdjacentImages();
    } else {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeydown);

      // Cleanup touch events
      if (imageStageRef.value) {
        imageStageRef.value.removeEventListener('touchstart', handleTouchStart);
        imageStageRef.value.removeEventListener('touchmove', handleTouchMove);
        imageStageRef.value.removeEventListener('touchend', handleTouchEnd);
      }
    }
  }
);

// Watch for navigation to preload adjacent images
watch(
  () => props.currentIndex,
  () => {
    preloadAdjacentImages();
  }
);

onUnmounted(() => {
  document.body.style.overflow = '';
  document.removeEventListener('keydown', handleKeydown);

  // Cleanup touch events
  if (imageStageRef.value) {
    imageStageRef.value.removeEventListener('touchstart', handleTouchStart);
    imageStageRef.value.removeEventListener('touchmove', handleTouchMove);
    imageStageRef.value.removeEventListener('touchend', handleTouchEnd);
  }
});

function onImageLoad() {
  isLoaded.value = true;
}

function handleError(event: Event) {
  const target = event.target as HTMLImageElement;
  target.src = IMAGE_CONFIG.PLACEHOLDER_URL;
  isLoaded.value = true;
}
</script>

<style scoped>
/* Modal Backdrop */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 12, 0.85); /* Darker backdrop */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1.5rem;
}

/* Container */
.modal-container {
  width: 100%;
  max-width: 950px;
  perspective: 1000px;
}

/* Main Card */
.modal-card {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 2rem;
  overflow: hidden;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  transform-style: preserve-3d;
  max-height: 85vh;
}

@media (min-width: 768px) {
  .modal-card {
    flex-direction: row;
    height: 600px;
  }
}

/* Image Stage */
.modal-image-stage {
  position: relative;
  background: #1a1a1a;
  flex: 1;
  min-height: 350px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 768px) {
  .modal-image-stage {
    flex: 1.3;
    height: 100%;
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
  object-fit: cover;
  opacity: 0;
  transform: scale(1.05);
  transition:
    opacity 0.6s ease,
    transform 0.6s cubic-bezier(0.2, 0, 0.2, 1);
}

.main-image.is-visible {
  opacity: 1;
  transform: scale(1);
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

/* Content Side */
.modal-content {
  flex: 1;
  background: #fffbf6; /* Very subtle cream */
  display: flex;
  flex-direction: column;
  padding: 2.5rem;
  position: relative;
}

/* Header */
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.cat-title {
  font-family: 'Nunito', sans-serif;
  font-size: 2.5rem;
  font-weight: 800;
  color: #2d2420;
  line-height: 1;
  margin-bottom: 0.75rem;
  letter-spacing: -0.02em;
}

.cat-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.location-badge {
  display: inline-flex;
  align-items: center;
  color: #a65d37;
  font-weight: 700;
  font-size: 0.95rem;
  font-family: 'Inter', sans-serif;
}

.date-text {
  color: #8d8d8d;
  font-size: 0.9rem;
  font-weight: 500;
  position: relative;
  padding-left: 1rem;
}

.date-text::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #ccc;
}

/* Close Button */
.close-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0ebe5;
  color: #5a4632;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.close-btn:hover {
  background: #e8dccf;
  transform: rotate(90deg);
  color: #a65d37;
}

/* Body */
.content-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  overflow-y: auto;
  padding-right: 0.5rem; /* Space for scrollbar */
}

/* Scrollbar styling */
.content-body::-webkit-scrollbar {
  width: 6px;
}
.content-body::-webkit-scrollbar-track {
  background: transparent;
}
.content-body::-webkit-scrollbar-thumb {
  background: #e0d6cc;
  border-radius: 3px;
}

.description-text {
  font-family: 'Inter', sans-serif;
  font-size: 1.05rem;
  line-height: 1.7;
  color: #5a4e47;
}

.description-placeholder {
  font-style: italic;
  color: #999;
}

.section-label {
  font-family: 'Nunito', sans-serif;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.1em;
  color: #a65d37;
  margin-bottom: 0.75rem;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-chip {
  padding: 0.4rem 1rem;
  background: #eaf0ee;
  color: #537c6d;
  border: 1px solid rgba(83, 124, 109, 0.1);
  border-radius: 100px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Inter', sans-serif;
}

.tag-chip:hover {
  background: #dce8e3;
  color: #3d5e51;
  transform: translateY(-1px);
}

/* Footer */
.content-footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.action-btn {
  width: 100%;
  padding: 1rem;
  border-radius: 1rem;
  font-family: 'Nunito', sans-serif;
  font-weight: 700;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.02em;
}

.action-btn.primary {
  background: #a65d37;
  color: white;
  border: none;
  box-shadow: 0 8px 20px rgba(166, 93, 55, 0.25);
}

.action-btn.primary:hover {
  background: #9a5029;
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(166, 93, 55, 0.3);
}

.action-btn.primary:active {
  transform: translateY(0);
}

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal-card {
  animation: modal-slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-fade-leave-active .modal-card {
  animation: modal-slide-down 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modal-slide-up {
  from {
    transform: translateY(40px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

@keyframes modal-slide-down {
  from {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  to {
    transform: translateY(20px) scale(0.95);
    opacity: 0;
  }
}
</style>
