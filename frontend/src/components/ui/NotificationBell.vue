<template>
  <div class="relative notification-wrapper">
    <button
      class="relative rounded-full transition-all duration-300 bell-button"
      :class="{ 'bell-active': isOpen }"
      aria-label="Notifications"
      @click="toggleDropdown"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5 icon-bell"
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
        class="absolute top-1.5 right-1.5 bg-terracotta text-white text-[10px] font-bold rounded-full h-4 w-4 flex items-center justify-center shadow-lg border-2 border-white notification-badge"
      >
        {{ unreadCount > 9 ? '9+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <Transition name="ghibli-pop">
      <div v-if="isOpen" class="absolute right-0 mt-3 w-80 ghibli-dropdown overflow-hidden z-50">
        <div class="dropdown-header flex justify-between items-center px-4 py-3">
          <h3 class="font-heading font-extrabold text-brown text-sm tracking-wide">
            Notifications
          </h3>
          <button
            class="mark-read-btn text-[11px] font-bold uppercase tracking-wider"
            @click="store.markAllRead"
          >
            Mark all read
          </button>
        </div>

        <div class="notification-list custom-scrollbar">
          <div v-if="store.notifications.length === 0" class="empty-state py-12 px-6 text-center">
            <div class="empty-icon mb-3"></div>
            <p class="text-sm font-body font-medium text-brown-light italic">
              No notifications yet... quiet as a napping kitten.
            </p>
          </div>
          <div
            v-for="notification in store.notifications"
            :key="notification.id"
            class="notification-item p-4 transition-all duration-300 cursor-pointer relative"
            :class="{ unread: !notification.is_read }"
            @click="handleRead(notification)"
          >
            <div class="flex gap-4">
              <div class="actor-avatar-wrapper">
                <img
                  :src="notification.actor_picture || '/default-avatar.svg'"
                  class="w-10 h-10 rounded-full flex-shrink-0 object-cover border-2 border-white shadow-sm"
                  alt="Actor"
                />
                <div v-if="!notification.is_read" class="unread-dot-v2"></div>
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
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useNotificationStore } from '@/store';
import { useRouter } from 'vue-router';
import type { Notification } from '@/services/notificationService';

const store = useNotificationStore();
const router = useRouter();
const isOpen = ref(false);
const unreadCount = computed(() => store.unreadCount);

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
  const wrapper = document.querySelector('.notification-wrapper');
  if (wrapper && !wrapper.contains(target)) {
    isOpen.value = false;
  }
}

onMounted(() => {
  store.fetchNotifications();
  store.subscribeToNotifications();
  document.addEventListener('mousedown', handleClickOutside);
});

onUnmounted(() => {
  store.unsubscribe();
  document.removeEventListener('mousedown', handleClickOutside);
});
</script>

<style scoped>
/* 3D Bell Button - Terracotta */
.bell-button {
  position: relative;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-btn-accent-e);
  border: 2px solid var(--color-btn-accent-a);
  color: var(--color-btn-accent-a);
  flex-shrink: 0;
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.bell-button::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-accent-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-accent-b),
    0 0.3em 0 0 var(--color-btn-accent-a);
  transform: translate3d(0, 0.3em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.bell-button:hover {
  background: var(--color-btn-accent-d);
  transform: translate(0, 0.15em);
  color: var(--color-btn-accent-a);
}

.bell-button:hover::before {
  transform: translate3d(0, 0.3em, -1em);
}

.bell-button:active {
  transform: translate(0, 0.3em);
}

.bell-button:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-accent-b),
    0 0.1em 0 0 var(--color-btn-accent-b);
}

.bell-active {
  background: var(--color-btn-accent-a);
  color: white;
  border-color: var(--color-btn-accent-a);
}

.bell-active::before {
  background: #8b4520;
  box-shadow:
    0 0 0 2px #a65d37,
    0 0.3em 0 0 #5d321d;
}

.icon-bell {
  position: relative;
  z-index: 1;
}

.notification-badge {
  transform: translate(25%, -25%);
  animation: badge-pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 2;
}

@keyframes badge-pop {
  from {
    transform: translate(25%, -25%) scale(0);
  }
  to {
    transform: translate(25%, -25%) scale(1);
  }
}

.ghibli-dropdown {
  background: linear-gradient(135deg, rgba(255, 253, 250, 0.98) 0%, rgba(250, 246, 236, 0.98) 100%);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(139, 77, 45, 0.15);
  border-radius: 1.5rem;
  box-shadow:
    0 10px 40px -10px rgba(139, 77, 45, 0.25),
    0 4px 12px rgba(0, 0, 0, 0.05);
  transform-origin: top right;
}

.dropdown-header {
  background: rgba(139, 77, 45, 0.03);
  border-bottom: 1px solid rgba(139, 77, 45, 0.08);
}

.mark-read-btn {
  color: #d67a4f;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mark-read-btn:hover {
  color: #a65d37;
  text-shadow: 0 0 8px rgba(214, 122, 79, 0.2);
}

.notification-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  border-bottom: 1px solid rgba(139, 77, 45, 0.05);
}

.notification-item:hover {
  background: rgba(139, 77, 45, 0.03);
}

.notification-item.unread {
  background: rgba(214, 122, 79, 0.04);
}

.actor-avatar-wrapper {
  position: relative;
}

.unread-dot-v2 {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  background: #d67a4f;
  border: 2px solid #fffdfa;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(214, 122, 79, 0.3);
}

.dropdown-footer {
  background: rgba(139, 77, 45, 0.02);
  border-top: 1px solid rgba(139, 77, 45, 0.05);
}

.view-all-link {
  color: #8b4d2d;
  background: rgba(139, 77, 45, 0.05);
  font-family: 'Quicksand', sans-serif;
  text-decoration: none;
}

.view-all-link:hover {
  background: rgba(139, 77, 45, 0.1);
  color: #5d321d;
}

/* Scrollbar Styling */
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(139, 77, 45, 0.2);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 77, 45, 0.3);
}

/* Animations */
.ghibli-pop-enter-active {
  animation: ghibli-pop-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.ghibli-pop-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.ghibli-pop-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

@keyframes ghibli-pop-in {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>
