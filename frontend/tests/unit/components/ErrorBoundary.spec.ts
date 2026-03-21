import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent, h, nextTick } from 'vue';
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue';

// A component that throws an error
const BuggyComponent = defineComponent({
  methods: {
    throwError() {
      throw new Error('Test Error');
    }
  },
  template: '<div>{{ throwError() }}</div>'
});

// Mock useRouter
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders slot content when no error occurs', () => {
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: '<div class="content">Fine</div>',
      },
    });

    expect(wrapper.find('.content').exists()).toBe(true);
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  });

  it('captures errors from child components and shows error UI', async () => {
    // We need to suppress console.error for this test to keep the logs clean
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: h(BuggyComponent),
      },
    });
    
    await nextTick();

    // In Vue 3, ErrorBoundary (onErrorCaptured) should react immediately
    expect(wrapper.find('[role="alert"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Something went wrong');
    
    consoleSpy.mockRestore();
  });

  it('shows custom fallback message', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    
    const wrapper = mount(ErrorBoundary, {
      props: {
        fallbackMessage: 'Custom Error Msg',
      },
      slots: {
        default: h(BuggyComponent),
      },
    });

    await nextTick();
    expect(wrapper.text()).toContain('Custom Error Msg');
  });

  it('emits error event when an error is caught', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: h(BuggyComponent),
      },
    });

    await nextTick();
    expect(wrapper.emitted('error')).toBeTruthy();
    expect(wrapper.emitted('error')![0][0]).toBeInstanceOf(Error);
  });

  it('resets state when retry button is clicked', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: h(BuggyComponent),
      },
    });

    await nextTick();
    expect(wrapper.find('[role="alert"]').exists()).toBe(true);
    
    // We need a way to stop the child from throwing again on re-render if we want to test "recovery"
    // but handleRetry just sets hasError = false. If we stay on the same page with the same buggy component,
    // it will just throw again.
    
    const retryButton = wrapper.find('button');
    await retryButton.trigger('click');
    
    expect(wrapper.emitted('retry')).toBeTruthy();
  });
});
