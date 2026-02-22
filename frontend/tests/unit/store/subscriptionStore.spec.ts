import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useSubscriptionStore } from '@/store/subscriptionStore';

const mockGetStatus = vi.fn();
const mockCreateCheckout = vi.fn();
const mockCancel = vi.fn();
const mockCreatePortalSession = vi.fn();

vi.mock('@/services/subscriptionService', () => ({
  SubscriptionService: {
    getStatus: (...args: any[]) => mockGetStatus(...args),
    createCheckout: (...args: any[]) => mockCreateCheckout(...args),
    cancel: (...args: any[]) => mockCancel(...args),
    createPortalSession: (...args: any[]) => mockCreatePortalSession(...args),
  },
}));

const mockGetBalance = vi.fn();
const mockGiveTreat = vi.fn();
const mockGetPackages = vi.fn();
const mockPurchaseCheckout = vi.fn();
const mockGetLeaderboard = vi.fn();

vi.mock('@/services/treatsService', () => ({
  TreatsService: {
    getBalance: (...args: any[]) => mockGetBalance(...args),
    giveTreat: (...args: any[]) => mockGiveTreat(...args),
    getPackages: (...args: any[]) => mockGetPackages(...args),
    purchaseCheckout: (...args: any[]) => mockPurchaseCheckout(...args),
    getLeaderboard: (...args: any[]) => mockGetLeaderboard(...args),
  },
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    isAuthenticated: true,
    user: { id: 'user-123', is_pro: false, treat_balance: 0 },
  })),
}));

describe('subscriptionStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('fetchStatus', () => {
    it('fetches and sets subscription status', async () => {
      mockGetStatus.mockResolvedValue({
        is_pro: true,
        subscription_end_date: '2024-12-31',
        cancel_at_period_end: false,
        treat_balance: 100,
        stripe_customer_id: 'cus_123',
      });

      const store = useSubscriptionStore();
      await store.fetchStatus();

      expect(store.isPro).toBe(true);
      expect(store.subscriptionEndDate).toBe('2024-12-31');
      expect(store.cancelAtPeriodEnd).toBe(false);
      expect(store.treatBalance).toBe(100);
    });

    it('respects cooldown', async () => {
      mockGetStatus.mockResolvedValue({ is_pro: true });

      const store = useSubscriptionStore();
      await store.fetchStatus();
      await store.fetchStatus();

      expect(mockGetStatus).toHaveBeenCalledTimes(1);
    });

    it('force fetch bypasses cooldown', async () => {
      mockGetStatus.mockResolvedValue({ is_pro: true });

      const store = useSubscriptionStore();
      await store.fetchStatus();
      await store.fetchStatus(true);

      expect(mockGetStatus).toHaveBeenCalledTimes(2);
    });

    it('handles errors', async () => {
      mockGetStatus.mockRejectedValue(new Error('Network error'));

      const store = useSubscriptionStore();
      await expect(store.fetchStatus()).resolves.not.toThrow();
    });
  });

  describe('fetchTreatBalance', () => {
    it('fetches and sets treat balance', async () => {
      mockGetBalance.mockResolvedValue({ balance: 50, recent_transactions: [] });

      const store = useSubscriptionStore();
      await store.fetchTreatBalance();

      expect(store.treatBalance).toBe(50);
    });

    it('handles errors', async () => {
      mockGetBalance.mockRejectedValue(new Error('Failed'));

      const store = useSubscriptionStore();
      await expect(store.fetchTreatBalance()).resolves.not.toThrow();
    });
  });

  describe('fetchPackages', () => {
    it('fetches and caches packages', async () => {
      const mockPkgs = {
        small: { amount: 100, price: 1.99, name: 'Small', bonus: 0, price_per_treat: 0.0199 },
      };
      mockGetPackages.mockResolvedValue(mockPkgs);

      const store = useSubscriptionStore();
      const result = await store.fetchPackages();

      expect(result).toEqual(mockPkgs);
      expect(store.packagesLoaded).toBe(true);
    });

    it('returns cached packages on second call', async () => {
      mockGetPackages.mockResolvedValue({ small: { amount: 100 } });

      const store = useSubscriptionStore();
      await store.fetchPackages();
      await store.fetchPackages();

      expect(mockGetPackages).toHaveBeenCalledTimes(1);
    });

    it('force fetch refreshes cache', async () => {
      mockGetPackages.mockResolvedValue({ small: { amount: 100 } });

      const store = useSubscriptionStore();
      await store.fetchPackages();
      await store.fetchPackages(true);

      expect(mockGetPackages).toHaveBeenCalledTimes(2);
    });
  });

  describe('sortedPackages', () => {
    it('sorts packages by amount', async () => {
      mockGetPackages.mockResolvedValue({
        large: { amount: 500, price: 9.99, name: 'Large', bonus: 50 },
        small: { amount: 100, price: 1.99, name: 'Small', bonus: 0 },
      });

      const store = useSubscriptionStore();
      await store.fetchPackages();

      const sorted = store.sortedPackages;
      expect(sorted[0].amount).toBe(100);
      expect(sorted[1].amount).toBe(500);
    });
  });

  describe('giveTreat', () => {
    it('optimistically updates balance', async () => {
      mockGiveTreat.mockResolvedValue({ success: true, new_balance: 40 });

      const store = useSubscriptionStore();
      store.treatBalance = 50;

      await store.giveTreat('photo-123', 10);

      expect(mockGiveTreat).toHaveBeenCalledWith('photo-123', 10);
    });

    it('throws when not authenticated', async () => {
      vi.mocked(await import('@/store/authStore')).useAuthStore.mockReturnValueOnce({
        isAuthenticated: false,
        user: null,
      });

      const store = useSubscriptionStore();

      await expect(store.giveTreat('photo-123', 10)).rejects.toThrow('Not authenticated');
    });

    it('rolls back on error', async () => {
      mockGiveTreat.mockRejectedValue(new Error('Insufficient treats'));

      const store = useSubscriptionStore();
      store.treatBalance = 50;

      await expect(store.giveTreat('photo-123', 10)).rejects.toThrow();
      expect(store.treatBalance).toBe(50);
    });
  });

  describe('refreshAll', () => {
    it('calls both fetch methods', async () => {
      mockGetStatus.mockResolvedValue({ is_pro: true });
      mockGetBalance.mockResolvedValue({ balance: 100 });

      const store = useSubscriptionStore();
      await store.refreshAll();

      expect(mockGetStatus).toHaveBeenCalled();
      expect(mockGetBalance).toHaveBeenCalled();
    });
  });
});
