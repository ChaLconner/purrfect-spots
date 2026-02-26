<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../../store/authStore';
import MapIcon from '../icons/map.vue';
import UploadIcon from '../icons/upload.vue';
import GalleryIcon from '../icons/gallery.vue';
import TrophyIcon from '../icons/trophy.vue';
import ProfileIcon from '../icons/profile.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const isActive = (path: string): boolean => {
  return route.path === path;
};

// Handle Profile Navigation based on Auth state
const navigateToProfile = (): void => {
  if (authStore.isAuthenticated) {
    router.push('/profile');
  } else {
    router.push('/login');
  }
};
</script>

<template>
  <div class="fixed bottom-0 left-0 right-0 z-50 px-4 pb-4 pt-2 pointer-events-none xl:hidden">
    <nav
      class="backdrop-blur-md rounded-2xl shadow-lg border border-btn-shade-a pointer-events-auto max-w-md mx-auto bg-glass-cream"
    >
      <div class="flex justify-around items-center px-2 py-3">
        <!-- Map -->
        <router-link
          to="/map"
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="
            isActive('/map') || isActive('/')
              ? 'text-btn-shade-a'
              : 'text-btn-shade-b hover:text-btn-shade-c'
          "
          :aria-label="$t('nav.map')"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300"
            :class="
              isActive('/map') || isActive('/')
                ? 'bg-btn-shade-e text-btn-shade-a -translate-y-0.5 shadow-[0_2px_4px_rgba(0,0,0,0.1)] border border-btn-shade-b'
                : ''
            "
          >
            <MapIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 font-accent">{{ $t('nav.map') }}</span>
        </router-link>

        <!-- Upload -->
        <router-link
          to="/upload"
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="
            isActive('/upload') ? 'text-btn-shade-a' : 'text-btn-shade-b hover:text-btn-shade-c'
          "
          :aria-label="$t('nav.upload')"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300"
            :class="
              isActive('/upload')
                ? 'bg-btn-shade-e text-btn-shade-a -translate-y-0.5 shadow-[0_2px_4px_rgba(0,0,0,0.1)] border border-btn-shade-b'
                : ''
            "
          >
            <UploadIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 font-accent">{{ $t('nav.upload') }}</span>
        </router-link>

        <!-- Gallery -->
        <router-link
          to="/gallery"
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="
            isActive('/gallery') ? 'text-btn-shade-a' : 'text-btn-shade-b hover:text-btn-shade-c'
          "
          :aria-label="$t('nav.gallery')"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300"
            :class="
              isActive('/gallery')
                ? 'bg-btn-shade-e text-btn-shade-a -translate-y-0.5 shadow-[0_2px_4px_rgba(0,0,0,0.1)] border border-btn-shade-b'
                : ''
            "
          >
            <GalleryIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 font-accent">{{ $t('nav.gallery') }}</span>
        </router-link>

        <!-- Leaderboard -->
        <router-link
          to="/leaderboard"
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="
            isActive('/leaderboard')
              ? 'text-btn-shade-a'
              : 'text-btn-shade-b hover:text-btn-shade-c'
          "
          :aria-label="$t('nav.leaderboard')"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300"
            :class="
              isActive('/leaderboard')
                ? 'bg-btn-shade-e text-btn-shade-a -translate-y-0.5 shadow-[0_2px_4px_rgba(0,0,0,0.1)] border border-btn-shade-b'
                : ''
            "
          >
            <TrophyIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 font-accent">{{ $t('nav.leaderboard') }}</span>
        </router-link>

        <!-- Profile / Login -->
        <button
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="
            isActive('/profile') || isActive('/login')
              ? 'text-btn-shade-a'
              : 'text-btn-shade-b hover:text-btn-shade-c'
          "
          :aria-label="authStore.isAuthenticated ? $t('nav.profile') : $t('auth.login')"
          @click="navigateToProfile"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300"
            :class="
              isActive('/profile') || isActive('/login')
                ? 'bg-btn-shade-e text-btn-shade-a -translate-y-0.5 shadow-[0_2px_4px_rgba(0,0,0,0.1)] border border-btn-shade-b'
                : ''
            "
          >
            <ProfileIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 font-accent">{{
            authStore.isAuthenticated ? $t('nav.profile') : $t('auth.login')
          }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>
