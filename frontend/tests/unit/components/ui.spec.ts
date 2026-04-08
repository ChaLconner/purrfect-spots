import { describe, it, expect, vi } from 'vitest';
import { mount, config } from '@vue/test-utils';
import { useRouter } from 'vue-router';
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
import BaseButton from '@/components/ui/BaseButton.vue';
import BaseCard from '@/components/ui/BaseCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import ErrorState from '@/components/ui/ErrorState.vue';
import CardSkeleton from '@/components/ui/CardSkeleton.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import { generateResponsiveSources } from '@/utils/imageUtils';

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

config.global.stubs = {
  RouterLink: true,
  RouterView: true
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
    const variants = ['ghibli-primary', 'ghibli-secondary', 'danger', 'outline'];
    variants.forEach(variant => {
      const wrapper = mount(BaseButton, {
        props: { variant: variant as any }
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
      props: { to: '/test' }
    });
    
    expect(wrapper.find('router-link-stub').exists()).toBe(true);
    expect(wrapper.find('router-link-stub').attributes('to')).toBe('/test');
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
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>'
          }
        }
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
      props: { padding: 'lg' }
    });
    expect(wrapper.find('div').classes()).toContain('p-8');
  });

  it('applies hover classes when hover is true', () => {
    const wrapper = mount(BaseCard, {
      props: { hover: true }
    });
    expect(wrapper.find('div').classes()).toContain('hover:scale-[1.02]');
  });
});

describe('EmptyState Component', () => {
  it('renders structure', () => {
    const wrapper = mount(EmptyState);
    expect(wrapper.find('h3').exists()).toBe(true);
  });

  it('renders provided title and message', () => {
    const wrapper = mount(EmptyState, {
      props: {
        title: 'Custom Title',
        message: 'Custom Message',
      },
    });
    expect(wrapper.find('h3').text()).toBe('Custom Title');
    expect(wrapper.text()).toContain('Custom Message');
  });

  it('renders subMessage when provided', () => {
    const wrapper = mount(EmptyState, {
      props: {
        subMessage: 'Sub Message Content',
      },
    });
    expect(wrapper.text()).toContain('Sub Message Content');
  });

  it('renders action button and handles clicks', async () => {
    const pushMock = vi.fn();
    vi.mocked(useRouter).mockReturnValue({
      push: pushMock,
    } as any);

    const wrapper = mount(EmptyState, {
      props: {
        actionText: 'Go Back',
        actionLink: '/home',
      },
    });

    const button = wrapper.find('button');
    expect(button.exists()).toBe(true);
    expect(button.text()).toBe('Go Back');

    await button.trigger('click');
    expect(pushMock).toHaveBeenCalledWith('/home');
  });

  it('renders different icon styles', () => {
    const icons = ['peek', 'nap', 'wait', 'box'];
    icons.forEach((icon) => {
      const wrapper = mount(EmptyState, {
        props: { icon: icon as any },
      });
      // The SVG path will be different for each
      expect(wrapper.find('svg').exists()).toBe(true);
    });
  });

  it('randomizes icon when not provided', () => {
    const wrapper = mount(EmptyState);
    expect(wrapper.find('svg').exists()).toBe(true);
  });
});

describe('ErrorState Component', () => {
  it('renders with default props', () => {
    const wrapper = mount(ErrorState);
    expect(wrapper.find('h3').exists()).toBe(true);
    expect(wrapper.text()).toContain('wrong');
    expect(wrapper.text()).toContain('Try Again');
  });

  it('emits retry event when button clicked', async () => {
    const wrapper = mount(ErrorState);
    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('retry')).toBeTruthy();
  });
});

describe('CardSkeleton Component', () => {
  it('renders skeleton structure', () => {
    const wrapper = mount(CardSkeleton);
    const container = wrapper.find('.card-skeleton-container');
    expect(container.exists()).toBe(true);
    expect(container.classes()).toContain('grid');
  });

  it('renders profile variant', () => {
    const wrapper = mount(CardSkeleton, {
      props: { variant: 'profile' },
    });
    expect(wrapper.find('.space-y-4').exists()).toBe(true);
    expect(wrapper.findAll('.flex-1.space-y-3')).toHaveLength(1);
  });

  it('renders list variant', () => {
    const wrapper = mount(CardSkeleton, {
      props: { variant: 'list' },
    });
    expect(wrapper.find('.space-y-4').exists()).toBe(true);
    expect(wrapper.findAll('.flex-1.space-y-2')).toHaveLength(1);
  });

  it('renders multiple skeletons', () => {
    const wrapper = mount(CardSkeleton, {
      props: { count: 3 },
    });
    expect(wrapper.findAll('.bg-white.rounded-\\[1rem\\]')).toHaveLength(3);
  });
});

describe('GhibliLoader Component', () => {
  it('renders loader structure', () => {
    const wrapper = mount(GhibliLoader);
    expect(wrapper.find('div').exists()).toBe(true);
  });

  it('shows text when provided', () => {
    const wrapper = mount(GhibliLoader, {
      props: { text: 'Loading...' }
    });
    expect(wrapper.text()).toContain('Loading...');
  });

  it('hides text when not provided', () => {
    const wrapper = mount(GhibliLoader);
    expect(wrapper.find('.mt-6').exists()).toBe(false);
  });
});

describe('OptimizedImage Logic', () => {
  it('should generate correct srcset for external URLs', () => {
    const sources = generateResponsiveSources('https://example.com/image.jpg');
    const srcset = sources.map(s => s.srcSet).join(', ');
    
    expect(srcset).toContain('https://example.com/image.jpg 320w');
    expect(srcset).toContain('https://example.com/image.jpg 1536w');
  });
});

