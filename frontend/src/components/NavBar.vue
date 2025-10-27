<script setup lang="ts">
import logo from "../components/icons/logo.vue";
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { authStore, initializeAuth, clearAuth } from "../store/auth";
import { AuthService } from "../services/authService";
import { isDev } from "../utils/env";
import Upload from "./icons/upload.vue";
import Map from "./icons/map.vue";
import gallery from "./icons/gallery.vue";

const menuOpen = ref(false);
const showUserMenu = ref(false);
const router = useRouter();

function goHome() {
  router.push("/");
}

const logout = async () => {
try {
  await AuthService.logout();
  clearAuth();
  showUserMenu.value = false;
  router.push("/"); // Redirect to home after logout
  // You can show a logout success toast here
} catch (error) {
  // Use our utility function to check if in development mode
  if (isDev()) {
    console.error("Logout error:", error);
  }
}
};

// Close user menu when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (showUserMenu.value && target && !target.closest(".user-menu-container")) {
    showUserMenu.value = false;
  }
};

// Initialize auth state on component mount
onMounted(() => {
  initializeAuth();
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>
<template>
  <nav class="navbar-glass flex items-center justify-between z-49">
    <!-- logo -->
    <div
      class="flex items-center md:mb-0 space-x-2 cursor-pointer align-middle"
      @click="goHome"
    >
      <logo class="w-8 h-8 animate-logo-float animate-logo-glow" />
      <div
        class="text-lg font-bold whitespace-nowrap cursor-pointer"
        @click.stop="router.push('/map')"
      >
        Purrfect Spots
      </div>
    </div>
    <!-- Hamburger button (mobile only) -->
    <button
      class="md:hidden p-3 rounded-xl transition-all duration-300 hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/20 active:bg-white/20 cursor-pointer"
      @click="menuOpen = !menuOpen"
      :aria-expanded="menuOpen"
      aria-controls="mobile-menu"
      aria-label="Toggle navigation menu"
    >
      <div class="relative w-6 h-6 flex flex-col justify-center items-center">
        <span
          class="absolute w-6 h-0.5 bg-current transition-all duration-300 ease-in-out"
          :class="menuOpen ? 'rotate-45 translate-y-0' : '-translate-y-2'"
        ></span>
        <span
          class="absolute w-6 h-0.5 bg-current transition-all duration-300 ease-in-out"
          :class="menuOpen ? 'opacity-0' : 'opacity-100'"
        ></span>
        <span
          class="absolute w-6 h-0.5 bg-current transition-all duration-300 ease-in-out"
          :class="menuOpen ? '-rotate-45 translate-y-0' : 'translate-y-2'"
        ></span>
      </div>
    </button>
    <!-- Menu -->
    <div
      id="mobile-menu"
      class="absolute top-full left-0 right-0 bg-[rgba(168,218,220,0.95)] backdrop-blur-md md:relative md:bg-transparent md:backdrop-blur-none flex-col md:flex-row items-center gap-2 md:gap-6 md:flex transition-all duration-300 ease-in-out py-4 md:py-0 shadow-lg md:shadow-none rounded-2xl"
      :class="menuOpen ? 'flex' : 'hidden md:flex'" 
      role="navigation"
      aria-label="Main navigation"
    >
      <div class="flex flex-row md:flex-row justify-around md:gap-2 w-full md:w-auto">
        <router-link
          to="/map"
          class="flex items-center gap-3 px-4 py-2 md:py-2 md:px-3 rounded-xl hover:bg-gray-100/50 transition-all duration-200 group active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-400/50"
          @click="menuOpen = false"
          aria-label="Navigate to Map page"
        >
          <Map class="w-6 h-6 md:w-6 md:h-6 flex-shrink-0" />
          <span class="text-base md:text-sm font-medium">Map</span>
        </router-link>
        <router-link
          to="/upload"
          class="flex items-center gap-3 px-4 py-2 md:py-2 md:px-3 rounded-xl hover:bg-gray-100/50 transition-all duration-200 group active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-400/50"
          @click="menuOpen = false"
          aria-label="Navigate to Upload page"
        >
          <Upload class="w-6 h-6 md:w-6 md:h-6 flex-shrink-0" />
          <span class="text-base md:text-sm font-medium">Upload</span>
        </router-link>
        <router-link
          to="/gallery"
          class="flex items-center gap-3 px-4 py-2 md:py-2 md:px-3 rounded-xl hover:bg-gray-100/50 transition-all duration-200 group active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-400/50"
          @click="menuOpen = false"
          aria-label="Navigate to Gallery page"
        >
          <gallery class="w-6 h-6 md:w-6 md:h-6 flex-shrink-0" />
          <span class="text-base md:text-sm font-medium">Gallery</span>
        </router-link>
      </div>

      <!-- Authentication Section -->
      <div v-if="!authStore.isAuthenticated" class="w-full md:w-auto px-5 md:px-0 pt-2 md:pt-0">
        <router-link
          to="/login"
          class="login-gradient-btn w-full md:w-auto justify-center text-base py-3 md:py-2 active:scale-95 transition-transform focus:outline-none focus:ring-2 focus:ring-blue-400/50"
          @click="menuOpen = false"
          aria-label="Navigate to Login page"
        >
          Login
        </router-link>
      </div>

      <!-- User Menu (when authenticated) -->
      <div v-else class="relative flex items-center gap-4 w-full md:w-auto px-5 md:px-0 pt-2 md:pt-0">
        <!-- User Avatar & Dropdown -->
        <div class="relative user-menu-container w-full md:w-auto">
          <button
            @click="showUserMenu = !showUserMenu"
            :aria-expanded="showUserMenu"
            aria-haspopup="true"
            aria-label="User menu"
            class="flex items-center gap-3 w-full md:w-auto focus:outline-none cursor-pointer p-3 md:p-2 rounded-xl hover:bg-gray-100/50 active:scale-95 transition-all"
          >
            <img
              :src="
                authStore.user?.picture ||
                '/default-avatar.svg'
              "
              :alt="authStore.user?.name || 'User Avatar'"
              class="w-10 h-10 md:w-8 md:h-8 rounded-full border-2 border-gray-300 shadow-sm"
            />
            <span class="flex-1 md:hidden text-base font-medium text-gray-700 text-left">
              {{ authStore.user?.name }}
            </span>
            <span class="hidden md:block text-sm font-medium text-gray-700">
              {{ authStore.user?.name }}
            </span>
            <svg
              class="w-5 h-5 md:w-4 md:h-4 text-gray-500 transition-transform"
              :class="showUserMenu ? 'rotate-180' : ''"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          <!-- Dropdown Menu -->
          <div
            v-if="showUserMenu"
            @click.stop
            role="menu"
            class="absolute right-0 md:right-0 left-0 md:left-auto mt-2 w-full md:w-52 bg-[rgba(168,218,220,0.95)] backdrop-blur-md rounded-xl border border-gray-200/50 py-2 z-50 shadow-lg animate-slideDown"
          >
            <div class="px-4 py-3 border-b border-gray-100">
              <p class="text-base md:text-sm font-medium text-gray-900">
                {{ authStore.user?.name }}
              </p>
              <p class="text-sm md:text-xs text-gray-500 truncate">{{ authStore.user?.email }}</p>
            </div>
            <router-link
              to="/profile"
              @click="showUserMenu = false; menuOpen = false"
              role="menuitem"
              class="block w-full text-left px-4 py-3 md:py-2 text-base md:text-sm text-gray-700 hover:bg-gray-100/60 transition-colors focus:outline-none focus:bg-gray-100/60"
            >
              Profile
            </router-link>
            <button
              @click="logout"
              role="menuitem"
              class="w-full text-left px-4 py-3 md:py-2 text-base md:text-sm text-red-600 hover:bg-red-50/60 transition-colors cursor-pointer focus:outline-none focus:bg-red-50/60"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
