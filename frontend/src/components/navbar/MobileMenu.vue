<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../../store/authStore';
import { AuthService } from '../../services/authService';
import { showSuccess } from '../../store/toast';
import { isDev } from '../../utils/env';
import SearchBox from './SearchBox.vue';
import MapIcon from '../icons/map.vue';
import Upload from '../icons/upload.vue';
import Gallery from '../icons/gallery.vue';

const { t } = useI18n();
const menuOpen = defineModel<boolean>('menuOpen', { default: false });
const router = useRouter();
const authStore = useAuthStore();

const logout = async () => {
  try {
    await AuthService.logout();
  } catch (error) {
    if (isDev()) {
      console.error('Logout error:', error);
    }
  } finally {
    authStore.clearAuth();
    router.push('/');
    showSuccess(t('toast.loggedOut'));
    menuOpen.value = false;
  }
};

const closeMenu = () => {
  menuOpen.value = false;
};
</script>

<template>
  <nav
    id="mobile-menu"
    class="absolute top-full left-0 right-0 mt-2 p-4 bg-[rgba(255,253,250,0.98)] backdrop-blur-md rounded-3xl border border-[rgba(139,90,43,0.15)] shadow-[0_8px_24px_rgba(139,90,43,0.15)] transition-all duration-300 ease-in-out md:hidden"
    :class="
      menuOpen
        ? 'opacity-100 translate-y-0 pointer-events-auto'
        : 'opacity-0 -translate-y-2.5 pointer-events-none'
    "
    aria-label="Mobile navigation"
  >
    <!-- Mobile Search -->
    <div class="mb-4">
      <SearchBox />
    </div>

    <!-- Mobile Navigation Links -->
    <div class="flex flex-col gap-1">
      <router-link
        to="/map"
        class="flex items-center gap-3 px-4 py-3.5 rounded-2xl font-accent text-[0.95rem] font-semibold text-sand-700 bg-transparent transition-all duration-300 ease-in-out w-full text-left hover:bg-[rgba(212,132,90,0.15)] hover:text-[#6b5c4b]"
        @click="closeMenu"
      >
        <MapIcon class="w-5 h-5" />
        <span>{{ $t('nav.map') }}</span>
      </router-link>

      <router-link
        to="/upload"
        class="flex items-center gap-3 px-4 py-3.5 rounded-2xl font-accent text-[0.95rem] font-semibold text-sand-700 bg-transparent transition-all duration-300 ease-in-out w-full text-left hover:bg-[rgba(212,132,90,0.15)] hover:text-[#6b5c4b]"
        @click="closeMenu"
      >
        <Upload class="w-5 h-5" />
        <span>{{ $t('nav.upload') }}</span>
      </router-link>

      <router-link
        to="/gallery"
        class="flex items-center gap-3 px-4 py-3.5 rounded-2xl font-accent text-[0.95rem] font-semibold text-sand-700 bg-transparent transition-all duration-300 ease-in-out w-full text-left hover:bg-[rgba(212,132,90,0.15)] hover:text-[#6b5c4b]"
        @click="closeMenu"
      >
        <Gallery class="w-5 h-5" />
        <span>{{ $t('nav.gallery') }}</span>
      </router-link>

      <router-link
        v-if="!authStore.isAuthenticated"
        to="/login"
        class="mt-2 flex items-center justify-center gap-3 px-4 py-3.5 rounded-2xl font-accent text-[0.95rem] font-semibold text-white bg-gradient-to-br from-[#c97b49] to-[#b06a3d] transition-all duration-300 ease-in-out w-full hover:from-[#d48a5a] hover:to-[#c97b49]"
        @click="closeMenu"
      >
        <span>{{ $t('auth.login') }}</span>
      </router-link>

      <button
        v-else
        class="mt-2 flex items-center justify-center gap-3 px-4 py-3.5 rounded-2xl font-accent text-[0.95rem] font-semibold text-[#dc4a4a] bg-transparent transition-all duration-300 ease-in-out w-full hover:bg-[rgba(220,74,74,0.1)]"
        @click="logout"
      >
        <span>{{ $t('auth.logout') }}</span>
      </button>
    </div>
  </nav>
</template>
