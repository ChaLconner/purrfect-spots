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
  
  async giveTreat(photoId: string, amount: number): Promise<{ success: boolean; message: string; new_balance?: number }> {
    return apiV1.post('/treats/give', { photo_id: photoId, amount });
  },
  
  async purchaseCheckout(packageType: 'small' | 'medium' | 'large' | 'legendary'): Promise<{ checkout_url: string; session_id: string }> {
    return apiV1.post('/treats/purchase/checkout', { package: packageType });
  },
  
  async getLeaderboard(): Promise<Array<{ id: string; name: string; total_treats_received: number; picture?: string }>> {
    return apiV1.get('/treats/leaderboard');
  },
};
