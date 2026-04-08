import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent, h, nextTick } from 'vue';
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue';

 
// A component that throws an error
const BuggyComponent = defineComponent({
  methods: {
    throwError(): never {
      throw new Error('Test Error');
    },
  },
  render() {
    return h('div', this.throwError());
  },
});

// Mock useRouter
vi.mock('vue-router', (): Record<string, unknown> => ({
  useRouter: (): Record<string, unknown> => ({
    push: vi.fn(),
  }),
}));

vi.mock('vue-i18n', (): Record<string, unknown> => ({
  useI18n: (): { t: (key: string) => string } => ({ t: (key: string): string => key }),
}));

vi.mock('@/components/toast/use-toast', (): Record<string, unknown> => ({
  useToast: (): Record<string, unknown> => ({
    toast: vi.fn(),
  }),
}));

describe('ErrorBoundary', (): void => {
  beforeEach((): void => {
    vi.clearAllMocks();
  });

  it('renders slot content when no error occurs', (): void => {
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: '<div class="content">Fine</div>',
      },
    });
 
    expect(wrapper.find('.content').exists()).toBe(true);
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  });

  it('captures errors from child components and shows error UI', async (): Promise<void> => {
    // We need to suppress console.error for this test to keep the logs clean
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation((): void => {});
 
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: h(BuggyComponent),
      },
    });
    
    await nextTick();
 
    // In Vue 3, ErrorBoundary (onErrorCaptured) should react immediately
    expect(wrapper.find('[role="alert"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('common.somethingWentWrong');
    expect(wrapper.text()).toContain('Test Error');
    
    consoleSpy.mockRestore();
  });

  it('shows custom fallback message', async (): Promise<void> => {
    vi.spyOn(console, 'error').mockImplementation((): void => {});
    
    // Create a component that throws an error without a message
    const NoMessageBuggy = defineComponent({
      render(): any {
        return h('div', (() => {
          throw new Error();
        })());
      },
    });

    const wrapper = mount(ErrorBoundary, {
      props: {
        fallbackMessage: 'Custom Error Msg',
      },
      slots: {
        default: h(NoMessageBuggy),
      },
    });

    await nextTick();
    expect(wrapper.text()).toContain('Custom Error Msg');
  });

  it('emits error event when an error is caught', async (): Promise<void> => {
    vi.spyOn(console, 'error').mockImplementation((): void => {});
    
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: h(BuggyComponent),
      },
    });
 
    await nextTick();
    expect(wrapper.emitted('error')).toBeTruthy();
    const emitted = wrapper.emitted('error');
    expect(emitted && emitted[0][0]).toBeInstanceOf(Error);
  });

  it('resets state when retry button is clicked', async (): Promise<void> => {
    vi.spyOn(console, 'error').mockImplementation((): void => {});
    
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
    
    const buttons = wrapper.findAll('button');
    const retryButton = buttons.find(b => b.text().includes('common.tryAgain'));
    
    expect(retryButton).toBeDefined();
    if (retryButton) {
      await retryButton.trigger('click');
    }
    
    expect(wrapper.emitted('retry')).toBeTruthy();
  });
});
