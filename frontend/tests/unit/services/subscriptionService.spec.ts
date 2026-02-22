import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SubscriptionService } from '@/services/subscriptionService';

const mockRequest = vi.fn();

vi.mock('@/utils/api', () => ({
  apiV1: {
    get: (...args: any[]) => mockRequest('get', ...args),
    post: (...args: any[]) => mockRequest('post', ...args),
  },
}));

describe('SubscriptionService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('window', {
      location: { origin: 'https://example.com' },
    });
  });

  describe('createCheckout', () => {
    it('calls POST /subscription/checkout with correct params', async () => {
      mockRequest.mockResolvedValue({
        checkout_url: 'https://stripe.com/checkout',
        session_id: 'sess_123',
      });

      const result = await SubscriptionService.createCheckout('price_pro_monthly');

      expect(mockRequest).toHaveBeenCalledWith('post', '/subscription/checkout', {
        price_id: 'price_pro_monthly',
        success_url: 'https://example.com/subscription/success',
        cancel_url: 'https://example.com/subscription/cancel',
      });
      expect(result.checkout_url).toBe('https://stripe.com/checkout');
    });
  });

  describe('getStatus', () => {
    it('calls GET /subscription/status', async () => {
      mockRequest.mockResolvedValue({
        is_pro: true,
        subscription_end_date: '2024-12-31',
        cancel_at_period_end: false,
        treat_balance: 100,
        stripe_customer_id: 'cus_123',
      });

      const result = await SubscriptionService.getStatus();

      expect(mockRequest).toHaveBeenCalledWith('get', '/subscription/status');
      expect(result.is_pro).toBe(true);
    });
  });

  describe('cancel', () => {
    it('calls POST /subscription/cancel', async () => {
      mockRequest.mockResolvedValue(undefined);

      await SubscriptionService.cancel();

      expect(mockRequest).toHaveBeenCalledWith('post', '/subscription/cancel');
    });
  });

  describe('createPortalSession', () => {
    it('calls POST /subscription/portal with return URL', async () => {
      mockRequest.mockResolvedValue({ url: 'https://stripe.com/portal' });

      const result = await SubscriptionService.createPortalSession('https://example.com/account');

      expect(mockRequest).toHaveBeenCalledWith('post', '/subscription/portal', {
        return_url: 'https://example.com/account',
      });
      expect(result.url).toBe('https://stripe.com/portal');
    });
  });
});
