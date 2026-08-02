import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { NotificationService, type Notification } from '@/services/notificationService';
import { useAuthStore } from './authStore';
import { supabase } from '@/lib/supabase';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { ProfileService } from '@/services/profileService';
import { isDev } from '@/utils/env';

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([]);
  const serverUnreadCount = ref<number | null>(null);
  const unreadCount = computed(() => {
    if (serverUnreadCount.value !== null) {
      return serverUnreadCount.value;
    }
    return notifications.value.filter((n) => !n.is_read).length;
  });

  const authStore = useAuthStore();
  let subscription: RealtimeChannel | null = null;
  const actorCache = new Map<string, { name?: string; picture?: string }>();
  const MAX_ACTOR_CACHE = 200;
  const MAX_NOTIFICATIONS = 100;

  // Pagination states
  const isLoadingMore = ref(false);
  const isLoaded = ref(false);
  const hasMore = ref(true);
  const limit = 15;

  function resetState(): void {
    notifications.value = [];
    serverUnreadCount.value = null;
    isLoadingMore.value = false;
    isLoaded.value = false;
    hasMore.value = true;
    unsubscribe();
  }

  async function fetchUnreadCount(): Promise<void> {
    if (!authStore.isAuthenticated) return;
    try {
      const count = await NotificationService.getUnreadCount();
      if (typeof count === 'number') {
        serverUnreadCount.value = count;
      }
    } catch (e) {
      if (isDev()) {
        console.error('Failed to fetch unread notification count', e);
      }
    }
  }

  async function fetchNotifications(silent = false): Promise<void> {
    if (!authStore.isAuthenticated) return;
    try {
      if (!silent) {
        isLoadingMore.value = true;
      }
      
      const data = await NotificationService.getNotifications(limit, 0);
      notifications.value = data;
      isLoaded.value = true;
      
      if (data.length < limit) {
        hasMore.value = false;
      } else {
        hasMore.value = true;
      }
    } catch (e) {
      if (isDev()) {
        console.error('Failed to fetch notifications', e);
      }
    } finally {
      isLoadingMore.value = false;
    }
  }

  async function fetchMoreNotifications(): Promise<void> {
    if (!authStore.isAuthenticated || isLoadingMore.value || !hasMore.value) return;
    isLoadingMore.value = true;
    try {
      const currentOffset = notifications.value.length;
      const cursor = notifications.value.at(-1)?.created_at;
      const data = await NotificationService.getNotifications(limit, currentOffset, cursor);
      if (data.length > 0) {
        // Filter out duplicates just in case new notifications arrived in between
        const newIds = new Set(data.map((n) => n.id));
        const existingNotifications = notifications.value.filter((n) => !newIds.has(n.id));
        notifications.value = [...existingNotifications, ...data];
      }
      if (data.length < limit) {
        hasMore.value = false;
      }
    } catch (e) {
      if (isDev()) {
        console.error('Failed to fetch more notifications', e);
      }
    } finally {
      isLoadingMore.value = false;
    }
  }

  async function markRead(id: string): Promise<void> {
    try {
      await NotificationService.markAsRead(id);
      const n = notifications.value.find((x) => x.id === id);
      if (n) {
        if (!n.is_read) {
          n.is_read = true;
          if (serverUnreadCount.value !== null && serverUnreadCount.value > 0) {
            serverUnreadCount.value--;
          }
        }
      } else if (serverUnreadCount.value !== null && serverUnreadCount.value > 0) {
        serverUnreadCount.value--;
      }
    } catch (e) {
      if (isDev()) {
        console.error(e);
      }
    }
  }

  async function markAllRead(): Promise<void> {
    try {
      await NotificationService.markAllAsRead();
      notifications.value.forEach((n) => {
        n.is_read = true;
      });
      serverUnreadCount.value = 0;
    } catch (e) {
      if (isDev()) {
        console.error(e);
      }
    }
  }

  function subscribeToNotifications(): void {
    if (!authStore.user?.id) return;
    if (subscription) return; // Already subscribed

    subscription = supabase
      .channel('public:notifications')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${authStore.user.id}`,
        },
        async (payload: { new: Notification }): Promise<void> => {
          const newNotification = payload.new as Notification;

          if (serverUnreadCount.value !== null) {
            serverUnreadCount.value++;
          }

          // Fetch actor details if available
          if (newNotification.actor_id) {
            try {
              const cachedActor = actorCache.get(newNotification.actor_id);
              if (cachedActor) {
                newNotification.actor_name = cachedActor.name;
                newNotification.actor_picture = cachedActor.picture;
              } else {
                const user = await ProfileService.getPublicProfile(newNotification.actor_id);
                actorCache.set(newNotification.actor_id, {
                  name: user.name,
                  picture: user.picture,
                });
                if (actorCache.size > MAX_ACTOR_CACHE) {
                  const oldestActorId = actorCache.keys().next().value;
                  if (oldestActorId) actorCache.delete(oldestActorId);
                }
                newNotification.actor_name = user.name;
                newNotification.actor_picture = user.picture;
              }
            } catch (e) {
              if (isDev()) {
                console.error('Failed to fetch actor details for notification', e);
              }
            }
          }

          notifications.value = [newNotification, ...notifications.value].slice(0, MAX_NOTIFICATIONS);
        }
      )
      .subscribe();
  }

  function unsubscribe(): void {
    if (subscription) {
      supabase.removeChannel(subscription);
      subscription = null;
    }
  }

  watch(
    () => authStore.user?.id ?? null,
    (newUserId, oldUserId) => {
      if (!newUserId) {
        resetState();
        return;
      }

      if (oldUserId && newUserId !== oldUserId) {
        resetState();
      }

      void fetchUnreadCount();
      subscribeToNotifications();
    },
    { immediate: true }
  );

  return {
    notifications,
    serverUnreadCount,
    unreadCount,
    isLoadingMore,
    isLoaded,
    hasMore,
    resetState,
    fetchUnreadCount,
    fetchNotifications,
    fetchMoreNotifications,
    markRead,
    markAllRead,
    subscribeToNotifications,
    unsubscribe,
  };
});
