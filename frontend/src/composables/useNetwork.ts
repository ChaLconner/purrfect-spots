import { ref, onMounted, onUnmounted, readonly } from 'vue';

export function useNetwork() {
  const isOnline = ref(navigator.onLine);
  const offlineAt = ref<Date | null>(null);

  function updateOnlineStatus() {
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
