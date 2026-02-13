<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../store/authStore';
import { useCatsStore } from '../store';

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
import Trophy from './icons/trophy.vue';

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
            <span class="cat-count">{{ catsStore.catCount }} cats</span>
            <span class="cat-subtitle">spotted nearby</span>
          </div>
        </div>
      </div>

      <!-- Center Section: Search Box -->
      <div class="center-section hidden xl:flex">
        <SearchBox />
      </div>

      <!-- Right Section: Navigation + Login -->
      <div class="right-section">
        <!-- Desktop Nav Links -->
        <div class="nav-links hidden xl:flex">
          <router-link
            to="/map"
            class="nav-link-3d nav-link-sage"
            :class="{ active: route.path === '/map' || route.path === '/' }"
            aria-label="Map"
          >
            <MapIcon class="nav-icon" />
            <span class="hidden 2xl:block">Map</span>
          </router-link>

          <router-link
            to="/upload"
            class="nav-link-3d nav-link-sky"
            :class="{ active: route.path === '/upload' }"
            aria-label="Upload"
          >
            <Upload class="nav-icon" />
            <span class="hidden 2xl:block">Upload</span>
          </router-link>

          <router-link
            to="/gallery"
            class="nav-link-3d nav-link-lavender"
            :class="{ active: route.path === '/gallery' }"
            aria-label="Gallery"
          >
            <Gallery class="nav-icon" />
            <span class="hidden 2xl:block">Gallery</span>
          </router-link>

          <router-link
            to="/leaderboard"
            class="nav-link-3d nav-link-sakura"
            :class="{ active: route.path === '/leaderboard' }"
            aria-label="Leaderboard"
          >
            <Trophy class="nav-icon" />
            <span class="hidden 2xl:block">Leaderboard</span>
          </router-link>
        </div>

        <!-- Login Button (not authenticated) - Hidden until xl, handled by BottomNav -->
        <div v-if="!authStore.isAuthenticated" class="hidden xl:block">
          <router-link to="/login" class="login-btn-3d"> Login </router-link>
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
  min-width: 0; /* Allow flex shrinking */
}

@media (min-width: 768px) {
  .navbar-content {
    padding: 0.625rem 1rem;
  }
}

@media (min-width: 1280px) {
  .navbar-content {
    padding: 0.75rem 1.5rem;
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
  justify-content: center;
  width: 100%;
  max-width: 250px;
}

@media (min-width: 1280px) {
  .center-section {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    max-width: 240px;
    padding: 0 0.5rem;
    z-index: 10;
    justify-content: center;
    display: flex;
  }
}

@media (min-width: 1440px) {
  .center-section {
    max-width: 320px;
  }
}

@media (min-width: 1600px) {
  .center-section {
    max-width: 400px;
  }
}

@media (min-width: 1920px) {
  .center-section {
    max-width: 500px;
  }
}

/* Right Section */
.right-section {
  display: flex; /* Ensure flex is applied locally */
  align-items: center;
  gap: 0.5rem;
  justify-self: end;
  min-width: 0;
  flex-shrink: 0; /* Prevent shrinking to avoid layout shifts */
  z-index: 20; /* Ensure right section is clickable above search if narrow */
}

.nav-links {
  /* display: flex; Removed to respect Tailwind hidden classes */
  align-items: center;
  gap: 0.375rem; /* Reduced gap from 0.5rem */
}

/* 3D Nav Link */
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
  padding: 0.5rem 0.75rem; /* Reduced padding from 0.875rem */
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
.nav-link-sage {
  /* Uses default shade variables */
}

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

.nav-link-sky:hover,
.nav-link-sky.active {
  background: var(--color-btn-sky-d);
}

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

.nav-link-lavender:hover,
.nav-link-lavender.active {
  background: var(--color-btn-lavender-d);
}

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

.nav-link-sakura:hover,
.nav-link-sakura.active {
  background: var(--color-btn-sakura-d);
}

/* 3D Login Button */
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
</style>
