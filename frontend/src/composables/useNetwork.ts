import { ref, onMounted, onUnmounted, readonly, type DeepReadonly, type Ref } from 'vue';

export interface UseNetworkReturn {
  isOnline: DeepReadonly<Ref<boolean>>;
  offlineAt: DeepReadonly<Ref<Date | null>>;
}

export function useNetwork(): UseNetworkReturn {
  const isOnline = ref(navigator.onLine);
  const offlineAt = ref<Date | null>(null);

  function updateOnlineStatus(): void {
    isOnline.value = navigator.onLine;
    if (isOnline.value) {
      offlineAt.value = null;
    } else {
      offlineAt.value = new Date();
    }
  }

  onMounted(() => {
    globalThis.addEventListener('online', updateOnlineStatus);
    globalThis.addEventListener('offline', updateOnlineStatus);
  });

  onUnmounted(() => {
    globalThis.removeEventListener('online', updateOnlineStatus);
    globalThis.removeEventListener('offline', updateOnlineStatus);
  });

  return {
    isOnline: readonly(isOnline),
    offlineAt: readonly(offlineAt),
  };
}
