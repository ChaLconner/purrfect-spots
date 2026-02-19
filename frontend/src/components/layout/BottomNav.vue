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

const isActive = (path: string) => {
  return route.path === path;
};

// Handle Profile Navigation based on Auth state
const navigateToProfile = () => {
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
      class="backdrop-blur-md rounded-2xl shadow-lg border pointer-events-auto max-w-md mx-auto"
      style="background: var(--color-glass-cream); border-color: var(--color-btn-shade-a)"
    >
      <div class="flex justify-around items-center px-2 py-3">
        <!-- Map -->
        <router-link
          to="/map"
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="isActive('/map') || isActive('/') ? 'active-link' : 'inactive-link'"
          :aria-label="$t('nav.map')"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300 icon-container"
            :class="{
              'active-icon': isActive('/map') || isActive('/'),
            }"
          >
            <MapIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 nav-label">{{ $t('nav.map') }}</span>
        </router-link>

        <!-- Upload -->
        <router-link
          to="/upload"
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="isActive('/upload') ? 'active-link' : 'inactive-link'"
          :aria-label="$t('nav.upload')"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300 icon-container"
            :class="{
              'active-icon': isActive('/upload'),
            }"
          >
            <UploadIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 nav-label">{{ $t('nav.upload') }}</span>
        </router-link>

        <!-- Gallery -->
        <router-link
          to="/gallery"
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="isActive('/gallery') ? 'active-link' : 'inactive-link'"
          :aria-label="$t('nav.gallery')"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300 icon-container"
            :class="{
              'active-icon': isActive('/gallery'),
            }"
          >
            <GalleryIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 nav-label">{{ $t('nav.gallery') }}</span>
        </router-link>

        <!-- Leaderboard -->
        <router-link
          to="/leaderboard"
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="isActive('/leaderboard') ? 'active-link' : 'inactive-link'"
          :aria-label="$t('nav.leaderboard')"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300 icon-container"
            :class="{
              'active-icon': isActive('/leaderboard'),
            }"
          >
            <TrophyIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 nav-label">{{ $t('nav.leaderboard') }}</span>
        </router-link>

        <!-- Profile / Login -->
        <button
          class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
          :class="isActive('/profile') || isActive('/login') ? 'active-link' : 'inactive-link'"
          :aria-label="authStore.isAuthenticated ? $t('nav.profile') : $t('auth.login')"
          @click="navigateToProfile"
        >
          <div
            class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300 icon-container"
            :class="{
              'active-icon': isActive('/profile') || isActive('/login'),
            }"
          >
            <ProfileIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-bold mt-1 nav-label">{{
            authStore.isAuthenticated ? $t('nav.profile') : $t('auth.login')
          }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.nav-label {
  font-family: 'Zen Maru Gothic', sans-serif;
}

.active-link {
  color: var(--color-btn-shade-a);
}

.inactive-link {
  color: var(--color-btn-shade-b);
}

.inactive-link:hover {
  color: var(--color-btn-shade-c);
}

.active-icon {
  background-color: var(--color-btn-shade-e);
  color: var(--color-btn-shade-a);
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--color-btn-shade-b);
}
</style>
