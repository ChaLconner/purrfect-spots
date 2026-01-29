import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useToastStore, addToast as legacyAddToast, removeToast as legacyRemoveToast, showError as legacyShowError, showSuccess as legacyShowSuccess, toastState } from '@/store/toastStore';

describe('Toast Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();
  });

  it('starts with empty state', () => {
    const store = useToastStore();
    expect(store.toasts).toHaveLength(0);
    expect(store.hasToasts).toBe(false);
    expect(store.errorCount).toBe(0);
  });

  it('adds a toast', () => {
    const store = useToastStore();
    const id = store.addToast('Test Message', 'info', 1000, 'Test Title');

    expect(store.toasts).toHaveLength(1);
    expect(store.toasts[0]).toEqual({
      id,
      type: 'info',
      message: 'Test Message',
      duration: 1000,
      title: 'Test Title',
    });
  });

  it('removes a toast manually', () => {
    const store = useToastStore();
    const id = store.addToast('Test');
    
    expect(store.toasts).toHaveLength(1);
    
    store.removeToast(id);
    expect(store.toasts).toHaveLength(0);
  });

  it('auto-removes toast after duration', () => {
    const store = useToastStore();
    store.addToast('Test', 'info', 1000);
    
    expect(store.toasts).toHaveLength(1);
    
    vi.advanceTimersByTime(1001);
    
    expect(store.toasts).toHaveLength(0);
  });

  it('clears all toasts', () => {
    const store = useToastStore();
    store.addToast('T1');
    store.addToast('T2');
    
    expect(store.toasts).toHaveLength(2);
    
    store.clearAllToasts();
    
    expect(store.toasts).toHaveLength(0);
  });

  it('helper methods work correctly', () => {
    const store = useToastStore();
    
    store.showSuccess('Success!');
    expect(store.toasts[0].type).toBe('success');
    expect(store.toasts[0].title).toBe('Success');

    store.showError('Error!');
    expect(store.toasts[1].type).toBe('error');
    expect(store.toasts[1].title).toBe('Error');
    expect(store.errorCount).toBe(1);

    store.showWarning('Warning!');
    expect(store.toasts[2].type).toBe('warning');

    store.showInfo('Info');
    expect(store.toasts[3].type).toBe('info');
  });

  it('legacy helpers work correctly', () => {
    // legacy helpers rely on getStore, which relies on active pinia
    // Since we called setActivePinia in beforeEach, this should work
    
    // First call to initialize internal store ref
    const id1 = legacyAddToast('Legacy Test');
    expect(useToastStore().toasts).toHaveLength(1);

    legacyShowSuccess('Legacy Success');
    expect(useToastStore().toasts).toHaveLength(2);
    expect(useToastStore().toasts[1].type).toBe('success');

    legacyShowError('Legacy Error');
    expect(useToastStore().toasts).toHaveLength(3);
    
    legacyRemoveToast(id1);
    expect(useToastStore().toasts).toHaveLength(2);
    
    // Check legacy reactive export
    expect(toastState.toasts).toHaveLength(2);
  });
});
