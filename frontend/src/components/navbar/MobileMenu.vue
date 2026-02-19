<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../store/authStore';
import { AuthService } from '../../services/authService';
import { showSuccess } from '../../store/toast';
import { isDev } from '../../utils/env';
import SearchBox from './SearchBox.vue';
import MapIcon from '../icons/map.vue';
import Upload from '../icons/upload.vue';
import Gallery from '../icons/gallery.vue';

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
    authStore.clearAuth();
    router.push('/');
    showSuccess(t('toast.loggedOut'));
    menuOpen.value = false;
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
    class="mobile-menu"
    :class="{ 'mobile-menu-open': menuOpen }"
    aria-label="Mobile navigation"
  >
    <!-- Mobile Search -->
    <div class="mobile-search-section">
      <SearchBox />
    </div>

    <!-- Mobile Navigation Links -->
    <div class="mobile-nav-links">
      <router-link to="/map" class="mobile-nav-link" @click="closeMenu">
        <MapIcon class="nav-icon" />
        <span>{{ $t('nav.map') }}</span>
      </router-link>

      <router-link to="/upload" class="mobile-nav-link" @click="closeMenu">
        <Upload class="nav-icon" />
        <span>{{ $t('nav.upload') }}</span>
      </router-link>

      <router-link to="/gallery" class="mobile-nav-link" @click="closeMenu">
        <Gallery class="nav-icon" />
        <span>{{ $t('nav.gallery') }}</span>
      </router-link>

      <router-link
        v-if="!authStore.isAuthenticated"
        to="/login"
        class="mobile-nav-link login"
        @click="closeMenu"
      >
        <span>{{ $t('auth.login') }}</span>
      </router-link>

      <button v-else class="mobile-nav-link logout" @click="logout">
        <span>{{ $t('auth.logout') }}</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.mobile-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 0.5rem;
  padding: 1rem;
  background: rgba(255, 253, 250, 0.98);
  backdrop-filter: blur(12px);
  border-radius: 1.5rem;
  border: 1px solid rgba(139, 90, 43, 0.15);
  box-shadow: 0 8px 24px rgba(139, 90, 43, 0.15);
  opacity: 0;
  transform: translateY(-10px);
  pointer-events: none;
  transition: all 0.3s ease;
}

.mobile-menu-open {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.mobile-search-section {
  margin-bottom: 1rem;
}

.mobile-nav-links {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: 1rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.95rem;
  font-weight: 600;
  color: #44403c;
  text-decoration: none;
  transition: all 0.3s ease;
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
}

.mobile-nav-link:hover {
  background: rgba(212, 132, 90, 0.15);
  color: #6b5c4b;
}

.mobile-nav-link.login {
  margin-top: 0.5rem;
  background: linear-gradient(135deg, #c97b49 0%, #b06a3d 100%);
  color: #fff;
  justify-content: center;
}

.mobile-nav-link.login:hover {
  background: linear-gradient(135deg, #d48a5a 0%, #c97b49 100%);
}

.mobile-nav-link.logout {
  margin-top: 0.5rem;
  color: #dc4a4a;
  justify-content: center;
}

.mobile-nav-link.logout:hover {
  background: rgba(220, 74, 74, 0.1);
}

.nav-icon {
  width: 1.25rem;
  height: 1.25rem;
}

/* Only show on mobile */
@media (max-width: 768px) {
  .mobile-menu {
    display: block;
  }
}
</style>
