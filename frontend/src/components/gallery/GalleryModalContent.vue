<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/authStore';
import { useSubscriptionStore } from '@/store/subscriptionStore';
import { showSuccess, showError } from '@/store/toast';
import { useCatsStore } from '@/store';
import { extractTags, getCleanDescription } from '@/store/catsStore';
import type { CatLocation } from '@/types/api';
import LikeButton from '@/components/social/LikeButton.vue';
import CommentList from '@/components/social/CommentList.vue';

const props = defineProps<{
  image: CatLocation | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const router = useRouter();
const authStore = useAuthStore();
const catsStore = useCatsStore();
const isSendingTreat = ref(false);
const selectedAmount = ref(1);

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

function handleUpdateLiked(val: boolean): void {
  if (props.image) {
    // eslint-disable-next-line vue/no-mutating-props
    props.image.liked = val;
  }
}

function handleUpdateLikesCount(val: number): void {
  if (props.image) {
    // eslint-disable-next-line vue/no-mutating-props
    props.image.likes_count = val;
  }
}

async function handleGiveTreat(): Promise<void> {
  if (!props.image) return;

  const amount = selectedAmount.value;
  if (!authStore.user || (authStore.user.treat_balance || 0) < amount) {
    showError('Not enough treats in your bag!');
    return;
  }

  isSendingTreat.value = true;
  const subscriptionStore = useSubscriptionStore();

  try {
    await subscriptionStore.giveTreat(props.image.id, amount);
    showSuccess(`You gave ${amount} treat(s)!`);
    // Balance update is handled by store now
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string };
    showError(e.response?.data?.detail || 'Failed to give treat');
  } finally {
    isSendingTreat.value = false;
  }
}

function searchByTag(tag: string): void {
  catsStore.setSearchQuery(`#${tag}`);
  emit('close');
  router.push({ path: '/map', query: { search: `#${tag}` } });
}

function openDirections(): void {
  if (!props.image) return;
  const lat = props.image.latitude;
  const lng = props.image.longitude;
  const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
  window.open(url, '_blank');
}
</script>

<template>
  <div class="modal-content">
    <!-- Mobile Drag Handle Visual -->
    <div class="block sm:hidden w-full flex justify-center pb-2">
      <div class="w-12 h-1.5 bg-gray-200/50 rounded-full"></div>
    </div>

    <!-- Header -->
    <div class="content-header">
      <div class="flex-1">
        <h3 id="modal-title" class="cat-title">Cat Details</h3>
        <div class="cat-meta flex items-center gap-4 flex-wrap">
          <button
            v-if="image?.location_name"
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

      <div class="flex items-center gap-2">
        <button class="close-btn desktop-close-btn" aria-label="Close" @click="$emit('close')">
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
    </div>

    <!-- Body -->
    <div class="content-body">
      <div class="description-section">
        <p v-if="cleanDescription" class="description-text">
          {{ cleanDescription }}
        </p>
        <p v-else class="description-placeholder">No description available for this spot.</p>
      </div>

      <!-- Social Interactions -->
      <div class="social-section mt-4 mb-6 border-b border-cream-dark/50 pb-6">
        <div class="flex flex-col gap-4">
          <!-- Unified Interaction Row -->
          <div class="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6">
            <!-- Left: Like Button (Full width on mobile, auto on desktop) -->
            <div class="flex items-center justify-start">
              <LikeButton
                v-if="image"
                :photo-id="image.id"
                :initial-count="image.likes_count"
                :initial-liked="image.liked"
                class="scale-110 sm:scale-100 origin-left"
                @update:liked="handleUpdateLiked"
                @update:count="handleUpdateLikesCount"
              />
            </div>

            <!-- Right: Treat Interaction (Responsive layout) -->
            <div
              v-if="image && authStore.isAuthenticated && authStore.user?.id !== image.user_id"
              class="flex items-center justify-between gap-3 sm:gap-4 flex-1"
            >
              <!-- Quantity Selector -->
              <div class="flex bg-brown/5 rounded-full p-1 gap-1">
                <button
                  v-for="amt in [1, 5, 10, 50]"
                  :key="amt"
                  class="w-8 h-8 sm:w-8 sm:h-8 flex items-center justify-center text-[11px] sm:text-xs font-bold rounded-full transition-all duration-200"
                  :class="
                    selectedAmount === amt
                      ? 'bg-white text-terracotta shadow-sm scale-105 ring-1 ring-black/5'
                      : 'text-brown/40 hover:text-brown hover:bg-white/50'
                  "
                  @click="selectedAmount = amt"
                >
                  {{ amt }}
                </button>
              </div>

              <!-- Action Button -->
              <button
                class="flex-1 max-w-[140px] sm:max-w-[160px] h-9 bg-terracotta hover:bg-terracotta-dark text-white font-bold rounded-full shadow-sm hover:shadow-md shadow-terracotta/20 active:scale-95 transition-all flex items-center justify-center group"
                :disabled="isSendingTreat"
                @click="handleGiveTreat"
              >
                <span v-if="!isSendingTreat" class="text-xs sm:text-sm tracking-wide px-2">
                  Give Treats
                </span>
                <span v-else class="flex gap-1">
                  <span class="w-1 h-1 bg-white rounded-full animate-bounce"></span>
                  <span class="w-1 h-1 bg-white rounded-full animate-bounce delay-100"></span>
                  <span class="w-1 h-1 bg-white rounded-full animate-bounce delay-200"></span>
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Comments -->
      <CommentList v-if="image" :photo-id="image.id" />
    </div>
  </div>
</template>

<style scoped>
/* Content Side */
/* Content Side */
.modal-content {
  flex: 1;
  background: #fffcf9;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  overflow: hidden;
  position: relative;
  z-index: 10;
}

/* Mobile: Standard layout without overlap */
@media (max-width: 639px) {
  .modal-content {
    border-radius: 0;
    margin-top: 0;
    padding: 1.5rem;
    box-shadow: none;
  }
}

/* Tablet & Desktop: Standard layout */
@media (min-width: 640px) {
  .modal-content {
    margin-top: 0;
    border-radius: 0;
    box-shadow: none;
    padding: 2rem;
  }
}

@media (min-width: 900px) {
  .modal-content {
    /* Removed fixed max-width to allow filling the container */
    padding: 2.5rem 2rem;
  }
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
  font-size: 1.75rem;
  font-weight: 800;
  color: #2d2420;
  line-height: 1.2;
  margin-bottom: 0.5rem;
  word-break: break-word; /* Ensure long names don't overflow */
}

@media (max-width: 639px) {
  .cat-title {
    font-size: 1.5rem; /* Smaller title on mobile */
  }
}

.cat-meta {
  font-size: 0.875rem;
  color: #8c7e7a;
}

.location-badge {
  color: #d97757;
  font-weight: 700;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.date-text {
  font-weight: 400;
  position: relative;
  padding-left: 1rem;
}

.date-text::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #d6ccc2;
}

/* Tags */
.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-chip-small {
  font-size: 0.75rem;
  font-weight: 600;
  color: #7a9e7e;
  background: rgba(122, 158, 126, 0.1);
  padding: 0.25rem 0.6rem;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s;
}

.tag-chip-small:hover {
  background: rgba(122, 158, 126, 0.2);
  transform: translateY(-1px);
}

/* Close Button */
.close-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex; /* Flex center to align SVG */
  align-items: center;
  justify-content: center;
  color: #8c7e7a;
  background: transparent;
  transition: all 0.2s;
  cursor: pointer;
}

.close-btn:hover {
  background: rgba(45, 36, 32, 0.05);
  color: #2d2420;
  transform: rotate(90deg);
}

/* Body */
.content-body {
  overflow-y: auto;
  flex: 1;
  padding-right: 0.5rem; /* Space for scrollbar on desktop */
  /* Firefox */
  scrollbar-width: thin;
  scrollbar-color: rgba(166, 93, 55, 0.2) transparent;
  scroll-behavior: smooth;
}

/* Hide scrollbar for Chrome, Safari and Opera on mobile */
@media (max-width: 768px) {
  .content-body {
    padding-right: 0;
    scrollbar-width: none;
  }
}
@media (min-width: 769px) {
  .content-body::-webkit-scrollbar {
    width: 5px;
  }
  .content-body::-webkit-scrollbar-track {
    background: transparent;
  }
  .content-body::-webkit-scrollbar-thumb {
    background-color: rgba(166, 93, 55, 0.2);
    border-radius: 20px;
    transition: background-color 0.3s ease;
  }
  .content-body::-webkit-scrollbar-thumb:hover {
    background-color: rgba(166, 93, 55, 0.5);
  }
}

.description-section {
  margin-bottom: 1.5rem;
}

.description-text {
  font-size: 1rem;
  line-height: 1.6;
  color: #5c504a;
  white-space: pre-wrap;
}

/* Comments */
.comment-input-area {
  background: white;
  border: 1px solid #f0e6e0;
  border-radius: 1rem;
  padding: 1rem;
  margin-top: auto; /* Push to bottom if space permits */
}

/* Ensure placeholder text is readable */
textarea::placeholder {
  color: #b0a6a0;
}
@media (max-width: 899px) {
  .desktop-close-btn {
    display: none;
  }
}
</style>
