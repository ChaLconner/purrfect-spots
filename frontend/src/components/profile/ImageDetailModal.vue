<script setup lang="ts">
import type { CatLocation } from '@/types/api';
import type { User } from '@/types/auth';
import { ref } from 'vue';
import { BaseCard } from '@/components/ui';
import ReportModal from '@/components/ui/ReportModal.vue';
import { useToast } from '@/components/toast/use-toast';
import { useI18n } from 'vue-i18n';
import { getAvatarFallback, handleAvatarError } from '@/utils/avatar';

const props = defineProps<{
  image: CatLocation | null;
  isOpen: boolean;
  user: User | null; // The owner of the photo
  currentUser: User | null; // The viewer
  isOwnProfile: boolean;
  isSendingTreat: boolean;
}>();

const emit = defineEmits<{
  close: [];
  'give-treat': [image: CatLocation];
  edit: [image: CatLocation];
  delete: [image: CatLocation];
}>();

const { toast } = useToast();
const { t, locale } = useI18n();

const handleGiveTreat = (): void => {
  if (props.image) {
    emit('give-treat', props.image);
  }
};

const isReportOpen = ref(false);

const handleReportClick = (): void => {
  if (!props.currentUser) {
    toast({
      description: t('map.signInToReport'),
      variant: 'destructive',
    });
    return;
  }
  isReportOpen.value = true;
};
</script>

<template>
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div
      v-if="isOpen && image"
      class="fixed inset-0 bg-stone-900/80 backdrop-blur-md z-[150] flex items-center justify-center p-4 md:p-8"
      @click="$emit('close')"
    >
      <BaseCard
        variant="white"
        padding="none"
        class="relative overflow-hidden shadow-2xl max-w-6xl w-full max-h-[95vh] md:max-h-[90vh] flex flex-col md:flex-row transform transition-all rounded-2xl md:rounded-3xl"
        @click.stop
      >
        <!-- Close Button (Minimalist) -->
        <button
          class="absolute top-3 right-3 md:top-6 md:right-6 z-20 text-stone-400 hover:text-brown bg-white/80 md:bg-transparent rounded-full md:rounded-none p-1.5 md:p-1 transition-colors cursor-pointer"
          @click="$emit('close')"
        >
          <svg class="w-6 h-6 md:w-8 md:h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <!-- Image Section -->
        <div
          class="w-full md:w-3/5 bg-stone-100 flex items-center justify-center relative overflow-hidden h-[40vh] sm:h-[45vh] md:h-auto group"
        >
          <!-- Main Image -->
          <img
            :src="image.image_url"
            class="w-full h-full object-cover z-10"
            :alt="image.description || 'A cat'"
          />
        </div>

        <!-- Details Section -->
        <div
          class="w-full md:w-2/5 bg-white flex flex-col h-auto md:h-auto relative overflow-y-auto"
        >
          <div class="p-4 sm:p-6 md:p-8 lg:p-10 flex flex-col h-full">
            <!-- Header: User Info -->
            <div class="flex items-center gap-3 md:gap-4 mb-4 md:mb-6 lg:mb-8 pt-0 md:pt-2">
              <img
                :src="user?.picture || getAvatarFallback(user?.name)"
                class="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-full object-cover border-2 border-stone-100 shadow-sm bg-stone-100"
                :alt="user?.name || t('profile.unknownUser')"
                @error="handleAvatarError($event, user?.name)"
              />
              <div>
                <h4 class="text-brown font-heading font-bold text-lg md:text-xl leading-none mb-1">
                  {{ user?.name || t('profile.unknownUser') }}
                </h4>
                <p
                  class="text-[10px] sm:text-xs text-stone-400 font-medium uppercase tracking-widest"
                >
                  {{ t('profile.uploaded') }}
                  {{ new Date(image.uploaded_at).toLocaleDateString(locale) }}
                </p>
              </div>
            </div>

            <!-- Content -->
            <div
              class="flex-grow overflow-y-auto custom-scrollbar pr-1 sm:pr-2 space-y-3 md:space-y-4"
            >
              <div>
                <h3
                  class="text-2xl sm:text-2xl md:text-3xl font-heading font-extrabold text-terracotta mb-2 leading-tight"
                >
                  {{ image.location_name || t('map.unknownSpot') }}
                </h3>
                <div class="h-1 w-20 bg-sage/30 rounded-full"></div>
              </div>

              <p
                v-if="image.description && image.description !== '-'"
                class="text-brown-light font-body leading-relaxed text-base sm:text-lg whitespace-pre-wrap"
              >
                {{ image.description }}
              </p>
              <p v-else class="text-stone-300 italic">{{ t('profile.noDescription') }}</p>
            </div>

            <!-- Footer Actions -->
            <div
              class="mt-4 sm:mt-6 md:mt-8 pt-4 sm:pt-5 md:pt-6 border-t border-stone-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0 text-stone-400 text-sm"
            >
              <span
                class="flex items-center text-brown-light font-medium bg-stone-50 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg text-xs sm:text-sm"
              >
                <svg
                  class="w-4 h-4 mr-2 text-terracotta"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
                {{ image.latitude ? t('profile.locationTagged') : t('profile.noLocation') }}
              </span>

              <!-- Action Buttons -->
              <div class="flex items-center gap-2 sm:gap-3">
                <!-- Give Treat Button (Only for other users' photos) -->
                <!-- Use currentUser to check auth status -->
                <button
                  v-if="!isOwnProfile"
                  class="treat-btn-mini group flex flex-col items-center"
                  :disabled="isSendingTreat"
                  @click="handleGiveTreat"
                >
                  <div
                    class="relative w-10 h-10 sm:w-11 sm:h-11 md:w-12 md:h-12 transition-transform hover:scale-110 active:scale-95"
                  >
                    <img
                      src="/give-treat.png"
                      :alt="t('profile.giveTreat')"
                      class="w-full h-full object-contain filter drop-shadow-sm"
                    />
                    <div
                      v-if="isSendingTreat"
                      class="absolute inset-0 flex items-center justify-center bg-white/40 rounded-full"
                    >
                      <div
                        class="w-4 h-4 border-2 border-terracotta border-t-transparent rounded-full animate-spin"
                      ></div>
                    </div>
                  </div>
                </button>

                <!-- Edit Button -->
                <button
                  v-if="isOwnProfile"
                  class="p-2 text-stone-400 hover:text-brown transition-colors rounded-full hover:bg-stone-50 cursor-pointer"
                  :title="t('profile.editDetails')"
                  @click="$emit('edit', image)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="w-5 h-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                    />
                  </svg>
                </button>

                <!-- Delete Button -->
                <button
                  v-if="isOwnProfile"
                  class="p-2 text-stone-400 hover:text-red-500 transition-colors rounded-full hover:bg-red-50 cursor-pointer"
                  :title="t('profile.deletePhoto')"
                  @click="$emit('delete', image)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="w-5 h-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>

                <!-- Report Button (Visible for non-owners) -->
                <button
                  v-if="!isOwnProfile"
                  class="p-2 text-stone-400 hover:text-red-500 transition-colors rounded-full hover:bg-red-50 cursor-pointer"
                  :title="t('profile.reportPhoto')"
                  @click="handleReportClick"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="w-5 h-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"
                    />
                    <line x1="4" y1="22" x2="4" y2="15" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>

      <!-- Report Modal -->
      <ReportModal
        v-if="image"
        :is-open="isReportOpen"
        :photo-id="image.id"
        @close="isReportOpen = false"
      />
    </div>
  </Transition>
</template>
