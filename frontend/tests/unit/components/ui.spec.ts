import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
import BaseButton from '@/components/ui/BaseButton.vue';
import BaseCard from '@/components/ui/BaseCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import ErrorState from '@/components/ui/ErrorState.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    useRouter: vi.fn(() => ({
      push: vi.fn(),
    })),
    useRoute: () => ({
      path: '/'
    })
  };
});

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

vi.mock('@/components/toast/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

import { config } from '@vue/test-utils';

// Provide base stubs that don't break slots
const baseStubs = {
  RouterLink: { template: '<a><slot /></a>' },
  RouterView: { template: '<div><slot /></div>' }
};

const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  resolve: vi.fn((to) => ({ href: to })),
  currentRoute: { value: { path: '/' } },
  addRoute: vi.fn(),
  removeRoute: vi.fn(),
  hasRoute: vi.fn(),
  getRoutes: vi.fn(() => []),
  options: { history: {} as any, routes: [] },
  isReady: vi.fn(() => Promise.resolve()),
  install: vi.fn(),
};

// Set global config for all tests in this file
config.global.plugins = [mockRouter as any];
config.global.stubs = baseStubs;
config.global.mocks = {
  $t: (msg: string) => msg
};

describe('ErrorBoundary Component', () => {
  it('should render slot content when no error', () => {
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: '<div class="child">Child Content</div>'
      }
    });

    expect(wrapper.find('.child').exists()).toBe(true);
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  });
});

describe('SkeletonLoader Component', () => {
  it('should render with default props', () => {
    const wrapper = mount(SkeletonLoader);
    const element = wrapper.find('div');

    expect(element.exists()).toBe(true);
    expect(element.attributes('style')).toContain('width: 100%');
    expect(element.attributes('style')).toContain('height: 100%');
  });

  it('should apply custom dimensions', () => {
    const wrapper = mount(SkeletonLoader, {
      props: {
        width: '200px',
        height: '100px'
      }
    });

    const element = wrapper.find('div');
    expect(element.attributes('style')).toContain('width: 200px');
    expect(element.attributes('style')).toContain('height: 100px');
  });
});

describe('BaseButton Component', () => {
  it('renders as button by default', () => {
    const wrapper = mount(BaseButton, {
      slots: { default: 'Click me' }
    });
    expect(wrapper.find('button').exists()).toBe(true);
    expect(wrapper.text()).toContain('Click me');
  });

  it('applies variant classes', () => {
    const wrapper = mount(BaseButton, {
      props: { variant: 'secondary' }
    });
    // Check for some secondary color class - updated to match current implementation
    expect(wrapper.find('button').classes()).toContain('bg-[#f6c1b1]');
  });

  it('applies size classes', () => {
    const wrapper = mount(BaseButton, {
      props: { size: 'lg' }
    });
    expect(wrapper.find('button').classes()).toContain('px-8');
  });

  it('shows loading spinner when loading', () => {
    const wrapper = mount(BaseButton, {
      props: { loading: true }
    });
    expect(wrapper.find('svg.animate-spin').exists()).toBe(true);
    expect(wrapper.find('button').attributes('disabled')).toBeDefined();
  });

  it('renders other variants', () => {
    const variants = ['ghibli-primary', 'ghibli-secondary', 'danger', 'outline'] as const;
    variants.forEach(variant => {
      const wrapper = mount(BaseButton, {
        props: { variant }
      });
      expect(wrapper.find('button').classes()).toBeDefined();
    });
  });

  it('renders sm size', () => {
    const wrapper = mount(BaseButton, {
      props: { size: 'sm' }
    });
    expect(wrapper.find('button').classes()).toContain('px-4');
  });

  it('uses to prop for router link', () => {
    const wrapper = mount(BaseButton, {
      props: { to: '/test' },
      global: {
        stubs: baseStubs
      }
    });
    
    expect(wrapper.find('a').exists()).toBe(true);
    // RouterLink stub attributes are a bit different, but it should render as <a>
  });

  it('renders as external link when href provided', () => {
    const wrapper = mount(BaseButton, {
      props: { href: 'https://example.com' }
    });
    const link = wrapper.find('a');
    expect(link.exists()).toBe(true);
    expect(link.attributes('target')).toBe('_blank');
  });

  it('shows loading spinner on external link', () => {
    const wrapper = mount(BaseButton, {
      props: { href: 'https://example.com', loading: true }
    });
    expect(wrapper.find('a svg.animate-spin').exists()).toBe(true);
  });

  it('shows loading spinner on router link', () => {
    const wrapper = mount(BaseButton, {
      props: { to: '/test', loading: true },
      global: {
        stubs: baseStubs
      }
    });
    expect(wrapper.find('svg.animate-spin').exists()).toBe(true);
  });

  it('applies block class when block prop is true', () => {
    const wrapper = mount(BaseButton, {
      props: { block: true }
    });
    expect(wrapper.find('button').classes()).toContain('w-full');
  });

  it('disables button when disabled prop is true', () => {
    const wrapper = mount(BaseButton, {
      props: { disabled: true }
    });
    expect(wrapper.find('button').attributes('disabled')).toBeDefined();
  });
});

describe('BaseCard Component', () => {
  it('renders with default props', () => {
    const wrapper = mount(BaseCard, {
      slots: { default: 'Card content' }
    });
    expect(wrapper.find('div').exists()).toBe(true);
    expect(wrapper.text()).toContain('Card content');
  });

  it('applies glass variant classes', () => {
    const wrapper = mount(BaseCard, {
      props: { variant: 'glass' }
    });
    expect(wrapper.find('div').classes()).toContain('backdrop-blur-md');
  });

  it('applies white variant classes', () => {
    const wrapper = mount(BaseCard, {
      props: { variant: 'white' }
    });
    expect(wrapper.find('div').classes()).toContain('bg-white');
  });

  it('applies padding classes', () => {
    const wrapper = mount(BaseCard, {
      props: { padding: 'none' }
    });
    expect(wrapper.find('div').classes()).toContain('p-0');
  });

  it('applies hover classes when hover is true', () => {
    const wrapper = mount(BaseCard, {
      props: { hover: true }
    });
    expect(wrapper.find('div').classes()).toContain('hover:shadow-xl');
  });
});

describe('EmptyState Component', () => {
  it('renders with title and message', () => {
    const wrapper = mount(EmptyState, {
      props: {
        title: 'No Cats Found',
        message: 'Try a different search term.'
      }
    });
    expect(wrapper.text()).toContain('No Cats Found');
    expect(wrapper.text()).toContain('Try a different search term.');
  });

  it('renders action slot', () => {
    const wrapper = mount(EmptyState, {
      slots: {
        action: '<button id="retry">Retry</button>'
      }
    });
    expect(wrapper.find('#retry').exists()).toBe(true);
  });
});

describe('ErrorState Component', () => {
  it('renders error message', () => {
    const wrapper = mount(ErrorState, {
      props: {
        message: 'Something went wrong!'
      }
    });
    expect(wrapper.text()).toContain('Something went wrong!');
  });

  it('emits retry event when button clicked', async () => {
    const wrapper = mount(ErrorState);
    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('retry')).toBeTruthy();
  });
});

describe('GhibliLoader Component', () => {
  it('renders by default', () => {
    const wrapper = mount(GhibliLoader);
    // GhibliLoader uses divs for sprites, not img tags now
    expect(wrapper.find('.animate-\\[gentle-sway_2s_infinite_ease-in-out\\]').exists()).toBe(true);
  });

  it('shows text when provided', () => {
    const wrapper = mount(GhibliLoader, {
      props: { text: 'Loading data...' }
    });
    expect(wrapper.text()).toContain('Loading data...');
  });
});
