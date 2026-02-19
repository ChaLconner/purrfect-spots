<template>
  <transition
    enter-active-class="transition-all duration-500 ease-out"
    leave-active-class="transition-all duration-300 ease-in"
    enter-from-class="opacity-0 translate-x-full"
    leave-to-class="opacity-0 translate-x-12"
  >
    <div
      v-if="cat"
      class="fixed inset-0 z-[150] flex justify-end items-stretch pointer-events-auto"
      @click="$emit('close')"
    >
      <div class="minimal-panel w-full max-w-[450px]" @click.stop>
        <!-- Close Action (Top Corner) -->
        <button class="close-x-btn" :aria-label="t('map.modal.ariaClose')" @click="$emit('close')">
          <svg
            viewBox="0 0 24 24"
            width="24"
            height="24"
            stroke="currentColor"
            stroke-width="2.5"
            fill="none"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <!-- Report Button (Top Left) -->
        <button
          v-if="cat && (!authStore.isAuthenticated || authStore.user?.id !== cat.user_id)"
          class="report-btn group"
          :aria-label="t('map.modal.ariaReport')"
          :title="t('map.modal.reportTitle')"
          @click="handleReportClick"
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
            class="group-hover:text-white"
          >
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
            <line x1="4" y1="22" x2="4" y2="15" />
          </svg>
        </button>

        <div class="panel-inner custom-scrollbar">
          <!-- Image Section -->
          <div class="image-wrapper">
            <img
              :src="cat.image_url"
              :alt="cat.location_name || t('galleryPage.modal.aCat')"
              class="main-image"
              loading="lazy"
            />
          </div>

          <!-- Content Section -->
          <div class="details-section">
            <div class="location-label">
              {{ cat.location_name }}
            </div>

            <h2 class="cat-name">{{ t('map.modal.catSpotted') }}</h2>

            <div class="description-text font-zen-maru">
              {{ cleanDescription || t('map.modal.defaultDescription') }}
            </div>

            <div v-if="tags.length > 0" class="tags-row mb-6">
              <span v-for="tag in tags" :key="tag" class="tag-text">#{{ tag }}</span>
            </div>

            <!-- Interaction Row -->
            <div class="mt-8 pt-6 border-t border-stone-100">
              <div class="flex flex-col gap-6">
                <!-- Like and Treat Row -->
                <div class="flex items-center gap-4">
                  <LikeButton
                    v-if="cat"
                    :photo-id="cat.id"
                    :initial-count="cat.likes_count || 0"
                    :initial-liked="cat.liked"
                    class="scale-110 origin-left"
                    @update:liked="cat!.liked = $event"
                    @update:count="cat!.likes_count = $event"
                  />

                  <div class="h-8 w-px bg-stone-100 mx-2"></div>

                  <div class="flex-1 flex items-center justify-between gap-3">
                    <div class="flex bg-stone-100 rounded-full p-1 gap-1">
                      <button
                        v-for="amt in [1, 5, 10]"
                        :key="amt"
                        class="w-8 h-8 flex items-center justify-center text-xs font-bold rounded-full transition-all"
                        :class="
                          selectedAmount === amt
                            ? 'bg-white text-brown shadow-sm ring-1 ring-black/5'
                            : 'text-stone-400 hover:text-stone-600'
                        "
                        @click="selectedAmount = amt"
                      >
                        {{ amt }}
                      </button>
                    </div>

                    <button
                      v-if="!authStore.isAuthenticated || authStore.user?.id !== cat.user_id"
                      class="flex-1 h-10 bg-brown hover:bg-brown-dark text-white text-sm font-bold rounded-full shadow-sm hover:shadow-md transition-all flex items-center justify-center disabled:opacity-50"
                      :disabled="isSendingTreat"
                      @click="handleGiveTreat"
                    >
                      <span v-if="!isSendingTreat">{{ t('map.modal.giveTreats') }}</span>
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
          </div>
        </div>

        <div class="footer-action">
          <button class="elegant-btn" @click="$emit('get-directions', cat)">
            {{ t('map.modal.getDirections') }}
          </button>
        </div>
      </div>
    </div>
  </transition>

  <ReportModal
    v-if="cat"
    :is-open="isReportOpen"
    :photo-id="cat.id"
    @close="isReportOpen = false"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import type { CatLocation } from '@/types/api';
import { extractTags, getCleanDescription } from '@/store/catsStore';
import { useAuthStore } from '@/store/authStore';
import { useSubscriptionStore } from '@/store/subscriptionStore';
import { useToast } from '@/components/toast/use-toast';
import LikeButton from '@/components/social/LikeButton.vue';
import ReportModal from '@/components/ui/ReportModal.vue';

const props = defineProps<{
  cat: CatLocation | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'tag-click', tag: string): void;
  (e: 'get-directions', cat: CatLocation): void;
}>();

const { t } = useI18n();
const authStore = useAuthStore();
const subscriptionStore = useSubscriptionStore();
const { toast } = useToast();
const selectedAmount = ref(1);
const isSendingTreat = ref(false);
const isReportOpen = ref(false);

function handleReportClick() {
  if (!authStore.isAuthenticated) {
    toast({
      description: t('map.signInToReport'),
      variant: 'destructive',
    });
    return;
  }
  isReportOpen.value = true;
}

const cleanDescription = computed(() => {
  if (!props.cat) return '';
  const desc = getCleanDescription(props.cat.description);
  return desc === '-' ? '' : desc;
});

const tags = computed(() => {
  if (!props.cat) return [];
  return extractTags(props.cat.description);
});

async function handleGiveTreat() {
  if (!props.cat) return;

  if (!authStore.isAuthenticated) {
    toast({
      description: t('profile.signInToGiveTreats'),
      variant: 'destructive',
    });
    return;
  }

  if ((authStore.user?.treat_balance || 0) < selectedAmount.value) {
    toast({
      description: t('galleryPage.modal.notEnoughTreats'),
      variant: 'destructive',
    });
    return;
  }

  isSendingTreat.value = true;
  try {
    await subscriptionStore.giveTreat(props.cat.id, selectedAmount.value);
    toast({
      description: t('galleryPage.modal.treatsGiven', { amount: selectedAmount.value }),
      variant: 'success',
    });
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string };
    toast({
      description: e.response?.data?.detail || e.message || t('profile.treatFailed'),
      variant: 'destructive',
    });
  } finally {
    isSendingTreat.value = false;
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    emit('close');
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.minimal-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: calc(100vh - 3rem);
  margin: 1.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 1.5rem;
  box-shadow: -10px 20px 40px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

/* Close Button - Simple X */
.close-x-btn {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  z-index: 20;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: none;
  border: none;
  cursor: pointer;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  transition: opacity 0.2s;
}

.close-x-btn:hover {
  opacity: 0.7;
}

.panel-inner {
  flex-grow: 1;
  overflow-y: auto;
}

/* Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f3f4f6;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #f3f4f6;
  border-radius: 10px;
}

/* Image */
.image-wrapper {
  width: 100%;
  aspect-ratio: 1/1;
  overflow: hidden;
}

.main-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Content */
.details-section {
  padding: 2rem;
}

.location-label {
  font-family: 'Quicksand', sans-serif;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--color-sage);
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.cat-name {
  font-family: 'Quicksand', sans-serif;
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-brown-dark);
  margin-bottom: 1.5rem;
  line-height: 1.2;
}

.description-text {
  font-size: 1rem;
  line-height: 1.6;
  color: #4b5563;
  margin-bottom: 1.5rem;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.tag-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: #9ca3af;
}

/* Action Button */
.footer-action {
  padding: 2rem;
  padding-top: 0;
}

.elegant-btn {
  width: 100%;
  padding: 1.25rem;
  background: var(--color-brown);
  border: none;
  border-radius: 1rem;
  color: white;
  font-family: 'Quicksand', sans-serif;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.3s ease;
}

.elegant-btn:hover {
  background: var(--color-brown-dark);
  box-shadow: 0 10px 20px rgba(139, 77, 45, 0.2);
  transform: translateY(-2px);
}

.elegant-btn:active {
  transform: translateY(0);
}

/* Report Button - Top Left */
.report-btn {
  position: absolute;
  top: 1.25rem;
  left: 1.25rem;
  z-index: 20;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: rgba(0, 0, 0, 0.2); /* Slightly darker for visibility on images */
  border-radius: 50%;
  border: none;
  cursor: pointer;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  transition: all 0.2s;
  backdrop-filter: blur(2px);
}

.report-btn:hover {
  background: rgba(239, 68, 68, 0.8); /* Red on hover */
  transform: scale(1.1);
}

@media (max-width: 640px) {
  .minimal-panel {
    margin: 0;
    height: 100vh;
    border-radius: 0;
    max-width: 100%;
  }
}
</style>
