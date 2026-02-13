import { apiV1 } from '../utils/api';

export const SubscriptionService = {
  async createCheckout(priceId: string): Promise<{ checkout_url: string; session_id: string }> {
    return apiV1.post('/subscription/checkout', {
      price_id: priceId,
      success_url: `${window.location.origin}/subscription/success`,
      cancel_url: `${window.location.origin}/subscription/cancel`,
    });
  },
  
  async getStatus(): Promise<{
    is_pro: boolean;
    subscription_end_date: string | null;
    cancel_at_period_end?: boolean;
    treat_balance?: number;
    stripe_customer_id?: string;
  }> {
    return apiV1.get('/subscription/status');
  },
  
  async cancel(): Promise<void> {
    return apiV1.post('/subscription/cancel');
  },
  
  async createPortalSession(returnUrl: string): Promise<{ url: string }> {
    return apiV1.post('/subscription/portal', { return_url: returnUrl });
  },
};
