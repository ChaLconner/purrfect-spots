export interface TreatPackage {
  amount: number;
  price: number;
  name: string;
  bonus: number;
  price_per_treat: number;
  // Computed property for UI logic (key from the object entries)
  key?: string;
}

export interface SubscriptionStatus {
  is_pro: boolean;
  subscription_end_date: string | null;
  cancel_at_period_end?: boolean;
  treat_balance?: number;
  stripe_customer_id?: string;
}
