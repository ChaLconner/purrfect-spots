import { apiV1 } from '../utils/api';

export interface TreatTransaction {
  id: string;
  amount: number;
  transaction_type: string;
  created_at: string;
  // ... other fields
}

export const TreatsService = {
  async getBalance(): Promise<{ balance: number; recent_transactions: TreatTransaction[] }> {
    return apiV1.get('/treats/balance');
  },

  async giveTreat(
    photoId: string,
    amount: number
  ): Promise<{ success: boolean; message: string; new_balance?: number }> {
    return apiV1.post('/treats/give', { photo_id: photoId, amount });
  },

  async purchaseCheckout(
    packageType: string
  ): Promise<{ checkout_url: string; session_id: string }> {
    return apiV1.post('/treats/purchase/checkout', { package: packageType });
  },

  async getLeaderboard(period: 'weekly' | 'monthly' | 'all_time' = 'all_time'): Promise<
    Array<{
      id: string;
      name: string;
      username?: string;
      total_treats_received: number;
      picture?: string;
    }>
  > {
    return apiV1.get('/treats/leaderboard', { params: { period } });
  },

  async getPackages(): Promise<
    Record<
      string,
      { amount: number; price: number; name: string; bonus: number; price_per_treat: number }
    >
  > {
    return apiV1.get('/treats/packages');
  },
};
