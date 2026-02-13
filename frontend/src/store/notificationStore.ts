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

    async function fetchNotifications() {
        if (!authStore.isAuthenticated) return;
        try {
            const data = await NotificationService.getNotifications();
            notifications.value = data;
        } catch (e) {
            console.error("Failed to fetch notifications", e);
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
        fetchNotifications,
        markRead,
        markAllRead,
        subscribeToNotifications,
        unsubscribe
    };
});
