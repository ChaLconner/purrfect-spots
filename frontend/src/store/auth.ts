import { reactive } from 'vue';
import type { AuthState, LoginResponse, User } from '../types/auth';

// Auth store using reactive state
export const authStore = reactive<AuthState>({
  user: null,
  token: localStorage.getItem('auth_token'),
  isAuthenticated: false,
  isLoading: false,
});

// Check if user has complete profile
export function hasCompleteProfile(user: User | null): boolean {
  return !!(user && user.email && user.name);
}

// Initialize authentication state from localStorage
export function initializeAuth() {
  // Check for tokens with different key names (compatibility with both auth methods)
  const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');
  const userData = localStorage.getItem('user_data') || localStorage.getItem('user');
  
  if (token && userData) {
    try {
      const user = JSON.parse(userData);
      authStore.token = token;
      authStore.user = user;
      authStore.isAuthenticated = true;
    } catch (error) {
      // Clear invalid data
      clearAuth();
    }
  }
}

// Set authentication data
export function setAuth(data: LoginResponse) {
  authStore.user = data.user;
  authStore.token = data.access_token;
  authStore.isAuthenticated = true;
  
  // Persist to localStorage
  localStorage.setItem('auth_token', data.access_token);
  localStorage.setItem('user_data', JSON.stringify(data.user));
}

// Clear authentication data
export function clearAuth() {
  authStore.user = null;
  authStore.token = null;
  authStore.isAuthenticated = false;
  
  // Clear localStorage (both key formats for compatibility)
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_data');
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
}

// Get authorization header
export function getAuthHeader(): Record<string, string> {
  return authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {};
}

// Check if user is ready to use protected features
export function isUserReady(): boolean {
  return authStore.isAuthenticated && hasCompleteProfile(authStore.user);
}
