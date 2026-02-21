import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { NotificationService, type Notification } from '@/services/notificationService';
import { useAuthStore } from './authStore';
import { supabase } from '@/lib/supabase';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { ProfileService } from '@/services/profileService';

export const useNotificationStore = defineStore('notifications', () => {
    const notifications = ref<Notification[]>([]);
    const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length);
    const authStore = useAuthStore();
    let subscription: RealtimeChannel | null = null;
    
    // Pagination states
    const isLoadingMore = ref(false);
    const hasMore = ref(true);
    const limit = 15;

    async function fetchNotifications() {
        if (!authStore.isAuthenticated) return;
        try {
            hasMore.value = true;
            isLoadingMore.value = false;
            const data = await NotificationService.getNotifications(limit, 0);
            notifications.value = data;
            if (data.length < limit) hasMore.value = false;
        } catch (e) {
            console.error("Failed to fetch notifications", e);
        }
    }

    async function fetchMoreNotifications() {
        if (!authStore.isAuthenticated || isLoadingMore.value || !hasMore.value) return;
        isLoadingMore.value = true;
        try {
            const currentOffset = notifications.value.length;
            const data = await NotificationService.getNotifications(limit, currentOffset);
            if (data.length > 0) {
                // Filter out duplicates just in case new notifications arrived in between
                const newIds = new Set(data.map(n => n.id));
                const existingNotifications = notifications.value.filter(n => !newIds.has(n.id));
                notifications.value = [...existingNotifications, ...data];
            }
            if (data.length < limit) {
                hasMore.value = false;
            }
        } catch (e) {
            console.error("Failed to fetch more notifications", e);
        } finally {
            isLoadingMore.value = false;
        }
    }

    async function markRead(id: string) {
        try {
            await NotificationService.markAsRead(id);
            const n = notifications.value.find(x => x.id === id);
            if (n) n.is_read = true;
        } catch (e) {
            console.error(e);
        }
    }

    async function markAllRead() {
        try {
            await NotificationService.markAllAsRead();
            notifications.value.forEach((n) => { n.is_read = true; });
        } catch (e) {
            console.error(e);
        }
    }

    function subscribeToNotifications() {
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
                    filter: `user_id=eq.${authStore.user.id}`
                },
                async (payload) => {
                    const newNotification = payload.new as Notification;
                    
                    // Fetch actor details if available
                    if (newNotification.actor_id) {
                        try {
                            const user = await ProfileService.getPublicProfile(newNotification.actor_id);
                            newNotification.actor_name = user.name;
                            newNotification.actor_picture = user.picture;
                        } catch (e) {
                            console.error("Failed to fetch actor details for notification", e);
                        }
                    }
                    
                    notifications.value.unshift(newNotification);
                }
            )
            .subscribe();
    }
    
    function unsubscribe() {
        if (subscription) {
            supabase.removeChannel(subscription);
            subscription = null;
        }
    }

    return {
        notifications,
        unreadCount,
        isLoadingMore,
        hasMore,
        fetchNotifications,
        fetchMoreNotifications,
        markRead,
        markAllRead,
        subscribeToNotifications,
        unsubscribe
    };
});
