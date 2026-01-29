<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../store/authStore';
import { AuthService } from '../../services/authService';
import { showSuccess } from '../../store/toast';
import { isDev } from '../../utils/env';

const showUserMenu = ref(false);
const router = useRouter();
const authStore = useAuthStore();

// Close user menu when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (showUserMenu.value && target && !target.closest('.user-menu-container')) {
    showUserMenu.value = false;
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
      console.error('Logout error:', error);
    }
    // Continue to clear auth even if backend fails
  } finally {
    authStore.clearAuth();
    router.push('/');
    showSuccess('Logged out successfully');
    showUserMenu.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
  <div class="user-menu-container">
    <button class="user-btn" :aria-expanded="showUserMenu" @click="showUserMenu = !showUserMenu">
      <img
        :src="authStore.user?.picture || '/default-avatar.svg'"
        :alt="authStore.user?.name || 'User'"
        class="user-avatar"
        @error="handleImageError"
      />
      <span class="user-name">{{ authStore.user?.name }}</span>
      <svg
        class="chevron-icon"
        :class="{ rotate: showUserMenu }"
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
      <router-link to="/profile" class="dropdown-item" @click="showUserMenu = false">
        Profile
      </router-link>
      <button class="dropdown-item logout" @click="logout">Logout</button>
    </div>
  </div>
</template>

<style scoped>
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
</style>
