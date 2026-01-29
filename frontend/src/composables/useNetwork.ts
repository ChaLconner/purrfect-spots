import { ref, onMounted, onUnmounted, readonly } from 'vue';

export function useNetwork() {
  const isOnline = ref(navigator.onLine);
  const offlineAt = ref<Date | null>(null);

  function updateOnlineStatus() {
    isOnline.value = navigator.onLine;
    if (!isOnline.value) {
      offlineAt.value = new Date();
    } else {
      offlineAt.value = null;
    }
  }

  onMounted(() => {
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
  });

  onUnmounted(() => {
    window.removeEventListener('online', updateOnlineStatus);
    window.removeEventListener('offline', updateOnlineStatus);
  });

  return {
    isOnline: readonly(isOnline),
    offlineAt: readonly(offlineAt),
  };
}
