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
  <nav class="sticky top-0 z-50 m-2 sm:m-3 md:m-4 xl:my-4 xl:mx-8" aria-label="Main Navigation">
    <div
      class="relative flex justify-between items-center px-3 sm:px-4 md:px-5 xl:px-6 py-2 md:py-2.5 xl:py-3 bg-btn-bg rounded-[1.25rem] border-2 border-btn-shade-a gap-2 md:gap-4 xl:gap-8 min-w-0"
      style="transform-style: preserve-3d"
    >
      <!-- 3D Base -->
      <div
        class="absolute inset-0 bg-btn-shade-c rounded-[inherit] -z-10 shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.25rem_0_0_var(--color-btn-shade-a)]"
        style="transform: translate3d(0, 0.25rem, -1em)"
      ></div>

      <!-- Left Section: Logo + Brand + Cat Counter -->
      <div class="flex items-center gap-4 shrink-0">
        <button
          class="relative flex items-center gap-2 cursor-pointer px-3 py-1.5 rounded-2xl border-2 border-btn-shade-a bg-btn-shade-e transition-all duration-200 ease-in-out hover:bg-btn-shade-d hover:-translate-y-0.5 active:translate-y-0"
          aria-label="Go to home"
          @click="router.push('/')"
        >
          <Logo class="relative z-10 w-9 h-9 drop-shadow-[0_2px_4px_rgba(106,163,137,0.3)]" />
          <span
            class="relative z-10 font-accent font-bold text-lg text-btn-shade-a whitespace-nowrap hidden md:block"
          >Purrfect Spots</span>
        </button>

        <div
          v-if="route.path === '/map' || route.path === '/'"
          class="relative items-center gap-2 px-3 py-1.5 rounded-2xl bg-btn-shade-e border-2 border-btn-shade-a hidden 2xl:flex"
          style="transform-style: preserve-3d"
        >
          <div
            class="absolute inset-0 bg-btn-shade-c rounded-[inherit] shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.2rem_0_0_var(--color-btn-shade-a)]"
            style="transform: translate3d(0, 0.2rem, -1em)"
          ></div>
          <div class="relative z-10 w-7 h-7 flex items-center justify-center">
            <Paw class="w-6 h-6 text-btn-shade-a" />
          </div>
          <div class="relative z-10 flex flex-col leading-tight">
            <span class="font-accent font-bold text-xs text-btn-shade-a">
              {{ catsStore.catCount }} {{ $t('cats.cats') }}
            </span>
            <span class="font-accent text-[0.6rem] text-btn-shade-b">{{
              $t('cats.spottedNearby')
            }}</span>
          </div>
        </div>
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

        <!-- Login Button (not authenticated) - Hidden until xl, handled by BottomNav -->
        <div v-if="!authStore.isAuthenticated" class="hidden xl:flex items-center gap-2">
          <NavLink to="/login" variant="accent" :label="$t('auth.login')">
            <template #icon>
              <ProfileIcon class="relative z-10 w-[1.1rem] h-[1.1rem]" />
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
