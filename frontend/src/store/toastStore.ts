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
    message: string,
    type: ToastType = 'info',
    duration: number = 5000,
    title?: string
  ): string {
    const id = `${Date.now()}-${idCounter++}`;
    const toast: Toast = { id, type, message, duration, title };

    toasts.value.push(toast);

    // Auto-remove after duration (if not 0)
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }

    return id;
  }

  /**
   * Remove a toast by ID
   */
  function removeToast(id: string) {
    const index = toasts.value.findIndex((t) => t.id === id);
    if (index !== -1) {
      toasts.value.splice(index, 1);
    }
  }

  /**
   * Remove all toasts
   */
  function clearAllToasts() {
    toasts.value = [];
  }

  /**
   * Show success toast
   */
  function showSuccess(message: string, title: string = 'Success') {
    return addToast(message, 'success', 4000, title);
  }

  /**
   * Show error toast
   */
  function showError(message: string, title: string = 'Error') {
    return addToast(message, 'error', 6000, title);
  }

  /**
   * Show warning toast
   */
  function showWarning(message: string, title: string = 'Warning') {
    return addToast(message, 'warning', 5000, title);
  }

  /**
   * Show info toast
   */
  function showInfo(message: string, title?: string) {
    return addToast(message, 'info', 5000, title);
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

function getStore() {
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
  get toasts() {
    return getStore()?.toasts ?? [];
  },
};

// Legacy function exports
export function addToast(
  message: string,
  type: ToastType = 'info',
  duration: number = 5000,
  title?: string
) {
  return getStore()?.addToast(message, type, duration, title) ?? '';
}

export function removeToast(id: string) {
  getStore()?.removeToast(id);
}

export function showError(message: string, title: string = 'Error') {
  return getStore()?.showError(message, title) ?? '';
}

export function showSuccess(message: string, title: string = 'Success') {
  return getStore()?.showSuccess(message, title) ?? '';
}
