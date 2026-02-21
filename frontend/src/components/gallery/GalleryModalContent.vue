<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/store/authStore';
import { useSubscriptionStore } from '@/store/subscriptionStore';
import { showSuccess, showError } from '@/store/toast';
import { useCatsStore } from '@/store';
import { extractTags, getCleanDescription } from '@/store/catsStore';
import type { CatLocation } from '@/types/api';
import LikeButton from '@/components/social/LikeButton.vue';
import CommentList from '@/components/social/CommentList.vue';
import ReportModal from '@/components/ui/ReportModal.vue';

const props = defineProps<{
  image: CatLocation | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const router = useRouter();
const { t } = useI18n();
const authStore = useAuthStore();
const catsStore = useCatsStore();
const isSendingTreat = ref(false);
const isReportOpen = ref(false);
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

// Robust visibility check for Give Treats button
const showGiveTreats = computed(() => {
  const result = (() => {
    // Safety check: if image is missing, hide
    if (!props.image) return false;

    // Unauthenticated users should see the button (to get prompted)
    if (!authStore.isAuthenticated) return true;

    // If auth user is missing ID (edge case), assume not owner -> Show
    if (!authStore.user?.id) return true;

    // If image has no user_id (edge case), assume not owner -> Show
    if (!props.image.user_id) return true;

    // Strict comparison of strings to prevent type mismatches
    return String(authStore.user.id) !== String(props.image.user_id);
  })();

  // LOGGING
  console.log('[GalleryModal] Visibility Calc:', {
    isAuthenticated: authStore.isAuthenticated, // Valid boolean?
    myId: authStore.user?.id,
    imgUserId: props.image?.user_id,
    match: String(authStore.user?.id) === String(props.image?.user_id),
    RESULT: result,
  });

  return result;
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

// Watch for image changes to log debug info

async function handleGiveTreat(): Promise<void> {
  if (!props.image) return;

  if (!authStore.isAuthenticated) {
    showError(t('galleryPage.modal.signInToTreat'));
    return;
  }

  const amount = selectedAmount.value;
  if ((authStore.user?.treat_balance || 0) < amount) {
    showError(t('galleryPage.modal.notEnoughTreats'));
    return;
  }

  isSendingTreat.value = true;
  const subscriptionStore = useSubscriptionStore();

  try {
    await subscriptionStore.giveTreat(props.image.id, amount);
    showSuccess(t('galleryPage.modal.treatsGiven', { amount }));
    // Balance update is handled by store now
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string };
    showError(e.response?.data?.detail || t('galleryPage.modal.treatFailed'));
  } finally {
    isSendingTreat.value = false;
  }
}

function searchByTag(tag: string): void {
  // Keep user in Gallery context when searching from Gallery
  catsStore.setGallerySearchQuery(tag);
  emit('close');
  // Update URL via router to reflect search, but stay on Gallery
  router.push({ name: 'Gallery', query: { q: tag } });
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
  <div
    class="flex flex-col bg-cream-bg p-5 sm:p-6 min-[900px]:py-6 min-[900px]:px-6 overflow-hidden overflow-x-hidden relative z-10 max-sm:rounded-none max-sm:mt-0 max-sm:shadow-none sm:mt-0 sm:rounded-none sm:shadow-none min-w-0 w-full"
  >
    <!-- Mobile Drag Handle Visual -->
    <div class="block sm:hidden w-full flex justify-center pb-2">
      <div class="w-12 h-1.5 bg-gray-200/50 rounded-full"></div>
    </div>

    <!-- Header -->
    <div class="flex justify-between items-start mb-5 gap-4">
      <div class="flex-1 min-w-0">
        <h3
          id="modal-title"
          class="font-nunito text-2xl sm:text-[1.5rem] font-extrabold text-brown-text leading-tight mb-2 break-words"
        >
          {{ $t('galleryPage.modal.catDetails') }}
        </h3>
        <div class="text-sm text-brown-meta flex flex-col gap-1.5 mt-1">
          <button
            v-if="image?.location_name"
            class="text-location-badge font-bold text-sm transition-all duration-300 hover:text-terracotta-dark flex items-center group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-terracotta focus-visible:ring-offset-2 rounded-md px-1 -mx-1 text-left"
            :title="$t('galleryPage.modal.openInMaps')"
            @click="openDirections"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              class="mr-1.5 flex-shrink-0 group-hover:scale-110 transition-transform duration-300"
            >
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            <span class="truncate">{{ image.location_name }}</span>
          </button>
          <span v-if="dateFormatted" class="font-normal text-date-bullet whitespace-nowrap">{{
            dateFormatted
          }}</span>
        </div>

        <!-- Tags moved to header -->
        <div v-if="imageTags.length > 0" class="flex flex-wrap gap-2 mt-4">
          <button
            v-for="tag in imageTags"
            :key="tag"
            class="text-xs font-semibold text-sage-pill bg-sage-pill-bg px-3 py-1.5 rounded-full cursor-pointer transition-all duration-300 hover:bg-sage-pill-bg-hover hover:-translate-y-0.5 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-pill focus-visible:ring-offset-2 active:scale-95"
            @click="searchByTag(tag)"
          >
            #{{ tag }}
          </button>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          class="w-10 h-10 rounded-full flex items-center justify-center text-brown-meta bg-transparent transition-all duration-300 cursor-pointer hover:bg-red-50 hover:text-red-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 active:scale-95"
          :title="$t('galleryPage.modal.reportContent')"
          @click="isReportOpen = true"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
            <line x1="4" y1="22" x2="4" y2="15" />
          </svg>
        </button>
        <button
          class="w-10 h-10 rounded-full flex items-center justify-center text-brown-meta bg-transparent transition-all duration-300 cursor-pointer hover:bg-brown-text/10 hover:text-brown-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brown-text active:scale-95 max-[899px]:hidden"
          :aria-label="$t('galleryPage.modal.close')"
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
    </div>

    <!-- Body: scrollable area -->
    <div
      class="overflow-y-auto overflow-x-hidden flex-1 -mr-2 pr-2 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-brown/25 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-brown/45"
    >
      <div class="mb-6">
        <p
          v-if="cleanDescription"
          class="text-base leading-[1.7] tracking-[0.01em] text-[#5c504a] whitespace-pre-wrap transition-opacity duration-300"
        >
          {{ cleanDescription }}
        </p>
        <p v-else class="text-base leading-relaxed text-[#5c504a] italic opacity-70">
          {{ $t('galleryPage.modal.noDescription') }}
        </p>
      </div>

      <!-- Social Interactions -->
      <div class="mt-4 mb-6 border-b border-cream-dark/50 pb-6">
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
              v-if="showGiveTreats"
              class="flex items-center justify-between gap-3 sm:gap-4 flex-1"
            >
              <!-- Quantity Selector -->
              <div class="flex bg-brown/5 rounded-full p-1 gap-1">
                <button
                  v-for="amt in [1, 5, 10, 50]"
                  :key="amt"
                  class="w-8 h-8 sm:w-9 sm:h-9 flex items-center justify-center text-[11px] sm:text-xs font-bold rounded-full transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-terracotta focus-visible:ring-offset-2 active:scale-95"
                  :class="
                    selectedAmount === amt
                      ? 'bg-white text-terracotta shadow-md scale-105 ring-1 ring-black/5'
                      : 'text-brown/50 hover:text-brown hover:bg-white/60 hover:scale-105'
                  "
                  @click="selectedAmount = amt"
                >
                  {{ amt }}
                </button>
              </div>

              <!-- Action Button -->
              <button
                class="flex-1 max-w-[140px] sm:max-w-[160px] h-9 sm:h-10 bg-terracotta hover:bg-terracotta-dark text-white font-bold rounded-full shadow-sm hover:shadow-md hover:shadow-terracotta/30 active:scale-95 transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-terracotta focus-visible:ring-offset-2 flex items-center justify-center group"
                :disabled="isSendingTreat"
                @click="handleGiveTreat"
              >
                <span v-if="!isSendingTreat" class="text-xs sm:text-sm tracking-wide px-2">
                  {{ $t('galleryPage.modal.giveTreats') }}
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

      <!-- Report Modal -->
      <ReportModal
        v-if="image"
        :is-open="isReportOpen"
        :photo-id="image.id"
        @close="isReportOpen = false"
      />
    </div>
  </div>
</template>
