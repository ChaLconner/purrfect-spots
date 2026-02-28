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
  actor_name?: string;
  actor_picture?: string;
}

export const NotificationService = {
  async getNotifications(limit: number = 20, offset: number = 0): Promise<Notification[]> {
    return apiV1.get('/notifications', { params: { limit, offset } });
  },

  async markAsRead(id: string): Promise<void> {
    return apiV1.put(`/notifications/${id}/read`);
  },

  async markAllAsRead(): Promise<void> {
    return apiV1.put('/notifications/read-all');
  },
};
