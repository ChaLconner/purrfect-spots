import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
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
    // Component renders a root div with Tailwind classes (no .skeleton-loader class)
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

describe('OptimizedImage Logic', () => {
  it('should generate correct srcset for external URLs', () => {
    const sources = generateResponsiveSources('https://example.com/image.jpg');
    const srcset = sources.map(s => s.srcSet).join(', ');
    
    // widths: [320, 640, 768, 1024, 1280, 1536] (from imageUtils.ts)
    // Note: In test env, CDN is disabled so params are not added
    expect(srcset).toContain('https://example.com/image.jpg 320w');
    expect(srcset).toContain('https://example.com/image.jpg 1536w');
  });
});

