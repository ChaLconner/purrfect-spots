export interface User {
  id: string;
  email: string;
  username?: string;
  name: string;
  picture?: string;
  bio?: string;
  created_at: string;
  google_id?: string;
  is_pro?: boolean;
  treat_balance?: number;
  total_treats_received?: number;
  role?: string;
  stripe_customer_id?: string;
}

export interface LoginResponse {
  access_token?: string;
  token_type?: string;
  user: User;
  refresh_token?: string; // Optional refresh token from backend
  message?: string;
  requires_verification?: boolean;
  email?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
