import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useNetwork } from '@/composables/useNetwork';
import { mount } from '@vue/test-utils';
import { defineComponent, nextTick } from 'vue';

describe('useNetwork', () => {
  let originalOnLine: boolean;

  beforeEach(() => {
    originalOnLine = navigator.onLine;
  });

  afterEach(() => {
    // Restore navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      value: originalOnLine,
      configurable: true,
    });
  });

  it('should initialize with current online status', () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
    const { isOnline } = useNetwork();
    expect(isOnline.value).toBe(true);
  });

  it('should respond to offline event', async () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
    
    let result: any;
    const TestComponent = defineComponent({
      setup() {
        result = useNetwork();
        return () => {};
      }
    });
    
    mount(TestComponent);
    
    expect(result.isOnline.value).toBe(true);

    // Simulate going offline
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true });
    window.dispatchEvent(new Event('offline'));

    await nextTick();

    expect(result.isOnline.value).toBe(false);
    expect(result.offlineAt.value).toBeInstanceOf(Date);
  });

  it('should respond to online event', async () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true });
    
    let result: any;
    const TestComponent = defineComponent({
        setup() {
            result = useNetwork();
            return () => {};
        }
    });

    mount(TestComponent);
    
    // Simulate going online
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
    window.dispatchEvent(new Event('online'));
    
    await nextTick();

    expect(result.isOnline.value).toBe(true);
    expect(result.offlineAt.value).toBe(null);
  });

  it('should remove event listeners on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
    
    const TestComponent = defineComponent({
      setup() {
        useNetwork();
        return {};
      }
    });

    const wrapper = mount(TestComponent);
    wrapper.unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
  });
});
