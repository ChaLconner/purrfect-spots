<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../store/authStore';

// Child Components
import SearchBox from './navbar/SearchBox.vue';
import NavLink from './navbar/NavLink.vue';
import LanguageSwitcher from './LanguageSwitcher.vue';

// Icons
import MapIcon from './icons/map.vue';
import Upload from './icons/upload.vue';
import Gallery from './icons/gallery.vue';
import Trophy from './icons/trophy.vue';
import ProfileIcon from './icons/profile.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const isAuthUiResolved = computed(
  () => authStore.isInitialized || authStore.isAuthenticated || !!authStore.user
);
const showAuthenticatedActions = computed(() => authStore.isAuthenticated);
const showGuestLogin = computed(() => isAuthUiResolved.value && !showAuthenticatedActions.value);
const UserMenu = defineAsyncComponent({
  loader: () => import('./navbar/UserMenu.vue'),
  suspensible: false,
});
const NotificationBell = defineAsyncComponent({
  loader: () => import('./ui/NotificationBell.vue'),
  suspensible: false,
});
</script>

<template>
  <nav class="sticky top-0 z-50 m-3 sm:mx-6 md:mx-8 xl:mx-12 xl:my-5" aria-label="Main Navigation">
    <div
      class="relative flex justify-between items-center px-4 sm:px-6 md:px-8 xl:px-10 py-2 bg-btn-bg rounded-[2rem] border-2 border-btn-shade-a gap-1.5 sm:gap-4 xl:gap-8 min-w-0"
      style="transform-style: preserve-3d"
    >
      <!-- 3D Base -->
      <div
        class="absolute inset-0 bg-btn-shade-c rounded-[inherit] -z-10 shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.25rem_0_0_var(--color-btn-shade-a)]"
        style="transform: translate3d(0, 0.25rem, -1em)"
      ></div>

      <!-- Left Section: Logo + Brand + Cat Counter -->
      <div class="flex items-center gap-2 lg:gap-3 shrink-0">
        <button
          class="relative flex items-center cursor-pointer p-0.5 rounded-2xl bg-transparent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-btn-shade-a"
          aria-label="Go to home"
          @click="router.push('/')"
        >
          <!-- Mobile Logo (Icon only) -->
          <img
            src="/cat-icon.webp"
            alt="Logo"
            class="relative z-10 w-9 h-9 sm:hidden object-contain"
            loading="eager"
            fetchpriority="high"
          />
          <!-- Desktop Logo (Full logo) -->
          <img
            src="/logo.webp"
            alt="Purrfect Spots — Discover cat-friendly locations"
            class="relative z-10 hidden sm:block w-auto object-contain drop-shadow-sm h-14 -my-3 md:h-20 md:-my-6 xl:h-28 xl:-my-10 max-w-[180px] sm:max-w-[220px] md:max-w-[280px] xl:max-w-[380px]"
            loading="eager"
            fetchpriority="high"
            decoding="async"
          />
        </button>
      </div>

      <!-- Center Section: Search Box -->
      <div
        class="flex justify-center flex-1 min-w-0 max-w-[480px] justify-self-center px-2 xl:z-10"
      >
        <SearchBox />
      </div>

      <!-- Right Section: Navigation + Login -->
      <div class="flex items-center gap-2 md:gap-4 shrink-0 z-20">
        <!-- Desktop Nav Links -->
        <div class="hidden xl:flex items-center gap-1.5">
          <NavLink
            to="/map"
            variant="sage"
            :label="$t('nav.map')"
            :class="{ active: route.path === '/map' || route.path === '/' }"
          >
            <template #icon>
              <MapIcon class="relative z-10 w-[1.1rem] h-[1.1rem]" />
            </template>
          </NavLink>

          <NavLink
            to="/upload"
            variant="sky"
            :label="$t('nav.upload')"
            :class="{ active: route.path === '/upload' }"
          >
            <template #icon>
              <Upload class="relative z-10 w-[1.1rem] h-[1.1rem]" />
            </template>
          </NavLink>

          <NavLink
            to="/gallery"
            variant="lavender"
            :label="$t('nav.gallery')"
            :class="{ active: route.path === '/gallery' }"
          >
            <template #icon>
              <Gallery class="relative z-10 w-[1.1rem] h-[1.1rem]" />
            </template>
          </NavLink>

          <NavLink
            to="/leaderboard"
            variant="sakura"
            :label="$t('nav.leaderboard')"
            :class="{ active: route.path === '/leaderboard' }"
          >
            <template #icon>
              <Trophy class="relative z-10 w-[1.1rem] h-[1.1rem]" />
            </template>
          </NavLink>
        </div>

        <!-- Language Switcher (Always visible) -->
        <LanguageSwitcher />

        <!-- Authentication Dependent Section -->
        <template v-if="showGuestLogin">
          <!-- Login Button (not authenticated) - Hidden until xl, handled by BottomNav -->
          <div class="hidden xl:flex items-center gap-2 min-w-[5.5rem] justify-end">
            <NavLink to="/login" variant="accent" :label="$t('auth.login')">
              <template #icon>
                <ProfileIcon class="relative z-10 w-[1.1rem] h-[1.1rem]" />
              </template>
            </NavLink>
          </div>
        </template>
        <template v-else-if="showAuthenticatedActions">
          <div class="flex items-center gap-2 min-w-[5.5rem] justify-end">
            <NotificationBell />
            <UserMenu />
          </div>
        </template>
        <template v-else>
          <!-- Preserve layout during silent auth hydration without showing a visible loading state. -->
          <div class="hidden xl:block min-w-[5.5rem] h-10" aria-hidden="true"></div>
        </template>
      </div>
    </div>
  </nav>
</template>
