<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../store/authStore';
import { useCatsStore } from '../store';
import { AuthService } from '../services/authService';
import { showSuccess } from '../store/toast';
import { isDev } from '../utils/env';

// Child Components
import SearchBox from './navbar/SearchBox.vue';
import UserMenu from './navbar/UserMenu.vue';
import NotificationBell from './ui/NotificationBell.vue';

// Icons
import Logo from './icons/logo.vue';
import Paw from './icons/paw.vue';
import MapIcon from './icons/map.vue';
import Upload from './icons/upload.vue';
import Gallery from './icons/gallery.vue';
import ProfileIcon from './icons/profile.vue';
import Trophy from './icons/trophy.vue';

const menuOpen = ref(false);
const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const catsStore = useCatsStore();

// Close menus when clicking outside
const handleEvents = (event: Event) => {
  const target = event.target as HTMLElement;
  const navContainer = document.querySelector('.navbar-container');

  // Close mobile hamburger menu on click outside
  if (event.type === 'click' && menuOpen.value && navContainer && !navContainer.contains(target)) {
    menuOpen.value = false;
  }

  // Close on Escape key
  if (event.type === 'keydown' && (event as KeyboardEvent).key === 'Escape' && menuOpen.value) {
    menuOpen.value = false;
  }
};

const mobileSearchInput = ref<HTMLInputElement | null>(null);

// Focus search input when menu opens
watch(menuOpen, (isOpen) => {
  if (isOpen) {
    setTimeout(() => {
      mobileSearchInput.value?.focus();
    }, 300);
  }
});

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
    showSuccess('Logged out successfully');
  }
};

onMounted(() => {
  // authStore initialized automatically
  document.addEventListener('click', handleEvents);
  document.addEventListener('keydown', handleEvents);
});

onUnmounted(() => {
  document.removeEventListener('click', handleEvents);
  document.removeEventListener('keydown', handleEvents);
});
</script>

<template>
  <nav class="navbar-container" aria-label="Main Navigation">
    <div class="navbar-content">
      <!-- Left Section: Logo + Brand + Cat Counter -->
      <div class="left-section">
        <button class="brand-section" aria-label="Go to home" @click="router.push('/')">
          <Logo class="brand-logo" />
          <span class="brand-name">Purrfect Spots</span>
        </button>

        <div v-if="route.path === '/map' || route.path === '/'" class="cat-counter">
          <div class="paw-icon-wrapper">
            <Paw class="paw-icon" />
          </div>
          <div class="cat-counter-text">
            <span class="cat-count">{{ catsStore.catCount }} cats</span>
            <span class="cat-subtitle">spotted nearby</span>
          </div>
        </div>
      </div>

      <!-- Center Section: Search Box -->
      <div class="center-section">
        <SearchBox />
      </div>

      <!-- Right Section: Navigation + Login -->
      <div class="right-section">
        <div class="nav-links">
          <router-link
            to="/map"
            class="nav-link-3d nav-link-sage"
            :class="{ active: route.path === '/map' || route.path === '/' }"
            aria-label="Map"
          >
            <MapIcon class="nav-icon" />
            <span>Map</span>
          </router-link>

          <router-link
            to="/upload"
            class="nav-link-3d nav-link-sky"
            :class="{ active: route.path === '/upload' }"
            aria-label="Upload"
          >
            <Upload class="nav-icon" />
            <span>Upload</span>
          </router-link>

          <router-link
            to="/gallery"
            class="nav-link-3d nav-link-lavender"
            :class="{ active: route.path === '/gallery' }"
            aria-label="Gallery"
          >
            <Gallery class="nav-icon" />
            <span>Gallery</span>
          </router-link>

          <router-link
            to="/leaderboard"
            class="nav-link-3d nav-link-sakura"
            :class="{ active: route.path === '/leaderboard' }"
            aria-label="Leaderboard"
          >
            <Trophy class="nav-icon" />
            <span>Leaderboard</span>
          </router-link>
        </div>

        <!-- Login Button (not authenticated) -->
        <div v-if="!authStore.isAuthenticated">
          <router-link to="/login" class="login-btn-3d"> Login </router-link>
        </div>

        <!-- User Menu (authenticated) -->
        <div v-if="authStore.isAuthenticated" class="flex items-center gap-2">
          <NotificationBell />
          <UserMenu />
        </div>
      </div>

      <!-- Hamburger button (mobile only) -->
      <button
        class="hamburger-btn"
        :aria-expanded="menuOpen"
        aria-controls="mobile-menu"
        aria-label="Toggle navigation menu"
        @click="menuOpen = !menuOpen"
      >
        <div class="hamburger-lines">
          <span
            class="hamburger-line"
            :class="menuOpen ? 'rotate-45 translate-y-0' : '-translate-y-2'"
          ></span>
          <span class="hamburger-line" :class="menuOpen ? 'opacity-0' : 'opacity-100'"></span>
          <span
            class="hamburger-line"
            :class="menuOpen ? '-rotate-45 translate-y-0' : 'translate-y-2'"
          ></span>
        </div>
      </button>
    </div>

    <!-- Mobile Menu -->
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
        <router-link
          to="/map"
          class="mobile-nav-link-3d"
          role="link"
          aria-label="Map"
          @click="menuOpen = false"
        >
          <MapIcon class="nav-icon" />
          <span>Map</span>
        </router-link>

        <router-link to="/upload" class="mobile-nav-link-3d" @click="menuOpen = false">
          <Upload class="nav-icon" />
          <span>Upload</span>
        </router-link>

        <router-link to="/gallery" class="mobile-nav-link-3d" @click="menuOpen = false">
          <Gallery class="nav-icon" />
          <span>Gallery</span>
        </router-link>

        <router-link to="/leaderboard" class="mobile-nav-link-3d" @click="menuOpen = false">
          <Trophy class="nav-icon" />
          <span>Leaderboard</span>
        </router-link>

        <router-link
          v-if="authStore.isAuthenticated"
          to="/profile"
          class="mobile-nav-link-3d"
          @click="menuOpen = false"
        >
          <ProfileIcon class="nav-icon" />
          <span>Profile</span>
        </router-link>

        <router-link
          v-if="!authStore.isAuthenticated"
          to="/login"
          class="mobile-nav-link-3d login"
          @click="menuOpen = false"
        >
          <span>Login</span>
        </router-link>

        <button
          v-else
          class="mobile-nav-link-3d logout"
          @click="
            logout();
            menuOpen = false;
          "
        >
          <span>Logout</span>
        </button>
      </div>
    </nav>
  </nav>
</template>

<style scoped>
.navbar-container {
  position: sticky;
  top: 0;
  z-index: 50;
  margin: 1rem 2rem;
}

/* 3D Navbar Content */
.navbar-content {
  position: relative;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: var(--color-btn-bg);
  border-radius: 1.25rem;
  border: 2px solid var(--color-btn-shade-a);
  transform-style: preserve-3d;
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
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.brand-section::before {
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
    0 0.35em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.35em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.brand-section:hover {
  background: var(--color-btn-shade-d);
  transform: translate(0, 0.175em);
}

.brand-section:hover::before {
  transform: translate3d(0, 0.35em, -1em);
}

.brand-section:active {
  transform: translate(0, 0.35em);
}

.brand-section:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.1em 0 0 var(--color-btn-shade-b);
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
  display: flex;
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
  width: 100%;
  max-width: 480px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #fffdf5;
  border: 2px solid rgba(139, 90, 43, 0.1);
  border-radius: 2rem;
  padding: 0.35rem 0.35rem 0.35rem 1.25rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  width: 100%;
  box-shadow: 0 2px 8px rgba(139, 90, 43, 0.03);
}

.search-box:focus-within {
  border-color: #d4845a;
  background: #fff;
  box-shadow:
    0 4px 12px rgba(212, 132, 90, 0.15),
    inset 0 1px 2px rgba(139, 90, 43, 0.05);
  transform: translateY(-1px);
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
  color: #5a4a3a;
  flex: 1;
  padding: 0.2rem 0;
  min-width: 0;
}

.search-input::placeholder {
  color: #757575; /* Darkened from #b0a090 */
  font-style: italic;
  opacity: 0.8;
}

.search-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #f5a962 0%, #e89445 100%);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(232, 148, 69, 0.3);
}

.search-btn:hover {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 4px 10px rgba(232, 148, 69, 0.5);
  background: linear-gradient(135deg, #fbbd7e 0%, #f5a962 100%);
}

.search-btn.clear-mode {
  background: linear-gradient(135deg, #d47979 0%, #c96262 100%);
  box-shadow: 0 2px 6px rgba(201, 98, 98, 0.3);
  color: white;
}

.search-btn.clear-mode:hover {
  transform: scale(1.1) rotate(-5deg);
  box-shadow: 0 4px 10px rgba(201, 98, 98, 0.5);
  background: linear-gradient(135deg, #e08888 0%, #d47979 100%);
}

.search-icon {
  width: 1rem;
  height: 1rem;
  color: white;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

/* Right Section */
.right-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  justify-self: end;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* 3D Nav Link - using CSS custom buttons from provided design */
.nav-link-3d {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  outline: none;
  border: 0;
  vertical-align: middle;
  text-decoration: none;
  font-size: 0.85rem;
  color: var(--color-btn-shade-a);
  font-weight: 600;
  font-family: 'Zen Maru Gothic', sans-serif;
  padding: 0.5rem 0.875rem;
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 0.75em;
  background: var(--color-btn-shade-e);
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.nav-link-3d::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-btn-shade-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.4em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.4em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.nav-link-3d:hover {
  background: var(--color-btn-shade-d);
  transform: translate(0, 0.2em);
}

.nav-link-3d:hover::before {
  transform: translate3d(0, 0.4em, -1em);
}

.nav-link-3d:active {
  transform: translate(0em, 0.4em);
}

.nav-link-3d:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.1em 0 0 var(--color-btn-shade-b);
}

.nav-link-3d.active {
  background: var(--color-btn-shade-d);
  font-weight: 700;
}

.nav-icon {
  width: 1.1rem;
  height: 1.1rem;
  transition: transform 0.2s ease;
  position: relative;
  z-index: 1;
}

.nav-link-3d span {
  position: relative;
  z-index: 1;
}

.nav-link-3d:hover .nav-icon {
  transform: rotate(-8deg) scale(1.1);
}

/* Nav Link Color Variants */
/* Sage (default - already applied in base) */
.nav-link-sage {
  /* Uses default shade variables */
}

/* Sky Blue Variant */
.nav-link-sky {
  color: var(--color-btn-sky-a);
  border-color: var(--color-btn-sky-a);
  background: var(--color-btn-sky-e);
}

.nav-link-sky::before {
  background: var(--color-btn-sky-c);
  box-shadow:
    0 0 0 2px var(--color-btn-sky-b),
    0 0.4em 0 0 var(--color-btn-sky-a);
}

.nav-link-sky:hover {
  background: var(--color-btn-sky-d);
}

.nav-link-sky.active {
  background: var(--color-btn-sky-d);
}

/* Lavender Variant */
.nav-link-lavender {
  color: var(--color-btn-lavender-a);
  border-color: var(--color-btn-lavender-a);
  background: var(--color-btn-lavender-e);
}

.nav-link-lavender::before {
  background: var(--color-btn-lavender-c);
  box-shadow:
    0 0 0 2px var(--color-btn-lavender-b),
    0 0.4em 0 0 var(--color-btn-lavender-a);
}

.nav-link-lavender:hover {
  background: var(--color-btn-lavender-d);
}

.nav-link-lavender.active {
  background: var(--color-btn-lavender-d);
}

/* Sakura Pink Variant */
.nav-link-sakura {
  color: var(--color-btn-sakura-a);
  border-color: var(--color-btn-sakura-a);
  background: var(--color-btn-sakura-e);
}

.nav-link-sakura::before {
  background: var(--color-btn-sakura-c);
  box-shadow:
    0 0 0 2px var(--color-btn-sakura-b),
    0 0.4em 0 0 var(--color-btn-sakura-a);
}

.nav-link-sakura:hover {
  background: var(--color-btn-sakura-d);
}

.nav-link-sakura.active {
  background: var(--color-btn-sakura-d);
}

/* 3D Login Button - Terracotta Accent */
.login-btn-3d {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  outline: none;
  border: 0;
  vertical-align: middle;
  text-decoration: none;
  font-size: 0.85rem;
  color: var(--color-btn-accent-a);
  font-weight: 700;
  text-transform: uppercase;
  font-family: 'Zen Maru Gothic', sans-serif;
  padding: 0.5rem 1.25rem;
  border: 2px solid var(--color-btn-accent-a);
  border-radius: 1em;
  background: var(--color-btn-accent-e);
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.login-btn-3d::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-btn-accent-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-accent-b),
    0 0.5em 0 0 var(--color-btn-accent-a);
  transform: translate3d(0, 0.5em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.login-btn-3d:hover {
  background: var(--color-btn-accent-d);
  transform: translate(0, 0.25em);
}

.login-btn-3d:hover::before {
  transform: translate3d(0, 0.5em, -1em);
}

.login-btn-3d:active {
  transform: translate(0em, 0.5em);
}

.login-btn-3d:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-accent-b),
    0 0.15em 0 0 var(--color-btn-accent-b);
}

/* User Menu */
.user-menu-container {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(139, 90, 43, 0.15);
  border-radius: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-btn:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(139, 90, 43, 0.25);
}

.user-avatar {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(201, 123, 73, 0.3);
}

.user-name {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
  color: #5a4a3a;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron-icon {
  width: 0.875rem;
  height: 0.875rem;
  color: #8b7355;
  transition: transform 0.3s ease;
}

.chevron-icon.rotate {
  transform: rotate(180deg);
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 200px;
  background: rgba(255, 253, 250, 0.98);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(139, 90, 43, 0.15);
  border-radius: 1rem;
  box-shadow: 0 8px 24px rgba(139, 90, 43, 0.15);
  overflow: hidden;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-header {
  padding: 0.875rem 1rem;
  background: rgba(139, 90, 43, 0.05);
}

.dropdown-name {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  color: #5a4a3a;
  margin: 0;
}

.dropdown-email {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.7rem;
  color: #8b7355;
  margin: 0.125rem 0 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-divider {
  height: 1px;
  background: rgba(139, 90, 43, 0.1);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.75rem 1rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.8rem;
  font-weight: 500;
  color: #5a4a3a;
  text-decoration: none;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s ease;
}

.dropdown-item:hover {
  background: rgba(139, 90, 43, 0.08);
}

.dropdown-item.logout {
  color: #dc4a4a;
}

.dropdown-item.logout:hover {
  background: rgba(220, 74, 74, 0.1);
}

/* 3D Hamburger Button */
.hamburger-btn {
  display: none;
  position: relative;
  width: 2.75rem;
  height: 2.75rem;
  padding: 0;
  border-radius: 0.75em;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  cursor: pointer;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
  color: var(--color-btn-shade-a);
  transform-style: preserve-3d;
  justify-content: center;
  align-items: center;
}

.hamburger-btn::before {
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
    0 0.35em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.35em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.hamburger-btn:hover {
  background: var(--color-btn-shade-d);
  transform: translate(0, 0.175em);
}

.hamburger-btn:hover::before {
  transform: translate3d(0, 0.35em, -1em);
}

.hamburger-btn:active {
  transform: translate(0, 0.35em);
}

.hamburger-btn:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.1em 0 0 var(--color-btn-shade-b);
}

.hamburger-lines {
  position: relative;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1;
}

.hamburger-line {
  position: absolute;
  width: 1.5rem;
  height: 2px;
  background: currentColor;
  border-radius: 2px;
  transition: all 0.3s ease;
}

/* 3D Mobile Menu */
.mobile-menu {
  display: none;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 0.75rem;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 1.25rem;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.5em 0 0 var(--color-btn-shade-a);
  z-index: 100;
}

.mobile-menu-open {
  display: flex;
}

.mobile-search-section {
  margin-bottom: 0.75rem;
}

.mobile-search-box {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  background: white;
  border: 2px solid rgba(139, 90, 43, 0.1);
  border-radius: 1.25rem;
  padding: 0.25rem;
  transition: all 0.3s ease;
}

.mobile-search-box:focus-within {
  border-color: #d4845a;
  box-shadow: 0 0 0 4px rgba(212, 132, 90, 0.1);
  transform: translateY(-1px);
}

.mobile-search-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: 0.75rem 0.75rem 0.75rem 1rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.95rem;
  color: #5a4a3a;
  outline: none;
}

.mobile-search-input::placeholder {
  color: #6b7280; /* gray-500 */
}

.mobile-search-icon {
  position: absolute;
  left: 1rem;
  width: 1.1rem;
  height: 1.1rem;
  color: #d4845a;
  pointer-events: none;
}

.mobile-clear-btn {
  position: absolute;
  right: 0.75rem;
  padding: 0.4rem;
  color: #757575; /* Darkened from #a69c91 */
  background: #f5f0e8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.mobile-clear-btn:active {
  transform: scale(0.9);
  background: #ede3d5;
}

.mobile-nav-links {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* 3D Mobile Nav Link */
.mobile-nav-link-3d {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  outline: none;
  border: 0;
  text-decoration: none;
  font-size: 0.95rem;
  color: var(--color-btn-shade-a);
  font-weight: 600;
  font-family: 'Zen Maru Gothic', sans-serif;
  padding: 0.875rem 1.25rem;
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 1em;
  background: var(--color-btn-shade-e);
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.mobile-nav-link-3d::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-btn-shade-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.5em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.5em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.mobile-nav-link-3d:hover {
  background: var(--color-btn-shade-d);
  transform: translate(0, 0.25em);
}

.mobile-nav-link-3d:hover::before {
  transform: translate3d(0, 0.5em, -1em);
}

.mobile-nav-link-3d:active {
  transform: translate(0em, 0.5em);
}

.mobile-nav-link-3d:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.15em 0 0 var(--color-btn-shade-b);
}

.mobile-nav-link-3d .nav-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: var(--color-btn-shade-a);
  transition: transform 0.2s ease;
  position: relative;
  z-index: 1;
}

.mobile-nav-link-3d span {
  position: relative;
  z-index: 1;
}

.mobile-nav-link-3d:hover .nav-icon {
  transform: rotate(-8deg) scale(1.1);
}

.mobile-nav-link-3d.login {
  background: var(--color-btn-accent-e);
  border-color: var(--color-btn-accent-a);
  color: var(--color-btn-accent-a);
  font-weight: 700;
}

.mobile-nav-link-3d.login::before {
  background: var(--color-btn-accent-c);
  box-shadow:
    0 0 0 2px var(--color-btn-accent-b),
    0 0.5em 0 0 var(--color-btn-accent-a);
}

.mobile-nav-link-3d.logout {
  color: #dc4a4a;
  border-color: #dc4a4a;
  background: #fff0f0;
}

.mobile-nav-link-3d.logout::before {
  background: #ffcccc;
  box-shadow:
    0 0 0 2px #f5a5a5,
    0 0.5em 0 0 #dc4a4a;
}

/* Responsive */
@media (max-width: 1280px) {
  .brand-name {
    display: none;
  }

  .cat-counter-text {
    display: none;
  }

  .cat-counter {
    padding: 0.375rem;
  }

  .nav-link-3d span {
    display: none;
  }

  .nav-link-3d {
    padding: 0.5rem;
  }

  .nav-icon {
    width: 1.25rem;
    height: 1.25rem;
  }

  .center-section {
    max-width: 200px;
    margin: 0 1rem;
  }
}

@media (max-width: 768px) {
  .navbar-container {
    margin: 0.5rem 1rem;
  }

  .navbar-content {
    padding: 0.5rem 1rem;
    display: flex;
    justify-content: space-between;
  }

  .cat-counter,
  .center-section,
  .right-section {
    display: none;
  }

  .hamburger-btn {
    display: flex;
  }
}

@media (max-width: 480px) {
  .navbar-container {
    margin: 0.5rem;
  }
}
</style>
