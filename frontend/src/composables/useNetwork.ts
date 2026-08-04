import {
  getFailedMutationCount,
  getPendingMutationCount,
  flushOfflineQueue,
  subscribeOfflineQueue,
  type OfflineFlushResult,
} from '@/utils/offlineQueue';
import { ref, onMounted, onUnmounted, getCurrentInstance, readonly, type DeepReadonly, type Ref } from 'vue';

export interface UseNetworkReturn {
  isOnline: DeepReadonly<Ref<boolean>>;
  offlineAt: DeepReadonly<Ref<Date | null>>;
  pendingSyncCount: DeepReadonly<Ref<number>>;
  failedSyncCount: DeepReadonly<Ref<number>>;
  isSyncing: DeepReadonly<Ref<boolean>>;
  lastSyncError: DeepReadonly<Ref<string | null>>;
  syncNow: () => Promise<OfflineFlushResult>;
  retryFailed: () => Promise<OfflineFlushResult>;
}

function readOnlineState(): boolean {
  return typeof navigator === 'undefined' ? true : navigator.onLine;
}

const sharedIsOnline = ref(readOnlineState());
const sharedOfflineAt = ref<Date | null>(sharedIsOnline.value ? null : new Date());
const sharedPendingSyncCount = ref(0);
const sharedFailedSyncCount = ref(0);
const sharedIsSyncing = ref(false);
const sharedLastSyncError = ref<string | null>(null);
let unsubscribeQueue: (() => void) | null = null;

async function refreshQueueState(): Promise<void> {
  [sharedPendingSyncCount.value, sharedFailedSyncCount.value] = await Promise.all([
    getPendingMutationCount(),
    getFailedMutationCount(),
  ]);
}

async function syncNow(): Promise<OfflineFlushResult> {
  if (!sharedIsOnline.value) {
    return {
      processed: 0,
      remaining: sharedPendingSyncCount.value,
      failed: sharedFailedSyncCount.value,
    };
  }
  if (sharedIsSyncing.value) {
    return {
      processed: 0,
      remaining: sharedPendingSyncCount.value,
      failed: sharedFailedSyncCount.value,
    };
  }

  sharedIsSyncing.value = true;
  sharedLastSyncError.value = null;
  try {
    const result = await flushOfflineQueue({ force: true });
    await refreshQueueState();
    return result;
  } catch (error) {
    sharedLastSyncError.value = error instanceof Error ? error.message : 'Offline sync failed';
    await refreshQueueState();
    throw error;
  } finally {
    sharedIsSyncing.value = false;
  }
}

async function retryFailed(): Promise<OfflineFlushResult> {
  if (!sharedIsOnline.value) {
    return {
      processed: 0,
      remaining: sharedPendingSyncCount.value,
      failed: sharedFailedSyncCount.value,
    };
  }
  if (sharedIsSyncing.value) {
    return {
      processed: 0,
      remaining: sharedPendingSyncCount.value,
      failed: sharedFailedSyncCount.value,
    };
  }

  sharedIsSyncing.value = true;
  sharedLastSyncError.value = null;
  try {
    const result = await flushOfflineQueue({ retryFailed: true, force: true });
    await refreshQueueState();
    return result;
  } catch (error) {
    sharedLastSyncError.value = error instanceof Error ? error.message : 'Offline sync failed';
    await refreshQueueState();
    throw error;
  } finally {
    sharedIsSyncing.value = false;
  }
}

function updateOnlineStatus(): void {
  sharedIsOnline.value = readOnlineState();
  if (sharedIsOnline.value) {
    sharedOfflineAt.value = null;
    void syncNow();
  } else {
    sharedOfflineAt.value = new Date();
  }
}

function attachListeners(): () => void {
  if (typeof globalThis.addEventListener !== 'function') return () => undefined;
  const onlineHandler = (): void => updateOnlineStatus();
  const offlineHandler = (): void => updateOnlineStatus();
  const visibilityHandler = (): void => {
    if (typeof document === 'undefined' || document.visibilityState === 'visible') void syncNow();
  };
  globalThis.addEventListener('online', onlineHandler);
  globalThis.addEventListener('offline', offlineHandler);
  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', visibilityHandler);
  }
  if (!unsubscribeQueue) {
    unsubscribeQueue = subscribeOfflineQueue(() => {
      void refreshQueueState();
    });
  }
  return () => {
    globalThis.removeEventListener('online', onlineHandler);
    globalThis.removeEventListener('offline', offlineHandler);
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', visibilityHandler);
    }
  };
}

export function useNetwork(): UseNetworkReturn {
  sharedIsOnline.value = readOnlineState();
  if (!sharedIsOnline.value && !sharedOfflineAt.value) sharedOfflineAt.value = new Date();
  if (sharedIsOnline.value) sharedOfflineAt.value = null;
  void refreshQueueState();

  if (getCurrentInstance()) {
    let detachNetworkListeners: (() => void) | null = null;
    onMounted(() => {
      detachNetworkListeners = attachListeners();
      void refreshQueueState();
      void syncNow();
    });

    onUnmounted(() => {
      detachNetworkListeners?.();
    });
  }

  return {
    isOnline: readonly(sharedIsOnline),
    offlineAt: readonly(sharedOfflineAt),
    pendingSyncCount: readonly(sharedPendingSyncCount),
    failedSyncCount: readonly(sharedFailedSyncCount),
    isSyncing: readonly(sharedIsSyncing),
    lastSyncError: readonly(sharedLastSyncError),
    syncNow,
    retryFailed,
  };
}
