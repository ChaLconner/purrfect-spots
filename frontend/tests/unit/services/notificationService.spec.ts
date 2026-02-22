import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NotificationService } from '@/services/notificationService';

const mockRequest = vi.fn();

vi.mock('@/utils/api', () => ({
  apiV1: {
    get: (...args: any[]) => mockRequest('get', ...args),
    put: (...args: any[]) => mockRequest('put', ...args),
  },
}));

describe('NotificationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getNotifications', () => {
    it('calls GET /notifications with default params', async () => {
      mockRequest.mockResolvedValue([]);

      const result = await NotificationService.getNotifications();

      expect(mockRequest).toHaveBeenCalledWith('get', '/notifications', {
        params: { limit: 20, offset: 0 },
      });
      expect(result).toEqual([]);
    });

    it('calls GET /notifications with custom params', async () => {
      mockRequest.mockResolvedValue([{ id: '1' }]);

      const result = await NotificationService.getNotifications(10, 20);

      expect(mockRequest).toHaveBeenCalledWith('get', '/notifications', {
        params: { limit: 10, offset: 20 },
      });
      expect(result).toHaveLength(1);
    });
  });

  describe('markAsRead', () => {
    it('calls PUT /notifications/:id/read', async () => {
      mockRequest.mockResolvedValue(undefined);

      await NotificationService.markAsRead('notif-123');

      expect(mockRequest).toHaveBeenCalledWith('put', '/notifications/notif-123/read');
    });
  });

  describe('markAllAsRead', () => {
    it('calls PUT /notifications/read-all', async () => {
      mockRequest.mockResolvedValue(undefined);

      await NotificationService.markAllAsRead();

      expect(mockRequest).toHaveBeenCalledWith('put', '/notifications/read-all');
    });
  });
});
