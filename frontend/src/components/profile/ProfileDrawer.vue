<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useProfileData } from '@/composables/useProfileData';
import { GhibliLoader, ErrorState } from '@/components/ui';
import ProfileHeader from './ProfileHeader.vue';
import ProfileGallery from './ProfileGallery.vue';
import type { CatLocation } from '@/types/api';

const props = defineProps<{
  isOpen: boolean;
  userId: string | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const { t } = useI18n();

// Use the same profile logic as ProfileView
const {
  viewedUser,
  loadingUser,
  isOwnProfile,
  uploads,
  uploadsLoading,
  uploadsError,
  loadProfileData,
} = useProfileData();

const drawerRef = ref<HTMLElement | null>(null);

const close = (): void => {
  emit('close');
};

// Custom loader to fetch data when ID changes
const fetchData = async (): Promise<void> => {
  if (props.userId) {
    // We need to manually set the route param or simulate it for useProfileData
    // Since useProfileData relies on route.params.id, we can temporarily mock or adapt
    // For now, let's assume we might need a small adjustment in useProfileData
    // but we'll try to use it as is if we can.
    await loadProfileData(undefined, props.userId);
  }
};

watch(
  () => props.userId,
  (newId) => {
    if (newId && props.isOpen) {
      loadProfileData(undefined, newId);
    }
  }
);

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen && props.userId) {
      loadProfileData(undefined, props.userId);
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  }
);

// Handle ESC key
const handleEsc = (e: KeyboardEvent): void => {
  if (e.key === 'Escape' && props.isOpen) {
    close();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleEsc);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleEsc);
  document.body.style.overflow = '';
});

// We need to provide a way to open images from the drawer too
const selectedImage = ref<CatLocation | null>(null);
const openImage = (image: CatLocation): void => {
  selectedImage.value = image;
  // For now, maybe just redirect or show a nested modal?
  // Let's stick to redirecting to the full profile for image details to keep it simple
  // or just emitted to parent.
};
</script>

<template>
  <div class="fixed inset-0 z-[100] pointer-events-none">
    <!-- Backdrop -->
    <Transition
      enter-active-class="transition-opacity duration-500 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-400 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="absolute inset-0 bg-stone-900/60 backdrop-blur-[2px] pointer-events-auto transition-all duration-300"
        @click="close"
      ></div>
    </Transition>

    <!-- Drawer Panel -->
    <Transition
      enter-active-class="transition-transform duration-500 cubic-bezier(0.16, 1, 0.3, 1)"
      enter-from-class="translate-x-full"
      enter-to-class="translate-x-0"
      leave-active-class="transition-transform duration-400 ease-in"
      leave-from-class="translate-x-0"
      leave-to-class="translate-x-full"
    >
      <div
        v-if="isOpen"
        ref="drawerRef"
        class="absolute top-0 right-0 h-full w-full max-w-2xl bg-stone-50 shadow-2xl pointer-events-auto flex flex-col border-l border-white/20"
      >
        <!-- Header / Close Button -->
        <div
          class="px-6 py-5 flex justify-between items-center bg-white/80 backdrop-blur-xl border-b border-stone-200/60 shrink-0 sticky top-0 z-20"
        >
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-6 bg-terracotta rounded-full"></div>
            <h2 class="font-heading font-bold text-brown text-xl tracking-tight">
              {{ viewedUser?.name || t('profile.title') }}
            </h2>
          </div>
          <button
            class="p-2.5 hover:bg-stone-100 rounded-xl transition-all duration-200 text-stone-400 hover:text-stone-600 hover:rotate-90 group"
            @click="close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6 stroke-[2.5]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Content Area -->
        <div class="flex-1 overflow-y-auto custom-scrollbar p-4 sm:p-6 lg:p-8">
          <div v-if="loadingUser && !viewedUser" class="h-64 flex items-center justify-center">
            <GhibliLoader :text="t('profile.gatheringMemories')" />
          </div>

          <ErrorState v-else-if="uploadsError" :message="uploadsError" @retry="fetchData" />

          <div v-else-if="viewedUser" class="space-y-8 animate-fade-in">
            <!-- Reuse ProfileHeader -->
            <div class="bg-white/40 rounded-[2.5rem] p-3 border border-white/60 shadow-sm">
              <ProfileHeader
                :name="viewedUser.name"
                :username="viewedUser.username"
                :bio="viewedUser.bio"
                :picture="viewedUser.picture"
                :created-at="viewedUser.created_at"
                :uploads-count="uploads.length"
                :is-pro="viewedUser.is_pro"
                :treat-balance="viewedUser.treat_balance || viewedUser.total_treats_received"
                :is-own-profile="isOwnProfile"
                is-drawer
                class="!mb-0 !shadow-none !border-none !rounded-[2rem]"
              />
            </div>

            <!-- Gallery Section -->
            <ProfileGallery
              :uploads="uploads"
              :is-loading="uploadsLoading"
              :error="uploadsError"
              :is-own-profile="isOwnProfile"
              :user-name="viewedUser.name"
              @open-image="openImage"
              @retry="fetchData"
            />

            <!-- Link to Full Profile -->
            <div class="pt-8 pb-12 flex justify-center">
              <router-link
                :to="`/profile/${viewedUser.username || viewedUser.id}`"
                class="group relative inline-flex items-center gap-3 px-10 py-4 bg-brown text-white rounded-full font-bold transition-all duration-300 shadow-[0_10px_20px_-5px_rgba(62,44,40,0.3)] hover:shadow-[0_20px_35px_-10px_rgba(62,44,40,0.4)] hover:-translate-y-1 active:scale-95 overflow-hidden"
              >
                <span class="relative z-10">{{
                  t('profile.viewFullProfile') || 'View Full Profile'
                }}</span>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 relative z-10 transition-transform group-hover:translate-x-1"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
                <div
                  class="absolute inset-0 bg-gradient-to-r from-terracotta to-brown opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                ></div>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.bg-glass {
  background: rgba(255, 255, 255, 0.7);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #d6d3d1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #a8a29e;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.animate-fade-in {
  animation: fade-in 0.5s ease-out forwards;
}
</style>
