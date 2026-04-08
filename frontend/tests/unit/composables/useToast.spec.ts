import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useToast } from '@/composables/useToast';
import { useToastStore } from '@/store/toastStore';
import { setActivePinia, createPinia } from 'pinia';

describe('useToast', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('should add an info toast by default', () => {
    const { toast } = useToast();
    const toastStore = useToastStore();
    const addToastSpy = vi.spyOn(toastStore, 'addToast');

    toast({ description: 'Hello World' });

    expect(addToastSpy).toHaveBeenCalledWith('Hello World', 'info', undefined, undefined);
  });

  it('should map variant to toast type correctly', () => {
    const { toast } = useToast();
    const toastStore = useToastStore();
    const addToastSpy = vi.spyOn(toastStore, 'addToast');

    toast({ description: 'Success', variant: 'success' });
    expect(addToastSpy).toHaveBeenCalledWith('Success', 'success', undefined, undefined);

    toast({ description: 'Error', variant: 'destructive' });
    expect(addToastSpy).toHaveBeenCalledWith('Error', 'error', undefined, undefined);

    toast({ description: 'Warning', variant: 'warning' });
    expect(addToastSpy).toHaveBeenCalledWith('Warning', 'warning', undefined, undefined);
  });

  it('should support showToast with type', () => {
    const { showToast } = useToast();
    const toastStore = useToastStore();
    const addToastSpy = vi.spyOn(toastStore, 'addToast');

    showToast('Info message');
    expect(addToastSpy).toHaveBeenCalledWith('Info message', 'info', undefined, undefined);

    showToast('Success message', 'success');
    expect(addToastSpy).toHaveBeenCalledWith('Success message', 'success', undefined, undefined);
  });

  it('should support dismiss and clear', () => {
    const { dismiss, clear } = useToast();
    const toastStore = useToastStore();
    const removeSpy = vi.spyOn(toastStore, 'removeToast');
    const clearSpy = vi.spyOn(toastStore, 'clearAllToasts');

    dismiss('123');
    expect(removeSpy).toHaveBeenCalledWith('123');

    clear();
    expect(clearSpy).toHaveBeenCalled();
  });
});
