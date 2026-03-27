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
 * A wrapper around useToastStore to provide a unified API.
 * Supports both shadcn-like { toast } and old { showToast } formats.
 */
export function useToast(): {
  toast: (options: ToastOptions) => string;
  showToast: (message: string, type?: ToastType) => string;
  dismiss: (id: string) => void;
  clear: () => void;
} {
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

  const showToast = (message: string, type: ToastType = 'info'): string => {
    const variantMap: Record<ToastType, ToastOptions['variant']> = {
      success: 'success',
      error: 'destructive',
      warning: 'warning',
      info: 'default',
    };

    return toast({
      description: message,
      variant: variantMap[type],
    });
  };

  return {
    toast,
    showToast,
    dismiss: (id: string): void => toastStore.removeToast(id),
    clear: (): void => toastStore.clearAllToasts(),
  };
}
