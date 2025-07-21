<script setup lang="ts">
import logo from "../components/icons/logo.vue";
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { authStore, initializeAuth, clearAuth } from "../store/auth";
import { AuthService } from "../services/authService";
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
    console.error("Logout error:", error);
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
  <nav
    class="flex flex-col md:flex-row items-center justify-between px-6 py-4 bg-white shadow-md"
  >
    <div
      class="flex items-center mb-2 md:mb-0 space-x-2 cursor-pointer"
      @click="goHome"
    >
      <logo class="w-8 h-8" />
      <div class="text-lg font-bold whitespace-nowrap">Purrfect Spots</div>
    </div>
    <!-- Hamburger button (mobile only) -->
    <button
      class="md:hidden p-2 rounded focus:outline-none"
      @click="menuOpen = !menuOpen"
      aria-label="Toggle menu"
    >
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 6h16M4 12h16M4 18h16"
        />
      </svg>
    </button>
    <!-- Menu -->
    <div
      class="flex-col md:flex-row items-center gap-4 md:gap-6 md:flex"
      :class="menuOpen ? 'flex' : 'hidden'"
    >
      <router-link to="/" class="hover:underline"><Map/> Map </router-link>
      <router-link to="/upload" class="hover:underline"><Upload/> Upload </router-link>
      <router-link to="/gallery" class="hover:underline"><gallery/> Gallery </router-link>

      <!-- Authentication Section -->
      <div v-if="!authStore.isAuthenticated" class="flex items-center gap-2">
        <router-link
          to="/login"
          class="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200 font-medium"
        >
          Login
        </router-link>
      </div>

      <!-- User Menu (when authenticated) -->
      <div v-else class="relative flex items-center gap-4">
        <!-- User Avatar & Dropdown -->
        <div class="relative user-menu-container">
          <button
            @click="showUserMenu = !showUserMenu"
            class="flex items-center gap-2 focus:outline-none"
          >
            <img
              :src="
                authStore.user?.picture ||
                'https://randomuser.me/api/portraits/men/32.jpg'
              "
              :alt="authStore.user?.name || 'User Avatar'"
              class="w-8 h-8 rounded-full border border-gray-300"
            />
            <span class="hidden md:block text-sm font-medium text-gray-700">
              {{ authStore.user?.name }}
            </span>
            <svg
              class="w-4 h-4 text-gray-500"
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
            class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50"
          >
            <div class="px-4 py-2 border-b border-gray-100">
              <p class="text-sm font-medium text-gray-900">
                {{ authStore.user?.name }}
              </p>
              <p class="text-xs text-gray-500">{{ authStore.user?.email }}</p>
            </div>
            <router-link
              to="/profile"
              @click="showUserMenu = false"
              class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              โปรไฟล์
            </router-link>
            <button
              @click="logout"
              class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
            >
              ออกจากระบบ
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
