import { apiV1 } from '../utils/api';

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  resource_id?: string;
  resource_type?: string;
  is_read: boolean;
  created_at: string;
  actor_id?: string;
  actor_name?: string;
  actor_picture?: string;
}

export const NotificationService = {
  async getNotifications(limit: number = 20, offset: number = 0, before?: string): Promise<Notification[]> {
    return apiV1.get('/notifications', {
      params: { limit, offset, ...(before ? { before } : {}) },
    });
  },

  async getUnreadCount(): Promise<number> {
    const res = await apiV1.get<{ unread_count: number }>('/notifications/unread-count');
    return res.unread_count;
  },

  async markAsRead(id: string): Promise<void> {
    return apiV1.put(`/notifications/${id}/read`);
  },

  async markAllAsRead(): Promise<void> {
    return apiV1.put('/notifications/read-all');
  },
};
