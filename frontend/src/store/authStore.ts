/**
 * Pinia Auth Store
 * 
 * Centralized authentication state management with Pinia.
 * Handles user authentication, token management, and session verification.
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User, LoginResponse } from '../types/auth';
import { ProfileService } from '../services/profileService';

import { apiV1, setAccessToken } from '../utils/api';


export const useAuthStore = defineStore('auth', () => {
  // ========== State ==========

  const user = ref<User | null>(null);
  const token = ref<string | null>(null); // Memory only, no localStorage!
  const isAuthenticated = ref(false);

  const isLoading = ref(false);
  const error = ref<string | null>(null);
  
  // Singleton promise to avoid parallel refresh calls
  let refreshPromise: Promise<boolean> | null = null;

  // ========== Getters ==========
  const hasCompleteProfile = computed(() => {
    return !!(user.value && user.value.email && user.value.name);
  });

  const isUserReady = computed(() => {
    return isAuthenticated.value && hasCompleteProfile.value;
  });

  const userDisplayName = computed(() => {
    return user.value?.name || user.value?.email || 'User';
  });

  const userAvatar = computed(() => {
    return user.value?.picture || '/default-avatar.svg';
  });

  // ========== Actions ==========
  
  /**
   * Initialize authentication state
   * Try to recover session from HttpOnly cookie via refresh endpoint
   */
  async function initializeAuth() {
    // Restore user data for UX while checking auth
    const storedUser = localStorage.getItem('user_data') || localStorage.getItem('user');

    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        if (isValidUser(parsedUser)) {
          user.value = parsedUser;
        }
      } catch (_e) {
        // eslint-disable-next-line no-console
        console.error('Failed to parse stored user data:', _e);
      }
    }


    // Always try to refresh token on init to check valid session
    // This effectively restores the session using the HttpOnly cookie
    await refreshToken();

  }

  /**
   * Refresh access token using HttpOnly cookie
   */
  async function refreshToken(): Promise<boolean> {
    // If a refresh is already in progress, return the existing promise
    if (refreshPromise) {
      return refreshPromise;
    }

    refreshPromise = (async () => {
      try {
        // Calls endpoint that reads HttpOnly cookie
        const response = await apiV1.post<{ access_token: string, token_type: string, user?: User }>('/auth/refresh-token');
        
        if (response.access_token) {
          token.value = response.access_token;
          isAuthenticated.value = true;
          
          // Update user if returned
          if (response.user) {
            user.value = response.user;
            localStorage.setItem('user_data', JSON.stringify(response.user));
          }
          
          
          // Update axios default header
          updateApiHeader(response.access_token);

          
          return true;
        }
        return false;
      } catch {
        // Silent fail on init - just means not logged in
        // eslint-disable-next-line no-console
        console.debug('No active session found');
        
        // Only clear if we thought we were authenticated
        // This avoids clearing the UX-fallback user data for guests
        if (isAuthenticated.value) {
          clearAuth();
        }
        
        return false;
      } finally {
        // Clear the promise so next call can trigger a new refresh if needed
        refreshPromise = null;
      }
    })();

    return refreshPromise;
  }

  function updateApiHeader(accessToken: string | null) {
      if (accessToken) {
        setAccessToken(accessToken);
      } else {
        setAccessToken(null);
        localStorage.removeItem('auth_token'); // Clean up legacy
        localStorage.removeItem('access_token'); // Clean up legacy
      }
  }


  /**
   * Validate user object shape
   */
  function isValidUser(userData: unknown): userData is User {
    if (typeof userData !== 'object' || userData === null) {
      return false;
    }
    const obj = userData as Record<string, unknown>;
    return (
      typeof obj.id === 'string' &&
      typeof obj.email === 'string'
    );
  }

  /**
   * Set authentication data after successful login
   */
  async function setAuth(data: LoginResponse) {
    user.value = data.user;
    token.value = data.access_token;
    isAuthenticated.value = true;
    error.value = null;

    // Persist user data for UX
    localStorage.setItem('user_data', JSON.stringify(data.user));
    
    // Update headers/storage
    updateApiHeader(data.access_token);
  }

  /**
   * Clear all authentication data
   */
  function clearAuth() {
    user.value = null;
    token.value = null;
    isAuthenticated.value = false;
    error.value = null;

    localStorage.removeItem('user_data');
    localStorage.removeItem('user');
    updateApiHeader(null);
  }

  /**
   * Verify session with backend
   */
  async function verifySession(): Promise<boolean> {
    if (!isAuthenticated.value) {
        // Try refresh first
        return await refreshToken();
    }

    // ... existing verification logic ...
    // Simplified: just check if we can fetch profile
    try {
      await ProfileService.getProfile();
      return true;
    } catch {
      // If profile fetch failed, try one last refresh
      return await refreshToken();
    }
  }

  /**
   * Update user profile data
   */
  function updateUser(updates: Partial<User>) {
    if (user.value) {
      user.value = { ...user.value, ...updates };
      localStorage.setItem('user_data', JSON.stringify(user.value));
    }
  }

  /**
   * Get authorization header for API requests
   */
  function getAuthHeader(): Record<string, string> {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {};
  }

  /**
   * Logout and redirect to login page
   */
  async function logout() {
    try {
      await apiV1.post('/auth/logout');
    } catch (e) {
      console.warn('Logout API call failed', e);
    } finally {
      clearAuth();
      // Navigation should be handled by the component calling this
    }
  }

  // Initialize on store creation
  initializeAuth();

  return {
    // State
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    
    // Getters
    hasCompleteProfile,
    isUserReady,
    userDisplayName,
    userAvatar,
    
    // Actions
    initializeAuth,
    setAuth,
    clearAuth,
    verifySession,
    updateUser,
    getAuthHeader,
    logout,
  };
});


