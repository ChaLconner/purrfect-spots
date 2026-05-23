<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../../store/authStore';
import { AuthService } from '../../services/authService';
import { showSuccess } from '../../store/toast';
import { isDev } from '../../utils/env';

const { t } = useI18n();
const showUserMenu = ref(false);
const router = useRouter();
const authStore = useAuthStore();
const avatarLoaded = ref(false);
const avatarLoadFailed = ref(false);

const avatarSrc = computed(() => authStore.user?.picture || '');
const userInitials = computed(() => {
  const displayName = authStore.user?.name?.trim();
  const emailName = authStore.user?.email?.split('@')[0]?.trim();
  const source = displayName || emailName || 'User';
  const parts = source.split(/\s+/).filter(Boolean);

  if (parts.length > 1) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return source.slice(0, 2).toUpperCase();
});

// Close user menu when clicking outside
const handleClickOutside = (event: Event): void => {
  const target = event.target as HTMLElement;
  if (showUserMenu.value && target && !target.closest('.user-menu-container')) {
    showUserMenu.value = false;
  }
};

const handleImageLoad = (): void => {
  avatarLoaded.value = true;
};

const handleImageError = (): void => {
  avatarLoaded.value = false;
  avatarLoadFailed.value = true;
};

const logout = async (): Promise<void> => {
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
    showSuccess(t('toast.loggedOut'));
    showUserMenu.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

watch(avatarSrc, () => {
  avatarLoaded.value = false;
  avatarLoadFailed.value = false;
});
</script>

<template>
  <div class="relative user-menu-container">
    <button
      class="group relative flex items-center justify-center h-10 w-10 p-[0.15rem] bg-btn-shade-e border-2 border-btn-shade-a rounded-full cursor-pointer shrink-0 transition-all duration-[150ms] ease-out hover:bg-btn-shade-d hover:translate-y-[0.1rem] active:translate-y-[0.25rem]"
      style="transform-style: preserve-3d; will-change: transform"
      :aria-expanded="showUserMenu"
      aria-label="User menu"
      @click="showUserMenu = !showUserMenu"
    >
      <span
        class="absolute inset-0 bg-btn-shade-c rounded-[inherit] shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.2rem_0_0_var(--color-btn-shade-a)] transition-all duration-[150ms] ease-out -z-10 group-hover:translate-y-[0.15rem] group-active:translate-y-0 group-active:translate-z-[-1em] group-active:shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.1em_0_0_var(--color-btn-shade-b)]"
        style="transform: translate3d(0, 0.2rem, -1em); will-change: transform"
      ></span>
      <span
        data-testid="user-avatar-fallback"
        class="absolute inset-[0.15rem] z-10 flex items-center justify-center rounded-full border-2 border-btn-shade-a bg-gradient-to-br from-[#eef5ea] via-[#dbe9d4] to-[#c9ddc4] font-accent text-[0.78rem] font-extrabold leading-none tracking-[-0.04em] text-btn-shade-a shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
        aria-hidden="true"
      >
        {{ userInitials }}
      </span>
      <img
        v-if="avatarSrc && !avatarLoadFailed"
        data-testid="user-avatar-image"
        :src="avatarSrc"
        :alt="authStore.user?.name || 'User'"
        class="relative z-20 w-full h-full rounded-full object-cover border-2 border-btn-shade-a shadow-[0_2px_4px_rgba(106,163,137,0.2)] shrink-0 bg-stone-100 transition-opacity duration-200 ease-out"
        :class="avatarLoaded ? 'opacity-100' : 'opacity-0'"
        decoding="async"
        @load="handleImageLoad"
        @error="handleImageError"
      />
    </button>

    <!-- Dropdown Menu -->
    <div
      v-if="showUserMenu"
      class="absolute top-[calc(100%+0.75rem)] right-0 min-w-[210px] bg-btn-shade-e border-2 border-btn-shade-a rounded-2xl shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.5em_0_0_var(--color-btn-shade-a)] overflow-hidden z-[100] origin-top-right animate-[ghibli-pop_0.3s_cubic-bezier(0.34,1.56,0.64,1)]"
      @click.stop
    >
      <div class="px-4 py-3.5 bg-btn-shade-d">
        <p class="m-0 font-accent text-sm font-semibold text-btn-shade-a flex items-center gap-2">
          {{ authStore.user?.name }}
          <span v-if="authStore.user?.is_pro" class="bg-gradient-to-r from-yellow-400 to-amber-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-sm uppercase tracking-wider shadow-sm">
            PRO
          </span>
        </p>
        <p
          class="m-0 mt-0.5 font-accent text-[0.7rem] text-btn-shade-b overflow-hidden text-ellipsis"
        >
          {{ authStore.user?.email }}
        </p>
      </div>
      <div class="h-[2px] bg-btn-shade-b"></div>
      <router-link
        v-if="!authStore.user?.is_pro"
        to="/subscription"
        class="block w-full px-4 py-3 font-accent text-[0.85rem] font-bold text-amber-600 text-left bg-amber-50 border-none cursor-pointer transition-all duration-[175ms] ease-in-out hover:bg-amber-100 hover:translate-x-1"
        @click="showUserMenu = false"
      >
        🌟 {{ $t('subscription.proPlan.upgrade') || 'Upgrade to PRO' }}
      </router-link>
      <router-link
        to="/profile"
        class="block w-full px-4 py-3 font-accent text-[0.85rem] font-semibold text-btn-shade-a text-left bg-transparent border-none cursor-pointer transition-all duration-[175ms] ease-in-out hover:bg-btn-shade-d hover:translate-x-1"
        @click="showUserMenu = false"
      >
        {{ $t('nav.profile') }}
      </router-link>
      <button
        class="block w-full px-4 py-3 font-accent text-[0.85rem] font-semibold text-left bg-transparent border-none cursor-pointer transition-all duration-[175ms] ease-in-out hover:translate-x-1 text-[#dc4a4a] hover:bg-[#ffeeee]"
        @click="logout"
      >
        {{ $t('auth.logout') }}
      </button>

      <div v-if="authStore.canAccessAdmin" class="h-[2px] bg-btn-shade-b"></div>
      <router-link
        v-if="authStore.canAccessAdmin"
        to="/admin"
        class="block w-full px-4 py-3 font-accent text-[0.85rem] font-semibold text-btn-shade-a text-left bg-transparent border-none cursor-pointer transition-all duration-[175ms] ease-in-out hover:bg-btn-shade-d hover:translate-x-1"
        @click="showUserMenu = false"
      >
        {{ $t('nav.adminPanel') }}
      </router-link>
    </div>
  </div>
</template>
