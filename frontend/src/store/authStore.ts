/**
 * Pinia Auth Store
 *
 * Centralized authentication state management with Pinia.
 * Handles user authentication, token management, and session verification.
 */
import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { supabase } from '../lib/supabase';
import { PERMISSIONS } from '../constants/permissions';
import type { RealtimeChannel } from '@supabase/supabase-js';

import { apiV1, setAccessToken, setAuthCallbacks } from '../utils/api';
import { ProfileService } from '../services/profileService';

// Module-level helper to update API header - avoids recreation on every store access
function updateApiHeader(accessToken: string | null): void {
  if (accessToken) {
    setAccessToken(accessToken);
  } else {
    setAccessToken(null);
    localStorage.removeItem('auth_token'); // Clean up legacy
    localStorage.removeItem('access_token'); // Clean up legacy
  }
}

/**
 * Filter sensitive fields before caching to localStorage
 */
function sanitizeUserForCache(userData: User | null): Partial<User> | null {
  if (!userData) return null;
  // Omit sensitive/volatile fields that should only be trusted from the verified token/API
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { stripe_customer_id, treat_balance, ...safeData } = userData;
  return safeData;
}

export const useAuthStore = defineStore('auth', () => {
  // ========== State ==========

  const user = ref<User | null>(null);
  const token = ref<string | null>(null); // Memory only, no localStorage!
  const isAuthenticated = ref(false);
  const isInitialized = ref(false);

  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const lastLoginTime = ref(0);

  let balanceChannel: RealtimeChannel | null = null;

  // Singleton promise to avoid parallel refresh calls
  let refreshPromise: Promise<boolean> | null = null;

  // ========== Getters ==========
  const hasCompleteProfile = computed(() => {
    return !!(user.value?.email && user.value?.name);
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

  const isAdmin = computed(() => {
    // Primary check: permission-based
    if (hasPermission(PERMISSIONS.ACCESS_ADMIN)) return true;
    if (hasPermission(PERMISSIONS.USERS_READ)) return true;

    // Fallback: legacy role-based (during transition)
    const r = user.value?.role?.toLowerCase();
    return r === 'admin' || r === 'super_admin';
  });

  function hasPermission(permission: string): boolean {
    return user.value?.permissions?.includes(permission) || false;
  }

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
      } catch {
        // invalid user data
      }
    }

    // Always try to refresh token on init to check valid session
    // This effectively restores the session using the HttpOnly cookie
    await refreshToken();

    if (isAuthenticated.value) {
      setupBalanceRealtime();
    }

    isInitialized.value = true;
  }

  /**
   * Refresh access token using HttpOnly cookie
   */
  // State

  // ...

  async function refreshToken(): Promise<boolean> {
    if (refreshPromise) return refreshPromise;

    refreshPromise = (async () => {
      try {
        const response = await apiV1.post<{
          access_token: string | null;
          token_type: string | null;
          user?: User;
        }>('/auth/refresh-token');

        if (response.access_token) {
          token.value = response.access_token;
          isAuthenticated.value = true;
          if (response.user) {
            user.value = response.user;
            localStorage.setItem('user_data', JSON.stringify(sanitizeUserForCache(response.user)));
          }
          updateApiHeader(response.access_token);
          return true;
        }
        return false;
      } catch {
        // RACE CONDITION FIx:
        // If we just logged in (within last 5 seconds), ignore this background check failure.
        // This prevents initializeAuth() from wiping a session established by AuthCallback
        // while the refresh check was in flight.
        const justLoggedIn = Date.now() - lastLoginTime.value < 5000;

        if (isAuthenticated.value && !justLoggedIn) {
          clearAuth();
        }

        return false;
      } finally {
        refreshPromise = null;
      }
    })();

    return refreshPromise;
  }

  /**
   * Validate user object shape
   */
  function isValidUser(userData: unknown): userData is User {
    if (typeof userData !== 'object' || userData === null) {
      return false;
    }
    const obj = userData as Record<string, unknown>;
    return typeof obj.id === 'string' && typeof obj.email === 'string';
  }

  /**
   * Set authentication data after successful login
   */
  async function setAuth(data: LoginResponse) {
    user.value = data.user;
    token.value = data.access_token;
    isAuthenticated.value = true;
    error.value = null;
    lastLoginTime.value = Date.now();

    // Persist safe user data for UX
    localStorage.setItem('user_data', JSON.stringify(sanitizeUserForCache(data.user)));

    // Update headers/storage
    updateApiHeader(data.access_token);

    // Setup realtime
    setupBalanceRealtime();
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

    // Cleanup realtime
    if (balanceChannel) {
      supabase.removeChannel(balanceChannel);
      balanceChannel = null;
    }
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
      localStorage.setItem('user_data', JSON.stringify(sanitizeUserForCache(user.value)));
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

  function setupBalanceRealtime(): void {
    if (!user.value?.id) return;

    if (balanceChannel) {
      supabase.removeChannel(balanceChannel);
    }

    balanceChannel = supabase
      .channel(`user_balance_${user.value.id}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'users',
          filter: `id=eq.${user.value.id}`,
        },
        (payload: { new: { treat_balance: number } }): void => {
          if (payload.new && typeof payload.new.treat_balance === 'number' && user.value) {
            updateUser({ treat_balance: payload.new.treat_balance });
          }
        }
      )
      .subscribe();
  }

  // Watch for user changes to handle setup/cleanup
  watch(
    () => user.value?.id,
    (newId, oldId) => {
      if (oldId && !newId && balanceChannel) {
        supabase.removeChannel(balanceChannel);
        balanceChannel = null;
      } else if (newId && newId !== oldId) {
        setupBalanceRealtime();
      }
    }
  );

  // Initialize on store creation
  // Register callbacks to API utility to break circular dependency
  setAuthCallbacks(refreshToken, logout);

  return {
    // State
    user,
    token,
    isAuthenticated,
    isInitialized,
    isLoading,
    error,
    lastLoginTime,

    // Getters
    hasCompleteProfile,
    isUserReady,
    userDisplayName,
    userAvatar,
    isAdmin,
    hasPermission,

    // Actions
    initializeAuth,
    refreshToken,
    setAuth,
    clearAuth,
    verifySession,
    updateUser,
    getAuthHeader,
    logout,
  };
});
