/**
 * Pinia Toast Store
 *
 * Centralized notification/toast management.
 * Supports multiple toast types with auto-dismiss.
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Toast, ToastType } from '../types/toast';

export const useToastStore = defineStore('toast', () => {
  // ========== State ==========
  const toasts = ref<Toast[]>([]);
  let idCounter = 0;

  // ========== Getters ==========
  const activeToasts = computed(() => toasts.value);
  const hasToasts = computed(() => toasts.value.length > 0);
  const errorCount = computed(() => toasts.value.filter((t) => t.type === 'error').length);

  // ========== Actions ==========

  /**
   * Add a new toast notification
   */
  function addToast(
    messageOrOptions: string | Omit<Toast, 'id'>,
    type: ToastType = 'info',
    duration: number = 5000,
    title?: string
  ): string {
    const id = `${Date.now()}-${idCounter++}`;

    let toast: Toast;
    if (typeof messageOrOptions === 'string') {
      toast = { id, type, message: messageOrOptions, duration, title };
    } else {
      toast = { ...messageOrOptions, id };
    }

    toasts.value.push(toast);

    // Auto-remove after duration (if not 0)
    const toastDuration = toast.duration ?? duration;
    if (toastDuration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, toastDuration);
    }

    return id;
  }

  /**
   * Remove a toast by ID
   */
  function removeToast(id: string): void {
    const index = toasts.value.findIndex((t) => t.id === id);
    if (index !== -1) {
      toasts.value.splice(index, 1);
    }
  }

  /**
   * Remove all toasts
   */
  function clearAllToasts(): void {
    toasts.value = [];
  }

  /**
   * Show success toast
   */
  function showSuccess(
    messageOrOptions: string | Omit<Toast, 'id' | 'type'>,
    title: string = 'Success'
  ): string {
    if (typeof messageOrOptions === 'string') {
      return addToast(messageOrOptions, 'success', 4000, title);
    }
    return addToast({ ...messageOrOptions, type: 'success' }, 'success', 4000);
  }

  /**
   * Show error toast
   */
  function showError(
    messageOrOptions: string | Omit<Toast, 'id' | 'type'>,
    title: string = 'Error'
  ): string {
    if (typeof messageOrOptions === 'string') {
      return addToast(messageOrOptions, 'error', 6000, title);
    }
    return addToast({ ...messageOrOptions, type: 'error' }, 'error', 6000);
  }

  /**
   * Show warning toast
   */
  function showWarning(
    messageOrOptions: string | Omit<Toast, 'id' | 'type'>,
    title: string = 'Warning'
  ): string {
    if (typeof messageOrOptions === 'string') {
      return addToast(messageOrOptions, 'warning', 5000, title);
    }
    return addToast({ ...messageOrOptions, type: 'warning' }, 'warning', 5000);
  }

  /**
   * Show info toast
   */
  function showInfo(messageOrOptions: string | Omit<Toast, 'id' | 'type'>, title?: string): string {
    if (typeof messageOrOptions === 'string') {
      return addToast(messageOrOptions, 'info', 5000, title);
    }
    return addToast({ ...messageOrOptions, type: 'info' }, 'info', 5000);
  }

  return {
    // State
    toasts,

    // Getters
    activeToasts,
    hasToasts,
    errorCount,

    // Actions
    addToast,
    removeToast,
    clearAllToasts,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };
});

// ========== Legacy exports for backward compatibility ==========
let _store: ReturnType<typeof useToastStore> | null = null;

function getStore(): ReturnType<typeof useToastStore> | null {
  if (!_store) {
    try {
      _store = useToastStore();
    } catch {
      return null;
    }
  }
  return _store;
}

// Legacy reactive export
export const toastState = {
  get toasts(): Toast[] {
    return getStore()?.toasts ?? [];
  },
};

// Legacy function exports
export function addToast(
  messageOrOptions: string | Omit<Toast, 'id'>,
  type: ToastType = 'info',
  duration: number = 5000,
  title?: string
): string {
  return getStore()?.addToast(messageOrOptions, type, duration, title) ?? '';
}

export function removeToast(id: string): void {
  getStore()?.removeToast(id);
}

export function showError(
  messageOrOptions: string | Omit<Toast, 'id' | 'type'>,
  title: string = 'Error'
): string {
  return getStore()?.showError(messageOrOptions, title) ?? '';
}

export function showSuccess(
  messageOrOptions: string | Omit<Toast, 'id' | 'type'>,
  title: string = 'Success'
): string {
  return getStore()?.showSuccess(messageOrOptions, title) ?? '';
}
