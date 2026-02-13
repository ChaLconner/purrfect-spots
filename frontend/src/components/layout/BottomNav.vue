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
      class="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg border border-stone-200 pointer-events-auto max-w-md mx-auto"
    >
      <div class="flex justify-around items-center px-2 py-3">
        <!-- Map -->
        <router-link
          to="/map"
          class="nav-item"
          :class="{ active: isActive('/map') || isActive('/') }"
          aria-label="Map"
        >
          <div class="icon-container">
            <MapIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-medium mt-1">Map</span>
        </router-link>

        <!-- Upload -->
        <router-link
          to="/upload"
          class="nav-item"
          :class="{ active: isActive('/upload') }"
          aria-label="Upload"
        >
          <div class="icon-container">
            <UploadIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-medium mt-1">Upload</span>
        </router-link>

        <!-- Gallery -->
        <router-link
          to="/gallery"
          class="nav-item"
          :class="{ active: isActive('/gallery') }"
          aria-label="Gallery"
        >
          <div class="icon-container">
            <GalleryIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-medium mt-1">Gallery</span>
        </router-link>

        <!-- Leaderboard -->
        <router-link
          to="/leaderboard"
          class="nav-item"
          :class="{ active: isActive('/leaderboard') }"
          aria-label="Leaderboard"
        >
          <div class="icon-container">
            <TrophyIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-medium mt-1">Rank</span>
        </router-link>

        <!-- Profile / Login -->
        <button
          class="nav-item"
          :class="{ active: isActive('/profile') || isActive('/login') }"
          aria-label="Profile"
          @click="navigateToProfile"
        >
          <div class="icon-container">
            <ProfileIcon class="w-6 h-6" />
          </div>
          <span class="text-xs font-medium mt-1">{{
            authStore.isAuthenticated ? 'Profile' : 'Login'
          }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #a8a29e; /* stone-400 */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0.25rem 0.5rem;
  border-radius: 0.75rem;
  flex: 1;
}

.nav-item:hover {
  color: #78716c; /* stone-500 */
}

.nav-item:active {
  transform: scale(0.95);
}

.nav-item.active {
  color: #ea580c; /* orange-600 */
}

.nav-item.active .icon-container {
  background-color: #fff7ed; /* orange-50 */
  color: #ea580c;
  transform: translateY(-2px);
  box-shadow:
    0 4px 6px -1px rgba(234, 88, 12, 0.1),
    0 2px 4px -1px rgba(234, 88, 12, 0.06);
}

.icon-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px; /* rounded-full */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
