import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useNotificationStore } from '@/store/notificationStore';
import type { RealtimeChannel } from '@supabase/supabase-js';

const mockGetNotifications = vi.fn();
const mockMarkAsRead = vi.fn();
const mockMarkAllAsRead = vi.fn();
const mockGetPublicProfile = vi.fn();

vi.mock('@/services/notificationService', () => ({
  NotificationService: {
    getNotifications: (...args: any[]) => mockGetNotifications(...args),
    markAsRead: (...args: any[]) => mockMarkAsRead(...args),
    markAllAsRead: (...args: any[]) => mockMarkAllAsRead(...args),
  },
}));

vi.mock('@/services/profileService', () => ({
  ProfileService: {
    getPublicProfile: (...args: any[]) => mockGetPublicProfile(...args),
  },
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    isAuthenticated: true,
    user: { id: 'user-123' },
  })),
}));

const mockChannel = {
  on: vi.fn().mockReturnThis(),
  subscribe: vi.fn().mockReturnThis(),
};

const mockRemoveChannel = vi.fn();

vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn(() => mockChannel),
    removeChannel: (...args: any[]) => mockRemoveChannel(...args),
  },
}));

describe('notificationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe('fetchNotifications', () => {
    it('fetches notifications when authenticated', async () => {
      const mockNotifications = [
        { id: '1', message: 'Test 1', is_read: false },
        { id: '2', message: 'Test 2', is_read: true },
      ];
      mockGetNotifications.mockResolvedValue(mockNotifications);

      const store = useNotificationStore();
      await store.fetchNotifications();

      expect(mockGetNotifications).toHaveBeenCalledWith(15, 0);
      expect(store.notifications).toEqual(mockNotifications);
    });

    it('sets hasMore to false when less than limit', async () => {
      mockGetNotifications.mockResolvedValue([{ id: '1' }]);

      const store = useNotificationStore();
      await store.fetchNotifications();

      expect(store.hasMore).toBe(false);
    });

    it('sets hasMore to true when equals limit', async () => {
      mockGetNotifications.mockResolvedValue(Array(15).fill({ id: '1' }));

      const store = useNotificationStore();
      await store.fetchNotifications();

      expect(store.hasMore).toBe(true);
    });

    it('handles fetch errors', async () => {
      mockGetNotifications.mockRejectedValue(new Error('Network error'));

      const store = useNotificationStore();
      await expect(store.fetchNotifications()).resolves.not.toThrow();
      expect(store.notifications).toEqual([]);
    });
  });

  describe('fetchMoreNotifications', () => {
    it('appends new notifications', async () => {
      mockGetNotifications.mockResolvedValueOnce(Array(15).fill({}).map((_, i) => ({ id: `${i + 1}` })));
      mockGetNotifications.mockResolvedValueOnce([{ id: '16' }, { id: '17' }]);

      const store = useNotificationStore();
      await store.fetchNotifications();
      expect(store.hasMore).toBe(true);
      await store.fetchMoreNotifications();

      expect(store.notifications).toHaveLength(17);
    });

    it('filters duplicates', async () => {
      mockGetNotifications.mockResolvedValueOnce(Array(15).fill({}).map((_, i) => ({ id: `${i + 1}` })));
      mockGetNotifications.mockResolvedValueOnce([{ id: '15' }, { id: '16' }]);

      const store = useNotificationStore();
      await store.fetchNotifications();
      await store.fetchMoreNotifications();

      expect(store.notifications).toHaveLength(16);
      expect(store.notifications.find(n => n.id === '15')).toBeDefined();
    });

    it('skips when already loading', async () => {
      mockGetNotifications.mockResolvedValue([{ id: '1' }]);

      const store = useNotificationStore();
      store.isLoadingMore = true;

      await store.fetchMoreNotifications();
      expect(mockGetNotifications).not.toHaveBeenCalled();
    });

    it('skips when no more items', async () => {
      mockGetNotifications.mockResolvedValue([{ id: '1' }]);

      const store = useNotificationStore();
      store.hasMore = false;

      await store.fetchMoreNotifications();
      expect(mockGetNotifications).not.toHaveBeenCalled();
    });
  });

  describe('markRead', () => {
    it('marks notification as read', async () => {
      mockMarkAsRead.mockResolvedValue(undefined);
      mockGetNotifications.mockResolvedValue([{ id: '1', is_read: false }]);

      const store = useNotificationStore();
      await store.fetchNotifications();
      await store.markRead('1');

      expect(mockMarkAsRead).toHaveBeenCalledWith('1');
      expect(store.notifications[0].is_read).toBe(true);
    });

    it('handles errors', async () => {
      mockMarkAsRead.mockRejectedValue(new Error('Failed'));
      mockGetNotifications.mockResolvedValue([{ id: '1', is_read: false }]);

      const store = useNotificationStore();
      await store.fetchNotifications();
      await expect(store.markRead('1')).resolves.not.toThrow();
    });
  });

  describe('markAllRead', () => {
    it('marks all notifications as read', async () => {
      mockMarkAllAsRead.mockResolvedValue(undefined);
      mockGetNotifications.mockResolvedValue([
        { id: '1', is_read: false },
        { id: '2', is_read: false },
      ]);

      const store = useNotificationStore();
      await store.fetchNotifications();
      await store.markAllRead();

      expect(mockMarkAllAsRead).toHaveBeenCalled();
      expect(store.notifications.every(n => n.is_read)).toBe(true);
    });
  });

  describe('subscribeToNotifications', () => {
    it('creates subscription', () => {
      const store = useNotificationStore();
      store.subscribeToNotifications();

      expect(mockChannel.on).toHaveBeenCalled();
      expect(mockChannel.subscribe).toHaveBeenCalled();
    });

    it('does not create duplicate subscription', () => {
      const store = useNotificationStore();
      store.subscribeToNotifications();
      store.subscribeToNotifications();

      expect(mockChannel.subscribe).toHaveBeenCalledTimes(1);
    });
  });

  describe('unsubscribe', () => {
    it('removes channel', () => {
      const store = useNotificationStore();
      store.subscribeToNotifications();
      store.unsubscribe();

      expect(mockRemoveChannel).toHaveBeenCalled();
    });
  });

  describe('unreadCount', () => {
    it('counts unread notifications', async () => {
      mockGetNotifications.mockResolvedValue([
        { id: '1', is_read: false },
        { id: '2', is_read: true },
        { id: '3', is_read: false },
      ]);

      const store = useNotificationStore();
      await store.fetchNotifications();

      expect(store.unreadCount).toBe(2);
    });
  });
});
