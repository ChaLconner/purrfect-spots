import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useToastStore } from '@/store/toastStore';

describe('useToastStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('should start with empty toasts', () => {
    const store = useToastStore();
    expect(store.toasts).toEqual([]);
    expect(store.hasToasts).toBe(false);
  });

  it('addToast should add a toast', () => {
    const store = useToastStore();
    store.addToast('Hello World', 'info');
    expect(store.toasts.length).toBe(1);
    expect(store.toasts[0].message).toBe('Hello World');
    expect(store.toasts[0].type).toBe('info');
  });

  it('removeToast should remove a toast by id', () => {
    const store = useToastStore();
    const id = store.addToast('To remove');
    expect(store.toasts.length).toBe(1);
    
    store.removeToast(id);
    expect(store.toasts.length).toBe(0);
  });

  it('clearAllToasts should remove all toasts', () => {
    const store = useToastStore();
    store.addToast('One');
    store.addToast('Two');
    expect(store.toasts.length).toBe(2);
    
    store.clearAllToasts();
    expect(store.toasts.length).toBe(0);
  });

  it('helpers like showSuccess should add correct toast type', () => {
    const store = useToastStore();
    store.showSuccess('Success!');
    expect(store.toasts[0].type).toBe('success');
    expect(store.toasts[0].message).toBe('Success!');
  });
});
