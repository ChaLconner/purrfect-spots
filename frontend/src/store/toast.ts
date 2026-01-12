import { reactive } from 'vue';
import type { Toast, ToastType } from '../types/toast';

interface ToastState {
  toasts: Toast[];
}

// Reactive state
export const toastState = reactive<ToastState>({
  toasts: [],
});

let idCounter = 0;

/**
 * Add a new toast notification
 * @param message The message to display
 * @param type 'success' | 'error' | 'warning' | 'info'
 * @param duration Duration in ms (default 5000), 0 for persistent
 * @param title Optional title
 */
export function addToast(message: string, type: ToastType = 'info', duration: number = 5000, title?: string) {
  const id = Date.now().toString() + '-' + (idCounter++);
  const toast: Toast = { id, type, message, duration, title };
  
  // Add to the beginning of the array for stack effect (newest on top/bottom depending on rendering)
  // Usually appending is better for "stacking up"
  toastState.toasts.push(toast);
  
  return id;
}

/**
 * Remove a toast by ID
 * @param id The toast ID
 */
export function removeToast(id: string) {
  const index = toastState.toasts.findIndex(t => t.id === id);
  if (index !== -1) {
    toastState.toasts.splice(index, 1);
  }
}

// Error specific helper
export function showError(message: string, title: string = 'Error') {
  addToast(message, 'error', 6000, title); // Errors now auto-dismiss after 6s
}

// Success specific helper
export function showSuccess(message: string, title: string = 'Success') {
  addToast(message, 'success', 4000, title);
}
