import { reactive } from 'vue';
import type { AuthState, LoginResponse } from '../types/auth';

// Auth store using reactive state
export const authStore = reactive<AuthState>({
  user: null,
  token: localStorage.getItem('auth_token'),
  isAuthenticated: false,
  isLoading: false,
});

// Initialize authentication state from localStorage
export function initializeAuth() {
  const token = localStorage.getItem('auth_token');
  const userData = localStorage.getItem('user_data');
  
  if (token && userData) {
    try {
      authStore.token = token;
      authStore.user = JSON.parse(userData);
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
  
  // Clear localStorage
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_data');
}

// Get authorization header
export function getAuthHeader(): Record<string, string> {
  return authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {};
}
