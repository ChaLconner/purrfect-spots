<template>
  <div ref="wrapperRef" class="relative">
    <button
      class="group relative w-10 h-10 flex items-center justify-center rounded-full bg-[var(--color-btn-accent-e)] border-2 border-[var(--color-btn-accent-a)] text-[var(--color-btn-accent-a)] shrink-0 transition-all duration-[150ms] ease-out hover:bg-[var(--color-btn-accent-d)] hover:translate-y-[0.1rem] active:translate-y-[0.25rem]"
      :class="{
        'bg-[var(--color-btn-accent-a)] text-white border-[var(--color-btn-accent-a)]': isOpen,
      }"
      style="transform-style: preserve-3d; will-change: transform"
      aria-label="Notifications"
      @click="toggleDropdown"
    >
      <span
        class="absolute inset-0 bg-[var(--color-btn-accent-c)] rounded-[inherit] shadow-[0_0_0_2px_var(--color-btn-accent-b),_0_0.2rem_0_0_var(--color-btn-accent-a)] transition-all duration-[150ms] ease-out -z-10 group-hover:translate-y-[0.15rem] group-active:translate-y-0 group-active:translate-z-[-1em] group-active:shadow-[0_0_0_2px_var(--color-btn-accent-b),_0_0.1em_0_0_var(--color-btn-accent-b)]"
        :class="{
          'bg-[#8b4520] shadow-[0_0_0_2px_#a65d37,0_0.2rem_0_0_#5d321d]': isOpen,
        }"
        style="transform: translate3d(0, 0.2rem, -1em); will-change: transform"
      ></span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5 relative z-[1]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2.5"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
      <span
        v-if="unreadCount > 0"
        class="absolute top-1.5 right-1.5 translate-x-1/4 -translate-y-1/4 bg-terracotta text-white text-[10px] font-bold rounded-full h-4 w-4 flex items-center justify-center shadow-lg border-2 border-white animate-[badge-pulse_2s_infinite] z-[2]"
      >
        {{ unreadCount > 9 ? '9+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <Transition
      enter-active-class="animate-ghibli-pop"
      leave-active-class="transition-all duration-200 ease-out"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 -translate-y-2.5"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 mt-3 w-80 max-w-[calc(100vw-2rem)] origin-top-right bg-gradient-to-br from-[#fffdfa]/98 to-[#faf6ec]/98 backdrop-blur-lg border border-brown/15 rounded-3xl shadow-[0_10px_40px_-10px_rgba(139,77,45,0.25),0_4px_12px_rgba(0,0,0,0.05)] overflow-hidden z-50"
      >
        <div class="flex justify-between items-center px-4 py-3 bg-brown/3 border-b border-brown/8">
          <h3 class="font-heading font-extrabold text-brown text-sm tracking-wide">
            Notifications
          </h3>
          <button
            class="text-terracotta bg-transparent border-none cursor-pointer transition-all duration-200 hover:text-brown-light hover:text-shadow-[0_0_8px_rgba(214,122,79,0.2)] text-[11px] font-bold uppercase tracking-wider"
            @click="store.markAllRead"
          >
            Mark all read
          </button>
        </div>

        <div class="max-h-[400px] overflow-y-auto custom-scrollbar">
          <div
            v-if="store.notifications.length === 0 && !store.isLoadingMore"
            class="py-12 px-6 text-center"
          >
            <div
              class="w-12 h-12 mx-auto mb-3 opacity-20 bg-[url('/empty-bell.svg')] bg-contain bg-center bg-no-repeat"
            ></div>
            <p class="text-sm font-body font-medium text-brown-light italic">
              No notifications yet... quiet as a napping kitten.
            </p>
          </div>
          <div
            v-for="notification in store.notifications"
            :key="notification.id"
            class="p-4 transition-all duration-300 cursor-pointer relative border-b border-brown/5 hover:bg-brown/3"
            :class="{ 'bg-terracotta/4': !notification.is_read }"
            @click="handleRead(notification)"
          >
            <div class="flex gap-4">
              <div class="relative">
                <img
                  :src="notification.actor_picture || '/default-avatar.svg'"
                  class="w-10 h-10 rounded-full flex-shrink-0 object-cover border-2 border-white shadow-sm"
                  alt="Actor"
                />
                <div
                  v-if="!notification.is_read"
                  class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-terracotta border-2 border-[#fffdfa] rounded-full shadow-[0_2px_4px_rgba(214,122,79,0.3)]"
                ></div>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-[13px] font-bold text-brown truncate font-heading mb-0.5">
                  {{ notification.title }}
                </p>
                <p
                  class="text-[11px] font-body font-medium text-brown-light leading-relaxed line-clamp-2"
                >
                  {{ notification.message }}
                </p>
                <p
                  class="text-[9px] font-bold text-terracotta/60 mt-1.5 uppercase tracking-tighter"
                >
                  {{ formatDate(notification.created_at) }}
                </p>
              </div>
            </div>
          </div>

          <!-- Infinite Scroll Trigger Element -->
          <div
            v-if="store.hasMore"
            ref="infiniteTrigger"
            class="h-10 w-full flex items-center justify-center p-4"
          >
            <div
              v-if="store.isLoadingMore"
              class="w-5 h-5 border-2 border-terracotta/30 border-t-terracotta rounded-full animate-spin"
            ></div>
          </div>
          <!-- End of list marker -->
          <div
            v-else-if="store.notifications.length > 0"
            class="py-4 text-center text-[10px] font-medium text-brown-light/60 uppercase tracking-widest"
          >
            End of notifications
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue';
import { useNotificationStore } from '@/store';
import { useRouter } from 'vue-router';
import type { Notification } from '@/services/notificationService';

const store = useNotificationStore();
const router = useRouter();
const isOpen = ref(false);
const unreadCount = computed(() => store.unreadCount);
const wrapperRef = ref<HTMLElement | null>(null);
const infiniteTrigger = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;

function toggleDropdown(): void {
  isOpen.value = !isOpen.value;
}

function handleRead(notification: Notification): void {
  if (!notification.is_read) {
    store.markRead(notification.id);
  }
  // Navigate if resource exists
  if (notification.resource_type === 'photo' && notification.resource_id) {
    // Navigating to profile or gallery
    router.push({ path: '/profile', query: { image: notification.resource_id } });
    isOpen.value = false;
  }
}

// Calculate time diff
function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = (now.getTime() - d.getTime()) / 1000; // seconds

  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString();
}

// Close on click outside
function handleClickOutside(event: MouseEvent): void {
  const target = event.target as HTMLElement;
  if (wrapperRef.value && !wrapperRef.value.contains(target)) {
    isOpen.value = false;
  }
}

// Setup IntersectionObserver for Infinite Loading
function setupObserver() {
  if (observer) observer.disconnect();

  observer = new IntersectionObserver(
    (entries) => {
      // Only fetch more when the trigger element comes into view and we are not already loading
      if (entries[0].isIntersecting && store.hasMore && !store.isLoadingMore) {
        store.fetchMoreNotifications();
      }
    },
    {
      root: null,
      rootMargin: '0px',
      threshold: 0.1,
    }
  );

  if (infiniteTrigger.value) {
    observer.observe(infiniteTrigger.value);
  }
}

// Watch dropdown toggle to initialize the observer
watch(isOpen, async (newVal) => {
  if (newVal) {
    if (store.notifications.length === 0) {
      await store.fetchNotifications();
    }
    // Wait for DOM to render to find the trigger element
    await nextTick();
    if (store.hasMore) {
      setupObserver();
    }
  } else {
    if (observer) observer.disconnect();
  }
});

// Clean up observer if it's the element dynamically replaced
watch(infiniteTrigger, (newVal) => {
  if (newVal && isOpen.value) {
    setupObserver();
  }
});

onMounted(() => {
  store.fetchNotifications();
  store.subscribeToNotifications();
  document.addEventListener('mousedown', handleClickOutside);
});

onUnmounted(() => {
  if (observer) observer.disconnect();
  store.unsubscribe();
  document.removeEventListener('mousedown', handleClickOutside);
});
</script>
