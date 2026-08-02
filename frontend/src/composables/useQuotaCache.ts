import { useAuthStore } from '../stores/authStore';

export interface UploadQuotaStatus {
  used: number;
  limit: number;
  remaining: number;
  is_pro: boolean;
  resets_at: string | null;
  reset_type: string | null;
}

const QUOTA_CACHE_KEY = 'upload_quota_cache_v1';
const QUOTA_CACHE_TTL_MS = 60 * 1000;

export function useQuotaCache(): {
  readQuotaCache: () => UploadQuotaStatus | null;
  writeQuotaCache: (data: UploadQuotaStatus) => void;
  clearQuotaCache: () => void;
} {
  const authStore = useAuthStore();

  const readQuotaCache = (): UploadQuotaStatus | null => {
    if (typeof window === 'undefined') return null;
    try {
      const raw = sessionStorage.getItem(QUOTA_CACHE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as {
        userId?: string;
        timestamp?: number;
        data?: UploadQuotaStatus;
      };

      const currentUserId = authStore.user?.id;
      if (!currentUserId || parsed.userId !== currentUserId) return null;
      if (!parsed.timestamp || Date.now() - parsed.timestamp > QUOTA_CACHE_TTL_MS) return null;
      return parsed.data ?? null;
    } catch {
      return null;
    }
  };

  const writeQuotaCache = (data: UploadQuotaStatus): void => {
    if (typeof window === 'undefined') return;
    const currentUserId = authStore.user?.id;
    if (!currentUserId) return;
    sessionStorage.setItem(
      QUOTA_CACHE_KEY,
      JSON.stringify({
        userId: currentUserId,
        timestamp: Date.now(),
        data,
      })
    );
  };

  const clearQuotaCache = (): void => {
    if (typeof window === 'undefined') return;
    sessionStorage.removeItem(QUOTA_CACHE_KEY);
  };

  return {
    readQuotaCache,
    writeQuotaCache,
    clearQuotaCache,
  };
}
