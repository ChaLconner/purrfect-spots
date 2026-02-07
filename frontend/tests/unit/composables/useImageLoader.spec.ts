import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useImageLoader } from '@/composables/useImageLoader';
import { mount, flushPromises } from '@vue/test-utils';
import { defineComponent, nextTick } from 'vue';

describe('useImageLoader', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should initialize with correct state for non-lazy loading', () => {
      const TestComponent = defineComponent({
        setup() {
          const result = useImageLoader({ src: 'https://example.com/cat.jpg', lazy: false });
          return result;
        },
        render() {
          return null;
        },
      });

      const wrapper = mount(TestComponent);
      const vm = wrapper.vm as ReturnType<typeof useImageLoader>;

      expect(vm.isLoaded).toBe(false);
      expect(vm.hasError).toBe(false);
      expect(vm.isIntersecting).toBe(true); // lazy=false means immediate intersection
      expect(vm.imageRef).toBeNull();

      wrapper.unmount();
    });

    it('should be intersecting immediately when lazy is false', () => {
      const TestComponent = defineComponent({
        setup() {
          return useImageLoader({ src: 'https://example.com/cat.jpg', lazy: false });
        },
        render() {
          return null;
        },
      });

      const wrapper = mount(TestComponent);
      const vm = wrapper.vm as ReturnType<typeof useImageLoader>;

      expect(vm.isIntersecting).toBe(true);

      wrapper.unmount();
    });
  });

  describe('Load Handling', () => {
    it('should set isLoaded to true on handleLoad', () => {
      const TestComponent = defineComponent({
        setup() {
          return useImageLoader({ src: 'https://example.com/cat.jpg', lazy: false });
        },
        render() {
          return null;
        },
      });

      const wrapper = mount(TestComponent);
      const vm = wrapper.vm as ReturnType<typeof useImageLoader>;

      expect(vm.isLoaded).toBe(false);
      vm.handleLoad();
      expect(vm.isLoaded).toBe(true);

      wrapper.unmount();
    });
  });

  describe('Error Handling', () => {
    it('should set hasError to true on handleError', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const TestComponent = defineComponent({
        setup() {
          return useImageLoader({ src: 'https://example.com/cat.jpg', lazy: false });
        },
        render() {
          return null;
        },
      });

      const wrapper = mount(TestComponent);
      const vm = wrapper.vm as ReturnType<typeof useImageLoader>;

      expect(vm.hasError).toBe(false);
      vm.handleError(new Event('error'));
      expect(vm.hasError).toBe(true);
      expect(consoleSpy).toHaveBeenCalled();

      wrapper.unmount();
      consoleSpy.mockRestore();
    });
  });

  describe('Retry', () => {
    it('should reset state on retry', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const TestComponent = defineComponent({
        setup() {
          return useImageLoader({ src: 'https://example.com/cat.jpg', lazy: false });
        },
        render() {
          return null;
        },
      });

      const wrapper = mount(TestComponent);
      const vm = wrapper.vm as ReturnType<typeof useImageLoader>;

      // Simulate error
      vm.handleError(new Event('error'));
      expect(vm.hasError).toBe(true);

      // Retry (for non-lazy, it just resets state)
      vm.retry();
      expect(vm.hasError).toBe(false);
      expect(vm.isLoaded).toBe(false);

      wrapper.unmount();
      consoleSpy.mockRestore();
    });

    it('should reset intersection for lazy loading on retry', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Skip IntersectionObserver for this test
      const originalIO = globalThis.IntersectionObserver;
      // @ts-expect-error - removing for test
      delete globalThis.IntersectionObserver;

      const TestComponent = defineComponent({
        setup() {
          return useImageLoader({ src: 'https://example.com/cat.jpg', lazy: true });
        },
        render() {
          return null;
        },
      });

      const wrapper = mount(TestComponent);
      const vm = wrapper.vm as ReturnType<typeof useImageLoader>;

      // Simulate error
      vm.handleError(new Event('error'));
      expect(vm.hasError).toBe(true);

      // Retry
      vm.retry();
      expect(vm.hasError).toBe(false);
      expect(vm.isLoaded).toBe(false);
      expect(vm.isIntersecting).toBe(false);

      // After timeout, should re-intersect
      vi.advanceTimersByTime(100);
      await nextTick();
      expect(vm.isIntersecting).toBe(true);

      wrapper.unmount();
      consoleSpy.mockRestore();

      // Restore
      globalThis.IntersectionObserver = originalIO;
    });
  });

  describe('Fallback for no IntersectionObserver', () => {
    it('should set isIntersecting true if no IntersectionObserver', async () => {
      // Remove IntersectionObserver
      const originalIO = globalThis.IntersectionObserver;
      // @ts-expect-error - Removing for test
      delete globalThis.IntersectionObserver;

      const TestComponent = defineComponent({
        setup() {
          const loader = useImageLoader({
            src: 'https://example.com/cat.jpg',
            lazy: true,
          });
          return loader;
        },
        template: '<div ref="imageRef">Image</div>',
      });

      const wrapper = mount(TestComponent);
      const vm = wrapper.vm as ReturnType<typeof useImageLoader>;
      await flushPromises();

      expect(vm.isIntersecting).toBe(true);

      wrapper.unmount();

      // Restore
      globalThis.IntersectionObserver = originalIO;
    });
  });
});
