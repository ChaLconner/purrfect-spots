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

/* 3D User Button */
.user-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  height: 2.5rem;
  padding: 0 0.75rem 0 0.25rem;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 2rem;
  cursor: pointer;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
  flex-shrink: 0;
  transform-style: preserve-3d;
}

.user-btn::before {
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
    0 0.3em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.3em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.user-btn:hover {
  background: var(--color-btn-shade-d);
  transform: translate(0, 0.15em);
}

.user-btn:hover::before {
  transform: translate3d(0, 0.3em, -1em);
}

.user-btn:active {
  transform: translate(0, 0.3em);
}

.user-btn:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.1em 0 0 var(--color-btn-shade-b);
}

.user-avatar {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-btn-shade-a);
  box-shadow: 0 2px 4px rgba(106, 163, 137, 0.2);
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.user-name {
  font-family: 'Quicksand', sans-serif;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-btn-shade-a);
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

.chevron-icon {
  width: 0.8rem;
  height: 0.8rem;
  color: var(--color-btn-shade-a);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  z-index: 1;
}

.chevron-icon.rotate {
  transform: rotate(180deg);
}

/* 3D Themed Dropdown */
.user-dropdown {
  position: absolute;
  top: calc(100% + 0.75rem);
  right: 0;
  min-width: 210px;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 1rem;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.5em 0 0 var(--color-btn-shade-a);
  overflow: hidden;
  z-index: 100;
  transform-origin: top right;
  animation: ghibli-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes ghibli-pop {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.dropdown-header {
  padding: 0.875rem 1rem;
  background: var(--color-btn-shade-d);
}

.dropdown-name {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-btn-shade-a);
  margin: 0;
}

.dropdown-email {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.7rem;
  color: var(--color-btn-shade-b);
  margin: 0.125rem 0 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-divider {
  height: 2px;
  background: var(--color-btn-shade-b);
}

/* 3D Dropdown Items */
.dropdown-item {
  position: relative;
  display: block;
  width: 100%;
  padding: 0.75rem 1rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-btn-shade-a);
  text-decoration: none;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 175ms ease;
}

.dropdown-item:hover {
  background: var(--color-btn-shade-d);
  transform: translateX(4px);
}

.dropdown-item.logout {
  color: #dc4a4a;
}

.dropdown-item.logout:hover {
  background: #ffeeee;
}
</style>
