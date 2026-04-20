<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue';
import { useAuthStore } from '../../store/authStore';
import NavLink from './NavLink.vue';
import ProfileIcon from '../icons/profile.vue';

const authStore = useAuthStore();

// Show authenticated UI immediately from cache while background refresh runs.
// If auth status is still hydrating and no cached user exists, keep showing normal guest UI.
const showAuthenticatedActions = computed(() => authStore.isAuthenticated);
const showGuestLogin = computed(() => !authStore.isAuthenticated);

const UserMenu = defineAsyncComponent({
  loader: () => import('./UserMenu.vue'),
  suspensible: false,
});

const NotificationBell = defineAsyncComponent({
  loader: () => import('../ui/NotificationBell.vue'),
  suspensible: false,
});
</script>

<template>
  <!-- Guest/default: keep normal UI while session hydration runs in background -->
  <template v-if="showGuestLogin">
    <div class="hidden xl:flex items-center gap-2 min-w-[5.5rem] justify-end">
      <NavLink to="/login" variant="accent" :label="$t('auth.login')">
        <template #icon>
          <ProfileIcon class="relative z-10 w-[1.1rem] h-[1.1rem]" />
        </template>
      </NavLink>
    </div>
  </template>

  <!-- Authenticated: show immediately from cached state, updates silently in background -->
  <template v-else-if="showAuthenticatedActions">
    <div class="flex items-center gap-2 min-w-[5.5rem] justify-end">
      <NotificationBell />
      <UserMenu />
    </div>
  </template>

  <!-- Fallback: reserve space -->
  <template v-else>
    <div class="hidden xl:block min-w-[5.5rem] h-10" aria-hidden="true"></div>
  </template>
</template>
