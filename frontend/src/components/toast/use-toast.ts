import { useToastStore } from '@/store/toastStore';
import type { ToastType } from '@/types/toast';

interface ToastOptions {
  title?: string;
  description: string;
  variant?: 'default' | 'destructive' | 'success' | 'warning';
  duration?: number;
}

/**
 * useToast Composable
 *
 * A wrapper around useToastStore to provide a shadcn-like API
 */
export function useToast() {
  const toastStore = useToastStore();

  const toast = (options: ToastOptions): string => {
    const typeMap: Record<string, ToastType> = {
      default: 'info',
      destructive: 'error',
      success: 'success',
      warning: 'warning',
    };

    const type = typeMap[options.variant || 'default'] || 'info';

    return toastStore.addToast(options.description, type, options.duration, options.title);
  };

  return {
    toast,
    dismiss: (id: string): void => toastStore.removeToast(id),
    clear: (): void => toastStore.clearAllToasts(),
  };
}
