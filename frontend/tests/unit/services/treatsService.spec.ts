import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TreatsService } from '@/services/treatsService';

const mockRequest = vi.fn();

vi.mock('@/utils/api', () => ({
  apiV1: {
    get: (...args: any[]) => mockRequest('get', ...args),
    post: (...args: any[]) => mockRequest('post', ...args),
  },
}));

describe('TreatsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getBalance', () => {
    it('calls GET /treats/balance', async () => {
      mockRequest.mockResolvedValue({ balance: 100, recent_transactions: [] });

      const result = await TreatsService.getBalance();

      expect(mockRequest).toHaveBeenCalledWith('get', '/treats/balance');
      expect(result.balance).toBe(100);
    });
  });

  describe('giveTreat', () => {
    it('calls POST /treats/give with correct payload', async () => {
      mockRequest.mockResolvedValue({ success: true, new_balance: 90 });

      const result = await TreatsService.giveTreat('photo-123', 10);

      expect(mockRequest).toHaveBeenCalledWith('post', '/treats/give', {
        photo_id: 'photo-123',
        amount: 10,
      });
      expect(result.success).toBe(true);
    });
  });

  describe('purchaseCheckout', () => {
    it('calls POST /treats/purchase/checkout', async () => {
      mockRequest.mockResolvedValue({ checkout_url: 'https://stripe.com/...', session_id: 'sess_123' });

      const result = await TreatsService.purchaseCheckout('large');

      expect(mockRequest).toHaveBeenCalledWith('post', '/treats/purchase/checkout', {
        package: 'large',
      });
      expect(result.checkout_url).toBeDefined();
    });
  });

  describe('getLeaderboard', () => {
    it('calls GET /treats/leaderboard with period param', async () => {
      mockRequest.mockResolvedValue([
        { id: '1', name: 'User 1', total_treats_received: 1000 },
      ]);

      const result = await TreatsService.getLeaderboard('weekly');

      expect(mockRequest).toHaveBeenCalledWith('get', '/treats/leaderboard', {
        params: { period: 'weekly' },
      });
      expect(result).toHaveLength(1);
    });

    it('defaults to all_time period', async () => {
      mockRequest.mockResolvedValue([]);

      await TreatsService.getLeaderboard();

      expect(mockRequest).toHaveBeenCalledWith('get', '/treats/leaderboard', {
        params: { period: 'all_time' },
      });
    });
  });

  describe('getPackages', () => {
    it('calls GET /treats/packages', async () => {
      const mockPackages = {
        small: { amount: 100, price: 1.99, name: 'Small', bonus: 0, price_per_treat: 0.0199 },
      };
      mockRequest.mockResolvedValue(mockPackages);

      const result = await TreatsService.getPackages();

      expect(mockRequest).toHaveBeenCalledWith('get', '/treats/packages');
      expect(result).toEqual(mockPackages);
    });
  });
});
