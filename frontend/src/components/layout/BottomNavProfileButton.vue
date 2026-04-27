<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../../store/authStore';
import ProfileIcon from '../icons/profile.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const isActive = computed(() => route.path === '/profile' || route.path === '/login');
const isAuthenticated = computed(() => authStore.isAuthenticated);

const navigateToProfile = (): void => {
  if (isAuthenticated.value) {
    router.push('/profile');
  } else {
    router.push('/login');
  }
};
</script>

<template>
  <button
    class="group flex flex-col items-center flex-1 py-1 px-2 rounded-xl transition-all duration-300 active:scale-95"
    :class="isActive ? 'text-btn-shade-a' : 'text-btn-shade-b hover:text-btn-shade-c'"
    :aria-label="isAuthenticated ? $t('nav.profile') : $t('auth.login')"
    @click="navigateToProfile"
  >
    <div
      class="flex justify-center items-center w-10 h-10 rounded-full transition-all duration-300"
      :class="
        isActive
          ? 'bg-btn-shade-e text-btn-shade-a -translate-y-0.5 shadow-[0_2px_4px_rgba(0,0,0,0.1)] border border-btn-shade-b'
          : ''
      "
    >
      <ProfileIcon class="w-6 h-6" />
    </div>
    <span class="text-xs font-bold mt-1 font-accent">{{
      isAuthenticated ? $t('nav.profile') : $t('auth.login')
    }}</span>
  </button>
</template>
