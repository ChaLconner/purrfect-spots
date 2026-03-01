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
      <div
        ref="modalContainer"
        class="relative flex flex-col w-full max-w-full sm:max-w-[450px] sm:m-6 h-screen sm:h-[calc(100vh-3rem)] bg-white sm:border sm:border-gray-200 sm:rounded-3xl shadow-[-10px_20px_40px_rgba(0,0,0,0.08)] overflow-hidden"
        tabindex="-1"
        @click.stop
        @keydown="handleKeydown"
      >
        <!-- Close Action (Top Corner) -->
        <button
          class="absolute top-5 right-5 z-20 w-10 h-10 flex items-center justify-center text-white bg-black/20 hover:bg-black/60 backdrop-blur-[4px] rounded-full border-none cursor-pointer drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)] transition-all duration-300 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 hover:scale-105"
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
          v-if="cat && (!authStore.isAuthenticated || authStore.user?.id !== cat.user_id)"
          class="report-btn group absolute top-5 left-5 z-20 w-10 h-10 flex items-center justify-center text-white bg-black/20 backdrop-blur-[4px] rounded-full border-none cursor-pointer drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)] transition-all duration-300 hover:bg-red-500/80 hover:scale-110 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:ring-offset-2"
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
          class="flex-grow overflow-y-auto [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-gray-100 [&::-webkit-scrollbar-thumb]:bg-gray-100 [&::-webkit-scrollbar-thumb]:rounded-full"
        >
          <!-- Image Section -->
          <div class="w-full aspect-square overflow-hidden">
            <img
              :src="cat.image_url"
              :alt="cat.location_name || t('galleryPage.modal.aCat')"
              class="w-full h-full object-cover"
              loading="lazy"
            />
          </div>

          <!-- Content Section -->
          <div class="p-8">
            <div
              class="font-accent text-[0.8rem] font-bold tracking-wider text-sage uppercase mb-2"
            >
              {{ cat.location_name }}
            </div>

            <h2 class="font-accent text-3xl font-extrabold text-[#5c4033] mb-6 leading-tight">
              {{ t('map.modal.catSpotted') }}
            </h2>

            <div class="text-base leading-relaxed text-gray-600 mb-6 font-zen-maru">
              {{ cleanDescription || t('map.modal.defaultDescription') }}
            </div>

            <div v-if="tags.length > 0" class="flex flex-wrap gap-3 mb-6">
              <span
                v-for="tag in tags"
                :key="tag"
                class="text-[0.85rem] font-semibold text-gray-400"
              >#{{ tag }}</span>
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
                        class="w-8 h-8 flex items-center justify-center text-xs font-bold rounded-full transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8b5a2b] focus-visible:ring-offset-2 active:scale-95"
                        :class="
                          selectedAmount === amt
                            ? 'bg-white text-[#8b5a2b] shadow-sm ring-1 ring-black/5 scale-105'
                            : 'text-stone-400 hover:text-stone-600 hover:scale-105 hover:bg-white/50'
                        "
                        @click="selectedAmount = amt"
                      >
                        {{ amt }}
                      </button>
                    </div>

                    <button
                      v-if="!authStore.isAuthenticated || authStore.user?.id !== cat.user_id"
                      class="flex-1 h-10 bg-[#8b5a2b] hover:bg-[#5c4033] text-white text-sm font-bold rounded-full shadow-sm hover:shadow-md transition-all duration-300 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8b5a2b] focus-visible:ring-offset-2 flex items-center justify-center disabled:opacity-50"
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

        <div class="p-8 pt-0">
          <button
            class="w-full p-5 bg-[#8b5a2b] hover:bg-[#5c4033] hover:shadow-[0_10px_20px_rgba(139,77,45,0.2)] hover:-translate-y-0.5 active:translate-y-px active:scale-[0.98] border-none rounded-2xl text-white font-accent text-sm font-bold tracking-widest cursor-pointer transition-all duration-300 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8b5a2b] focus-visible:ring-offset-2"
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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
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
const modalContainer = ref<HTMLElement | null>(null);
const previousFocus = ref<HTMLElement | null>(null);

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

function trapFocus(e: KeyboardEvent): void {
  if (!modalContainer.value) return;
  const focusableElements = modalContainer.value.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  if (focusableElements.length === 0) return;

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  if (e.shiftKey) {
    // Shift + Tab
    if (
      document.activeElement === firstElement ||
      document.activeElement === modalContainer.value
    ) {
      lastElement.focus();
      e.preventDefault();
    }
  } else {
    // Tab
    if (document.activeElement === lastElement) {
      firstElement.focus();
      e.preventDefault();
    }
  }
}

const handleKeydown = (e: KeyboardEvent): void => {
  if (e.key === 'Escape') {
    emit('close');
  } else if (e.key === 'Tab') {
    trapFocus(e);
  }
};

onMounted(() => {
  previousFocus.value = document.activeElement as HTMLElement;
  document.body.style.overflow = 'hidden';
  // Note: we let the global unmount handle keydown if we bounded it to document,
  // but since we bound it to the element now we don't strictly need document.addEventListener
  nextTick(() => {
    modalContainer.value?.focus();
  });
});

onUnmounted(() => {
  document.body.style.overflow = '';
  if (previousFocus.value) {
    previousFocus.value.focus();
  }
});
</script>
