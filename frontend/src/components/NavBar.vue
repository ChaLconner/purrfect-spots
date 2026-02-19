<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../store/authStore';
import { useCatsStore } from '../store';

// Child Components
import SearchBox from './navbar/SearchBox.vue';
import UserMenu from './navbar/UserMenu.vue';
import NavLink from './navbar/NavLink.vue';
import NotificationBell from './ui/NotificationBell.vue';
import LanguageSwitcher from './LanguageSwitcher.vue';

// Icons
import Logo from './icons/logo.vue';
import Paw from './icons/paw.vue';
import MapIcon from './icons/map.vue';
import Upload from './icons/upload.vue';
import Gallery from './icons/gallery.vue';
import Trophy from './icons/trophy.vue';
import ProfileIcon from './icons/profile.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const catsStore = useCatsStore();
</script>

<template>
  <nav class="navbar-container" aria-label="Main Navigation">
    <div class="navbar-content">
      <!-- Left Section: Logo + Brand + Cat Counter -->
      <div class="left-section">
        <button class="brand-section" aria-label="Go to home" @click="router.push('/')">
          <Logo class="brand-logo" />
          <span class="brand-name hidden md:block">Purrfect Spots</span>
        </button>

        <div v-if="route.path === '/map' || route.path === '/'" class="cat-counter hidden 2xl:flex">
          <div class="paw-icon-wrapper">
            <Paw class="paw-icon" />
          </div>
          <div class="cat-counter-text">
            <span class="cat-count">{{ catsStore.catCount }} {{ $t('cats.cats') }}</span>
            <span class="cat-subtitle">{{ $t('cats.spottedNearby') }}</span>
          </div>
        </div>
      </div>

      <!-- Center Section: Search Box -->
      <div class="center-section">
        <SearchBox />
      </div>

      <!-- Right Section: Navigation + Login -->
      <div class="right-section">
        <!-- Desktop Nav Links -->
        <div class="nav-links hidden xl:flex items-center gap-1.5">
          <NavLink
            to="/map"
            variant="sage"
            :label="$t('nav.map')"
            :class="{ active: route.path === '/map' || route.path === '/' }"
          >
            <template #icon>
              <MapIcon class="nav-icon" />
            </template>
          </NavLink>

          <NavLink
            to="/upload"
            variant="sky"
            :label="$t('nav.upload')"
            :class="{ active: route.path === '/upload' }"
          >
            <template #icon>
              <Upload class="nav-icon" />
            </template>
          </NavLink>

          <NavLink
            to="/gallery"
            variant="lavender"
            :label="$t('nav.gallery')"
            :class="{ active: route.path === '/gallery' }"
          >
            <template #icon>
              <Gallery class="nav-icon" />
            </template>
          </NavLink>

          <NavLink
            to="/leaderboard"
            variant="sakura"
            :label="$t('nav.leaderboard')"
            :class="{ active: route.path === '/leaderboard' }"
          >
            <template #icon>
              <Trophy class="nav-icon" />
            </template>
          </NavLink>
        </div>

        <!-- Language Switcher (Always visible) -->
        <LanguageSwitcher />

        <!-- Login Button (not authenticated) - Hidden until xl, handled by BottomNav -->
        <div v-if="!authStore.isAuthenticated" class="hidden xl:flex items-center gap-2">
          <NavLink to="/login" variant="accent" :label="$t('auth.login')">
            <template #icon>
              <ProfileIcon class="nav-icon" />
            </template>
          </NavLink>
        </div>

        <!-- User Menu (authenticated) -->
        <div v-if="authStore.isAuthenticated" class="flex items-center gap-2">
          <NotificationBell />
          <UserMenu />
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar-container {
  position: sticky;
  top: 0;
  z-index: 50;
  margin: 1rem 2rem 1.5rem 2rem;
}

@media (max-width: 1279px) {
  .navbar-container {
    margin: 0.75rem 1rem;
  }
}

@media (max-width: 640px) {
  .navbar-container {
    margin: 0.5rem 0.75rem;
  }
}

@media (max-width: 480px) {
  .navbar-container {
    margin: 0.5rem;
  }
}

/* 3D Navbar Content */
.navbar-content {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--color-btn-bg);
  border-radius: 1.25rem;
  border: 2px solid var(--color-btn-shade-a);
  transform-style: preserve-3d;
  min-width: 0;
  gap: 0.5rem;
}

@media (min-width: 768px) {
  .navbar-content {
    padding: 0.625rem 1rem;
    gap: 1rem;
  }
}

@media (min-width: 1280px) {
  .navbar-content {
    padding: 0.75rem 1.5rem;
    gap: 2rem;
  }
}

.navbar-content::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-shade-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.4em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.4em, -1em);
  z-index: -1;
}

/* Left Section */
.left-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
}

/* 3D Brand Section */
.brand-section {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.375rem 0.75rem;
  border-radius: 1em;
  border: 2px solid var(--color-btn-shade-a);
  background: var(--color-btn-shade-e);
  transition: all 0.2s ease;
}

.brand-section:hover {
  background: var(--color-btn-shade-d);
  transform: translateY(-2px);
}

.brand-section:active {
  transform: translateY(0);
}

.brand-logo {
  width: 2.25rem;
  height: 2.25rem;
  filter: drop-shadow(0 2px 4px rgba(106, 163, 137, 0.3));
  position: relative;
  z-index: 1;
}

.brand-name {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--color-btn-shade-a);
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

/* 3D Cat Counter */
.cat-counter {
  position: relative;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border-radius: 1em;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  transform-style: preserve-3d;
}

.cat-counter::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-shade-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.25em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.25em, -1em);
}

.paw-icon-wrapper {
  width: 1.75rem;
  height: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.paw-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: var(--color-btn-shade-a);
}

.cat-counter-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
  position: relative;
  z-index: 1;
}

.cat-count {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-weight: 700;
  font-size: 0.8rem;
  color: var(--color-btn-shade-a);
}

.cat-subtitle {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.6rem;
  color: var(--color-btn-shade-b);
}

/* Center Section - Search */
.center-section {
  display: flex;
  justify-content: center;
  flex: 1;
  min-width: 0;
  max-width: 480px;
  justify-self: center;
  padding: 0 0.5rem;
}

@media (min-width: 1280px) {
  .center-section {
    z-index: 10;
  }
}

/* Right Section */
.right-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  z-index: 20;
}

@media (min-width: 768px) {
  .right-section {
    gap: 1rem;
  }
}

/* Nav Icon Sizing - Hover effects handled in NavLink */
.nav-icon {
  width: 1.1rem;
  height: 1.1rem;
  position: relative;
  z-index: 1;
}

/* Mobile Nav Visibility - Removed display: none */
@media (max-width: 640px) {
  .navbar-container {
    margin: 0.5rem;
    display: block !important;
  }
}
</style>
