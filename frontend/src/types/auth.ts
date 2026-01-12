export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  bio?: string;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  refresh_token?: string; // Optional refresh token from backend
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
