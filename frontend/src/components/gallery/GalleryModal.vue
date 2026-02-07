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
        <div class="modal-container" @click.stop>
          <div class="modal-card">
            <!-- Left Side: Image Stage -->
            <div ref="imageStageRef" class="modal-image-stage">
              <!-- Loading State -->
              <div v-if="!isLoaded" class="loading-skeleton">
                <SkeletonLoader width="100%" height="100%" border-radius="0" />
              </div>

              <!-- Blurred Background for gaps -->
              <div class="blurred-bg" :style="{ backgroundImage: `url(${image.image_url})` }"></div>

              <!-- Main Image -->
              <!-- Main Image -->
              <div
                v-if="hasError"
                class="error-state flex flex-col items-center justify-center p-8 text-center text-white/60"
              >
                <img
                  src="/cat-illustration.png"
                  alt="No image available"
                  class="w-48 h-auto opacity-40 mb-4 grayscale"
                />
                <p class="font-heading text-xl">Image Not Found</p>
                <p class="text-sm mt-2 opacity-70">This spot's photo seems to be hiding.</p>
              </div>
              <img
                v-else
                :src="image.image_url"
                :alt="image.location_name ? `A cat at ${image.location_name}` : 'A cat'"
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
                aria-label="Previous"
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
                aria-label="Next"
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
                <div class="flex-1">
                  <h3 id="modal-title" class="cat-title">Cat Details</h3>
                  <div class="cat-meta flex items-center gap-4 flex-wrap">
                    <button
                      v-if="image.location_name"
                      class="location-badge hover:text-terracotta-dark transition-colors group flex items-center"
                      title="Open in Google Maps"
                      @click="openDirections"
                    >
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.5"
                        class="mr-1.5 group-hover:scale-110 transition-transform"
                      >
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                        <circle cx="12" cy="10" r="3" />
                      </svg>
                      {{ image.location_name }}
                    </button>
                    <span v-if="dateFormatted" class="date-text">{{ dateFormatted }}</span>
                  </div>

                  <!-- Tags moved to header -->
                  <div v-if="imageTags.length > 0" class="tags-list mt-3">
                    <button
                      v-for="tag in imageTags"
                      :key="tag"
                      class="tag-chip-small"
                      @click="searchByTag(tag)"
                    >
                      #{{ tag }}
                    </button>
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

                <!-- Social Interactions -->
                <div class="social-section mt-0 mb-2 border-b border-cream-dark/50 pb-2">
                  <div class="flex items-center justify-between">
                    <LikeButton
                      v-if="image"
                      :photo-id="image.id"
                      :initial-count="image.likes_count"
                      :initial-liked="image.liked"
                    />

                    <button
                      v-if="
                        image && authStore.isAuthenticated && authStore.user?.id !== image.user_id
                      "
                      class="treat-btn-new group"
                      :class="{ 'is-loading': isSendingTreat }"
                      :disabled="isSendingTreat"
                      @click="handleGiveTreat"
                    >
                      <div class="treat-visual-container">
                        <img src="/give-treat.png" alt="Give Treat" class="treat-main-img" />
                        <div v-if="isSendingTreat" class="loader-overlay">
                          <span class="loader-spinner"></span>
                        </div>
                        <!-- Treat Balance Indicator (Badge-like) -->
                        <div v-if="!isSendingTreat && authStore.user" class="treat-count-badge">
                          {{ authStore.user.treat_balance || 0 }}
                        </div>
                      </div>
                      <span class="treat-label">Give Treat</span>
                    </button>
                  </div>
                </div>

                <!-- Comments -->
                <CommentList v-if="image" :photo-id="image.id" />
              </div>
            </div>
          </div>
        </div>
      </dialog>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
import { useCatsStore } from '@/store';
import { useAuthStore } from '@/store/authStore';
import { useSubscriptionStore } from '@/store/subscriptionStore';
import { TreatsService } from '@/services/treatsService';
import { showSuccess, showError } from '@/store/toast';
import { extractTags, getCleanDescription } from '@/store/catsStore';
import type { CatLocation } from '@/types/api';
import { IMAGE_CONFIG } from '@/utils/constants';

import LikeButton from '@/components/social/LikeButton.vue';
import CommentList from '@/components/social/CommentList.vue';
import { supabase } from '@/lib/supabase';

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
const authStore = useAuthStore();
const isSendingTreat = ref(false);

async function handleGiveTreat() {
  if (!props.image) return;

  // Debug: Check auth state
  // console.log('Handling Give Treat. Authenticated:', authStore.isAuthenticated);

  isSendingTreat.value = true;
  const subscriptionStore = useSubscriptionStore();

  try {
    await subscriptionStore.giveTreat(props.image.id, 1);
    showSuccess('You gave a treat!');

    // Balance update is handled by store now
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string };
    showError(e.response?.data?.detail || 'Failed to give treat');
  } finally {
    isSendingTreat.value = false;
  }
}

const closeButtonRef = ref<HTMLButtonElement | null>(null);
const imageStageRef = ref<HTMLDivElement | null>(null);
const isLoaded = ref(false);
const hasError = ref(false);

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

// Event listener management
function setupListeners() {
  document.body.style.overflow = 'hidden';
  document.addEventListener('keydown', handleKeydown);

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

function cleanupListeners() {
  document.body.style.overflow = '';
  document.removeEventListener('keydown', handleKeydown);

  if (imageStageRef.value) {
    imageStageRef.value.removeEventListener('touchstart', handleTouchStart);
    imageStageRef.value.removeEventListener('touchmove', handleTouchMove);
    imageStageRef.value.removeEventListener('touchend', handleTouchEnd);
  }
}

let balanceChannel: any = null;

function setupBalanceRealtime() {
  if (!authStore.user?.id) return;

  balanceChannel = supabase
    .channel(`user_balance_${authStore.user.id}`)
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'users',
        filter: `id=eq.${authStore.user.id}`,
      },
      (payload) => {
        if (payload.new && typeof payload.new.treat_balance === 'number' && authStore.user) {
          authStore.user.treat_balance = payload.new.treat_balance;
        }
      }
    )
    .subscribe();
}

onMounted(() => {
  if (props.image) {
    setupListeners();
  }
  setupBalanceRealtime();
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

// Watch for navigation to preload adjacent images
watch(
  () => props.currentIndex,
  () => {
    preloadAdjacentImages();
  }
);

watch(
  () => authStore.user?.id,
  (newId) => {
    if (balanceChannel) {
      supabase.removeChannel(balanceChannel);
    }
    if (newId) {
      setupBalanceRealtime();
    }
  }
);

onUnmounted(() => {
  cleanupListeners();
  if (balanceChannel) {
    supabase.removeChannel(balanceChannel);
  }
});

function onImageLoad() {
  isLoaded.value = true;
}

function handleError(event: Event) {
  hasError.value = true;
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
  border: none; /* Reset default dialog border */
  margin: 0; /* Reset default dialog margin */
  width: 100vw; /* Ensure full width */
  height: 100vh; /* Ensure full height */
  max-width: 100vw;
  max-height: 100vh;
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
    min-height: 500px;
    max-height: 90vh;
    height: auto;
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
  position: relative;
  z-index: 2;
  opacity: 0;
  transform: scale(1.05);
  transition:
    opacity 0.6s ease,
    transform 0.6s cubic-bezier(0.2, 0, 0.2, 1);
}

.blurred-bg {
  position: absolute;
  inset: -20px;
  background-size: cover;
  background-position: center;
  filter: blur(40px) brightness(0.7);
  opacity: 0.6;
  z-index: 1;
  transform: scale(1.1);
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
  padding: 1.5rem;
  position: relative;
}

/* Header */
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.25rem;
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
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
}

.location-badge:hover {
  color: #8a4a2a;
  text-decoration: underline;
}

.date-text {
  color: #6b7280;
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
  gap: 1.25rem;
  overflow-y: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.content-body::-webkit-scrollbar {
  display: none;
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
  color: #6b7280;
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

.tag-chip-small {
  padding: 0.25rem 0.6rem;
  background: #eaf0ee;
  color: #537c6d;
  border: 1px solid rgba(83, 124, 109, 0.1);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Inter', sans-serif;
}

.tag-chip-small:hover {
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

.action-btn-mini {
  padding: 0.6rem 1.25rem;
  border-radius: 0.75rem;
  font-family: 'Nunito', sans-serif;
  font-weight: 700;
  font-size: 0.9rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.02em;
  border: none;
}

.action-btn-mini.primary {
  background: #a65d37;
  color: white;
  box-shadow: 0 4px 12px rgba(166, 93, 55, 0.2);
}

.action-btn-mini.primary:hover {
  background: #9a5029;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(166, 93, 55, 0.25);
}

.action-btn-compact {
  padding: 0.35rem 0.75rem;
  border-radius: 0.5rem;
  font-family: 'Nunito', sans-serif;
  font-weight: 700;
  font-size: 0.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 0.01em;
  border: none;
}

.action-btn-compact.primary {
  background: #a65d37;
  color: white;
  box-shadow: 0 2px 8px rgba(166, 93, 55, 0.15);
}

.action-btn-compact.primary:hover {
  background: #9a5029;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(166, 93, 55, 0.2);
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

/* Treat Button Enhancements */
.treat-btn-new {
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.treat-visual-container {
  position: relative;
  width: 48px;
  height: 48px;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  background: white;
  border-radius: 12px;
  padding: 4px;
  border: 1.5px solid #f0ebe5;
  box-shadow: 0 4px 12px rgba(166, 93, 55, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.treat-main-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.3s ease;
}

.treat-btn-new:hover:not(:disabled) .treat-visual-container {
  transform: translateY(-3px) scale(1.02);
  border-color: #a65d37;
  background: #fffcf9;
  box-shadow: 0 8px 20px rgba(166, 93, 55, 0.15);
}

.treat-btn-new:hover:not(:disabled) .treat-main-img {
  transform: rotate(12deg) scale(1.1);
}

.treat-btn-new:active:not(:disabled) .treat-visual-container {
  transform: translateY(0) scale(0.95);
}

.treat-label {
  margin-top: 8px;
  font-size: 0.65rem;
  font-weight: 800;
  color: #a65d37;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.6;
  transition: all 0.3s ease;
}

.treat-btn-new:hover .treat-label {
  opacity: 1;
  transform: translateY(1px);
}

.loader-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
  z-index: 5;
}

.loader-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid #a65d37;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spinner 0.8s linear infinite;
}

@keyframes spinner {
  to {
    transform: rotate(360deg);
  }
}

.treat-count-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #d67a4f;
  color: white;
  font-size: 0.7rem;
  font-weight: 900;
  min-width: 20px;
  padding: 2px 6px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(214, 122, 79, 0.4);
  z-index: 2;
  border: 2px solid white;
}

.treat-btn-new.is-loading {
  cursor: wait;
}

.treat-btn-new.is-loading .treat-main-img {
  opacity: 0.7;
}

/* Success "Pop" effect could be added here if we had a dedicated success state */
</style>
