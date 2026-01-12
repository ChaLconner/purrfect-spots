<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../store/authStore";
import { catStore, catCount, setSearchQuery } from "../store/cats";
import { AuthService } from "../services/authService";
import { showError, showSuccess } from "../store/toast";
import { isDev } from "../utils/env";

// Icons
import Logo from "./icons/logo.vue";
import Paw from "./icons/paw.vue";
import Search from "./icons/search.vue";
import MapIcon from "./icons/map.vue";
import Upload from "./icons/upload.vue";
import Gallery from "./icons/gallery.vue";

const menuOpen = ref(false);
const showUserMenu = ref(false);
const searchQuery = ref("");
const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// Close user menu when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (showUserMenu.value && target && !target.closest(".user-menu-container")) {
    showUserMenu.value = false;
  }
};

// Initialize search from route query
onMounted(() => {
  if (route.query.search) {
    searchQuery.value = route.query.search as string;
  }
});

// Watch for route changes to update search
watch(() => route.query.search, (newSearch) => {
  if (newSearch) {
    searchQuery.value = newSearch as string;
  }
});

function goHome() {
  router.push("/");
}

const handleSearch = () => {
  setSearchQuery(searchQuery.value);
  
  if (route.path !== '/map' && route.path !== '/') {
    router.push({ path: "/map", query: { search: searchQuery.value } });
  }
};

watch(searchQuery, (newValue) => {
  if (!newValue.trim()) {
    setSearchQuery('');
  }
});

const clearSearch = () => {
  searchQuery.value = "";
  setSearchQuery("");
  if (route.path === '/map') {
    // Update URL without reloading if on map
    router.replace({ ...route, query: { ...route.query, search: undefined } });
  }
};

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement;
  if (!target.src.includes('default-avatar.svg')) {
    target.src = '/default-avatar.svg';
  }
};

const logout = async () => {
  try {
    await AuthService.logout();
  } catch (error) {
    if (isDev()) {
      console.error("Logout error:", error);
    }
    // Continue to clear auth even if backend fails
  } finally {
    authStore.clearAuth();
    router.push("/");
    showSuccess('Logged out successfully');
  }
};

onMounted(() => {
  // authStore initialized automatically
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>

<template>
  <nav class="navbar-container">
    <div class="navbar-content">
      <!-- Left Section: Logo + Brand + Cat Counter -->
      <div class="left-section">
        <div class="brand-section" @click="goHome">
          <Logo class="brand-logo" />
          <span class="brand-name">Purrfect Spots</span>
        </div>

        <div v-if="route.path === '/map' || route.path === '/'" class="cat-counter">
          <div class="paw-icon-wrapper">
            <Paw class="paw-icon" />
          </div>
          <div class="cat-counter-text">
            <span class="cat-count">{{ catCount }} cats</span>
            <span class="cat-subtitle">spotted nearby</span>
          </div>
        </div>
      </div>

      <!-- Center Section: Search Box -->
      <div class="center-section">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="Find a spot..."
            class="search-input"
            @keyup.enter="handleSearch"
          />
          <button 
            v-if="searchQuery" 
            class="search-btn clear-mode" 
            @click="clearSearch"
            aria-label="Clear search"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
          <button v-else class="search-btn" @click="handleSearch" aria-label="Search">
            <Search class="search-icon" />
          </button>
        </div>
      </div>

      <!-- Right Section: Navigation + Login -->
      <div class="right-section">
        <div class="nav-links">
          <router-link 
            to="/map" 
            class="nav-link"
            :class="{ active: route.path === '/map' || route.path === '/' }"
          >
            <MapIcon class="nav-icon" />
            <span>Map</span>
          </router-link>
          
          <router-link 
            to="/upload" 
            class="nav-link"
            :class="{ active: route.path === '/upload' }"
          >
            <Upload class="nav-icon" />
            <span>Upload</span>
          </router-link>
          
          <router-link 
            to="/gallery" 
            class="nav-link"
            :class="{ active: route.path === '/gallery' }"
          >
            <Gallery class="nav-icon" />
            <span>Gallery</span>
          </router-link>
        </div>

        <!-- Login Button (not authenticated) -->
        <div v-if="!authStore.isAuthenticated">
          <router-link 
            to="/login" 
            class="login-btn"
          >
            Login
          </router-link>
        </div>

        <!-- User Menu (authenticated) -->
        <div v-else class="user-menu-container">
          <button
            @click="showUserMenu = !showUserMenu"
            class="user-btn"
            :aria-expanded="showUserMenu"
          >
            <img
              :src="authStore.user?.picture || '/default-avatar.svg'"
              :alt="authStore.user?.name || 'User'"
              class="user-avatar"
              @error="handleImageError"
            />
            <span class="user-name">{{ authStore.user?.name }}</span>
            <svg
              class="chevron-icon"
              :class="{ 'rotate': showUserMenu }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown Menu -->
          <div v-if="showUserMenu" class="user-dropdown" @click.stop>
            <div class="dropdown-header">
              <p class="dropdown-name">{{ authStore.user?.name }}</p>
              <p class="dropdown-email">{{ authStore.user?.email }}</p>
            </div>
            <div class="dropdown-divider"></div>
            <router-link
              to="/profile"
              class="dropdown-item"
              @click="showUserMenu = false"
            >
              Profile
            </router-link>
            <button class="dropdown-item logout" @click="logout(); showUserMenu = false">
              Logout
            </button>
          </div>
        </div>
      </div>

      <!-- Hamburger button (mobile only) -->
      <button
        class="hamburger-btn"
        @click="menuOpen = !menuOpen"
        :aria-expanded="menuOpen"
        aria-controls="mobile-menu"
        aria-label="Toggle navigation menu"
      >
        <div class="hamburger-lines">
          <span
            class="hamburger-line"
            :class="menuOpen ? 'rotate-45 translate-y-0' : '-translate-y-2'"
          ></span>
          <span
            class="hamburger-line"
            :class="menuOpen ? 'opacity-0' : 'opacity-100'"
          ></span>
          <span
            class="hamburger-line"
            :class="menuOpen ? '-rotate-45 translate-y-0' : 'translate-y-2'"
          ></span>
        </div>
      </button>
    </div>

    <!-- Mobile Menu -->
    <div
      id="mobile-menu"
      class="mobile-menu"
      :class="{ 'mobile-menu-open': menuOpen }"
      role="navigation"
      aria-label="Mobile navigation"
    >
      <!-- Mobile Search -->
      <div class="mobile-search-section">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="Find a spot..."
            class="search-input"
            @keyup.enter="handleSearch"
          />
          <button 
            v-if="searchQuery" 
            class="search-btn clear-mode" 
            @click="clearSearch"
            aria-label="Clear search"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
          <button v-else class="search-btn" @click="handleSearch" aria-label="Search">
            <Search class="search-icon" />
          </button>
        </div>
      </div>

      <!-- Mobile Navigation Links -->
      <div class="mobile-nav-links">
        <router-link 
          to="/map" 
          class="mobile-nav-link"
          @click="menuOpen = false"
        >
          <MapIcon class="nav-icon" />
          <span>Map</span>
        </router-link>
        
        <router-link 
          to="/upload" 
          class="mobile-nav-link"
          @click="menuOpen = false"
        >
          <Upload class="nav-icon" />
          <span>Upload</span>
        </router-link>
        
        <router-link 
          to="/gallery" 
          class="mobile-nav-link"
          @click="menuOpen = false"
        >
          <Gallery class="nav-icon" />
          <span>Gallery</span>
        </router-link>

        <router-link 
          v-if="!authStore.isAuthenticated"
          to="/login" 
          class="mobile-nav-link login"
          @click="menuOpen = false"
        >
          <span>Login</span>
        </router-link>

        <button 
          v-else
          class="mobile-nav-link logout"
          @click="logout(); menuOpen = false"
        >
          <span>Logout</span>
        </button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar-container {
  position: sticky;
  top: 0;
  z-index: 50;
  margin: 1rem 2rem;
}

.navbar-content {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(
    135deg,
    rgba(255, 253, 250, 0.95) 0%,
    rgba(250, 245, 235, 0.95) 50%,
    rgba(255, 253, 250, 0.95) 100%
  );
  backdrop-filter: blur(12px);
  border-radius: 2rem;
  border: 1px solid rgba(139, 90, 43, 0.1);
  box-shadow: 
    0 4px 20px rgba(139, 90, 43, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  position: relative;
}

/* Left Section */
.left-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
  transition: all 0.3s ease;
}

.brand-section:hover {
  /* background removed */
}

.brand-logo {
  width: 2.25rem;
  height: 2.25rem;
  filter: drop-shadow(0 2px 4px rgba(201, 123, 73, 0.3));
}

.brand-name {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
  color: #5a4a3a;
  white-space: nowrap;
}

/* Cat Counter */
.cat-counter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border-radius: 1.25rem;
  background: rgba(139, 90, 43, 0.05);
  border: 1px solid rgba(139, 90, 43, 0.1);
}

.paw-icon-wrapper {
  width: 1.75rem;
  height: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.paw-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: #d4845a;
}

.cat-counter-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.cat-count {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-weight: 700;
  font-size: 0.8rem;
  color: #5a4a3a;
}

.cat-subtitle {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.6rem;
  color: #8b7355;
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
  color: #b0a090;
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
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.1));
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
  gap: 0.25rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border-radius: 2rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  color: #8b7355;
  text-decoration: none;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  background: transparent;
  position: relative;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.8);
  color: #d4845a;
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 20px rgba(212, 132, 90, 0.2);
}

.nav-link:active {
  transform: translateY(1px) scale(0.94);
  box-shadow: 0 2px 8px rgba(212, 132, 90, 0.15);
  transition: all 0.1s ease;
}

.nav-link.active {
  background: linear-gradient(135deg, rgba(212, 132, 90, 0.15), rgba(212, 132, 90, 0.05));
  color: #c97b49;
  font-weight: 700;
  box-shadow: inset 0 2px 6px rgba(139, 90, 43, 0.05);
}

.nav-icon {
  width: 1.1rem;
  height: 1.1rem;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.nav-link:hover .nav-icon {
  transform: rotate(-12deg) scale(1.15);
}

.nav-link:active .nav-icon {
  transform: rotate(-12deg) scale(0.9);
}

/* Login Button */
.login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1.25rem;
  background: linear-gradient(135deg, #c97b49 0%, #b06a3d 100%);
  border: none;
  border-radius: 1.25rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(201, 123, 73, 0.3);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(201, 123, 73, 0.4);
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

/* Hamburger Button */
.hamburger-btn {
  display: none;
  padding: 0.75rem;
  border-radius: 50%;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #5a4a3a;
}

.hamburger-btn:hover {
  background: rgba(139, 90, 43, 0.1);
}

.hamburger-lines {
  position: relative;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.hamburger-line {
  position: absolute;
  width: 1.5rem;
  height: 2px;
  background: currentColor;
  border-radius: 2px;
  transition: all 0.3s ease;
}

/* Mobile Menu */
.mobile-menu {
  display: none;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  margin-top: 0.75rem;
  background: linear-gradient(
    135deg,
    rgba(255, 253, 250, 0.98) 0%,
    rgba(250, 245, 235, 0.98) 100%
  );
  backdrop-filter: blur(12px);
  border-radius: 1.5rem;
  border: 1px solid rgba(139, 90, 43, 0.1);
  box-shadow: 0 4px 20px rgba(139, 90, 43, 0.1);
}

.mobile-menu-open {
  display: flex;
}

.mobile-search-section {
  margin-bottom: 0.5rem;
}

.mobile-search-section .search-box {
  width: 100%;
}

.mobile-nav-links {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 1rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
  color: #5a4a3a;
  text-decoration: none;
  transition: all 0.3s ease;
}

.mobile-nav-link:hover {
  background: rgba(255, 255, 255, 0.9);
}

.mobile-nav-link .nav-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #d4845a;
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.mobile-nav-link:active .nav-icon {
  transform: scale(0.9);
}

.mobile-nav-link.login {
  background: linear-gradient(135deg, #c97b49 0%, #b06a3d 100%);
  color: white;
  border: none;
}

.mobile-nav-link.logout {
  color: #dc4a4a;
  border-color: rgba(220, 74, 74, 0.2);
  cursor: pointer;
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
  
  .nav-link span {
    display: none;
  }
  
  .nav-link {
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
