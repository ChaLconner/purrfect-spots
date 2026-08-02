<template>
  <transition
    enter-active-class="transition-all duration-500 ease-out"
    leave-active-class="transition-all duration-300 ease-in"
    enter-from-class="opacity-0 translate-x-full"
    leave-to-class="opacity-0 translate-x-full"
  >
    <div
      v-if="cat"
      class="fixed inset-0 z-[150] flex justify-end items-stretch bg-black/20 pointer-events-auto"
      @click="$emit('close')"
    >
      <div
        ref="modalContainer"
        class="relative flex flex-col w-full max-w-full sm:max-w-[450px] sm:m-6 h-screen sm:h-[calc(100vh-3rem)] bg-white sm:border sm:border-gray-200 sm:rounded-3xl shadow-[-10px_20px_40px_rgba(0,0,0,0.08)] overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cat-detail-title"
        tabindex="-1"
        @click.stop
        @keydown="handleKeydown"
      >
        <!-- Close Action (Top Corner) -->
        <button
          class="absolute top-5 right-5 z-20 w-10 h-10 flex items-center justify-center text-white bg-black/20 hover:bg-black/60 backdrop-blur-[4px] rounded-full border-none cursor-pointer drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)] transition-all duration-300 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2"
          :aria-label="t('map.modal.ariaClose')"
          @click="$emit('close')"
        >
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
          v-if="canInteractWithCat"
          class="report-btn group absolute top-5 left-5 z-20 w-10 h-10 flex items-center justify-center text-white bg-black/20 backdrop-blur-[4px] rounded-full border-none cursor-pointer drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)] transition-all duration-300 hover:bg-red-500/80 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:ring-offset-2"
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

        <div
          class="min-h-0 flex-1 overflow-y-auto custom-scrollbar"
        >
          <!-- Image Section -->
          <div
            class="w-full aspect-[4/3] sm:aspect-square overflow-hidden bg-stone-100 flex items-center justify-center"
          >
            <img
              :src="catImageSrc"
              :alt="cat.location_name || t('galleryPage.modal.aCat')"
              class="w-full h-full object-cover"
              loading="lazy"
              @error="handleImageError"
            />
          </div>

          <!-- Content Section -->
          <div class="p-5 sm:p-8">
            <div
              class="font-accent text-sm font-bold tracking-wide text-sage mb-2 break-words"
            >
              {{ cat.location_name }}
            </div>

            <h2
              id="cat-detail-title"
              class="font-heading text-3xl font-extrabold text-wood-dark mb-6 leading-snug pt-0.5"
            >
              {{ t('map.modal.catSpotted') }}
            </h2>

            <div
              class="text-base leading-relaxed text-stone-600 mb-6 font-body break-words"
            >
              {{ cleanDescription || t('map.modal.defaultDescription') }}
            </div>

            <div v-if="tags.length > 0" class="flex flex-wrap gap-3 mb-6">
              <button
                v-for="tag in tags"
                :key="tag"
                type="button"
                class="text-xs font-semibold text-sage-dark hover:text-wood-brown focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wood-brown focus-visible:ring-offset-2 rounded-md"
                @click="emit('tag-click', tag)"
              >
                #{{ tag }}
              </button>
            </div>

            <!-- Interaction Row -->
            <div class="mt-8 pt-6 border-t border-stone-100">
              <div class="flex flex-col gap-6">
                <!-- Like and Treat Row -->
                <div class="flex flex-col sm:flex-row sm:items-center gap-4">
                  <LikeButton
                    v-if="cat"
                    :photo-id="cat.id"
                    :initial-count="cat.likes_count || 0"
                    :initial-liked="cat.liked"
                    class="scale-110 origin-left"
                    @update:liked="cat!.liked = $event"
                    @update:count="cat!.likes_count = $event"
                  />

                  <div class="hidden sm:block h-8 w-px bg-stone-100 mx-2"></div>

                  <div class="flex-1 flex items-center justify-between gap-3">
                    <div class="flex bg-stone-100 rounded-full p-1 gap-1">
                      <button
                        v-for="amt in [1, 5, 10]"
                        :key="amt"
                        class="w-8 h-8 flex items-center justify-center text-xs font-bold rounded-full transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wood-brown focus-visible:ring-offset-2 active:scale-95"
                        :class="
                          selectedAmount === amt
                            ? 'bg-white text-wood-brown shadow-sm ring-1 ring-black/5 scale-105'
                            : 'text-stone-400 hover:text-stone-600 hover:bg-white/50'
                        "
                        @click="selectedAmount = amt"
                      >
                        {{ amt }}
                      </button>
                    </div>

                    <button
                      v-if="canInteractWithCat"
                      class="flex-1 min-w-0 h-10 bg-wood-brown hover:bg-wood-dark text-white text-sm font-bold rounded-full shadow-sm transition-all duration-300 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wood-brown focus-visible:ring-offset-2 flex items-center justify-center disabled:opacity-50"
                      :disabled="isSendingTreat"
                      @click="handleGiveTreat"
                    >
                      <span v-if="!isSendingTreat">{{ t('map.modal.giveTreats') }}</span>
                      <span v-else class="flex gap-1">
                        <span class="sr-only">{{ t('map.modal.giveTreats') }}</span>
                        <span class="w-1 h-1 bg-white rounded-full animate-pulse"></span>
                        <span class="w-1 h-1 bg-white rounded-full animate-pulse delay-100"></span>
                        <span class="w-1 h-1 bg-white rounded-full animate-pulse delay-200"></span>
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="shrink-0 p-5 pt-3 sm:p-8 sm:pt-3 bg-white border-t border-stone-100">
          <button
            class="w-full p-4 bg-wood-brown hover:bg-wood-dark active:translate-y-px active:scale-[0.98] border-none rounded-2xl text-white font-heading text-sm font-bold tracking-widest cursor-pointer transition-all duration-300 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wood-brown focus-visible:ring-offset-2"
            @click="$emit('get-directions', cat)"
          >
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
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { CatLocation } from '@/types/api';
import { extractTags, getCleanDescription } from '@/stores/catsStore';
import { useAuthStore } from '@/stores/authStore';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { useToast } from '@/composables/useToast';
import { useModalFocus } from '@/composables/useModalFocus';
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
const modalContainer = ref<HTMLElement | null>(null);
const isImageError = ref(false);

const handleImageError = (): void => {
  isImageError.value = true;
};

const catImageSrc = computed(() => {
  if (isImageError.value || !props.cat?.image_url) {
    return '/cat-illustration.webp';
  }
  return props.cat.image_url;
});

const canInteractWithCat = computed(() => {
  if (!props.cat) return false;
  if (!authStore.isAuthenticated) return true;
  return authStore.user?.id !== props.cat.user_id;
});

const { handleKeydown } = useModalFocus(modalContainer, {
  onClose: () => emit('close'),
});

function handleReportClick(): void {
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

async function handleGiveTreat(): Promise<void> {
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
</script>
