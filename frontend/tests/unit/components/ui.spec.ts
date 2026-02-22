import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
import BaseButton from '@/components/ui/BaseButton.vue';
import BaseCard from '@/components/ui/BaseCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import ErrorState from '@/components/ui/ErrorState.vue';
import CardSkeleton from '@/components/ui/CardSkeleton.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import { generateResponsiveSources } from '@/utils/imageUtils';

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
  });

  it('uses to prop for router link', () => {
    const wrapper = mount(BaseButton, {
      props: { to: '/test' }
    });
    // When 'to' is provided, the component should render a RouterLink
    // which is stubbed globally as 'true'
    expect(wrapper.props('to')).toBe('/test');
  });

  it('renders as external link when href provided', () => {
    const wrapper = mount(BaseButton, {
      props: { href: 'https://example.com' }
    });
    const link = wrapper.find('a');
    expect(link.exists()).toBe(true);
    expect(link.attributes('target')).toBe('_blank');
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
    expect(wrapper.find('div').exists()).toBe(true);
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

