import { authStore } from '../store/auth';

export function requireAuth(): boolean {
  return authStore.isAuthenticated;
}

export function useAuthGuard() {
  const isAuthenticated = () => authStore.isAuthenticated;
  const getUser = () => authStore.user;
  const getToken = () => authStore.token;

  return {
    isAuthenticated,
    getUser,
    getToken,
  };
}
