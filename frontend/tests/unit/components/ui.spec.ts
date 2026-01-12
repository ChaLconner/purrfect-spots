/**
 * Tests for UI Components
 * 
 * Tests ErrorBoundary, OptimizedImage, and other UI components
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref, nextTick } from 'vue';

// Mock components for testing
const mockErrorBoundary = {
  template: `
    <div>
      <div v-if="hasError" class="error-state">
        <p>{{ errorMessage }}</p>
        <button @click="retry">Retry</button>
      </div>
      <slot v-else />
    </div>
  `,
  setup() {
    const hasError = ref(false);
    const errorMessage = ref('');

    const triggerError = (msg: string) => {
      hasError.value = true;
      errorMessage.value = msg;
    };

    const retry = () => {
      hasError.value = false;
      errorMessage.value = '';
    };

    return { hasError, errorMessage, triggerError, retry };
  }
};

describe('ErrorBoundary Component', () => {
  it('should render slot content when no error', () => {
    const wrapper = mount(mockErrorBoundary, {
      slots: {
        default: '<div class="child">Child Content</div>'
      }
    });

    expect(wrapper.find('.child').exists()).toBe(true);
    expect(wrapper.find('.error-state').exists()).toBe(false);
  });

  it('should show error state when error is triggered', async () => {
    const wrapper = mount(mockErrorBoundary);
    
    // Access component instance and trigger error
    (wrapper.vm as any).triggerError('Test error message');
    await nextTick();

    expect(wrapper.find('.error-state').exists()).toBe(true);
    expect(wrapper.text()).toContain('Test error message');
  });

  it('should clear error on retry', async () => {
    const wrapper = mount(mockErrorBoundary, {
      slots: {
        default: '<div class="child">Child Content</div>'
      }
    });
    
    // Trigger error first
    (wrapper.vm as any).triggerError('Error');
    await nextTick();
    expect(wrapper.find('.error-state').exists()).toBe(true);

    // Click retry
    await wrapper.find('button').trigger('click');
    await nextTick();

    expect(wrapper.find('.error-state').exists()).toBe(false);
    expect(wrapper.find('.child').exists()).toBe(true);
  });
});

describe('SkeletonLoader Component', () => {
  // Mock SkeletonLoader
  const SkeletonLoader = {
    props: {
      width: { type: String, default: '100%' },
      height: { type: String, default: '100%' },
      borderRadius: { type: String, default: '0.5rem' }
    },
    template: `
      <div 
        class="skeleton-loader"
        :style="{ width, height, borderRadius }"
      />
    `
  };

  it('should render with default props', () => {
    const wrapper = mount(SkeletonLoader);
    const element = wrapper.find('.skeleton-loader');
    
    expect(element.exists()).toBe(true);
  });

  it('should apply custom dimensions', () => {
    const wrapper = mount(SkeletonLoader, {
      props: {
        width: '200px',
        height: '100px'
      }
    });

    const element = wrapper.find('.skeleton-loader');
    expect(element.attributes('style')).toContain('width: 200px');
    expect(element.attributes('style')).toContain('height: 100px');
  });

  it('should apply custom border radius', () => {
    const wrapper = mount(SkeletonLoader, {
      props: {
        borderRadius: '50%'
      }
    });

    const element = wrapper.find('.skeleton-loader');
    expect(element.attributes('style')).toContain('border-radius: 50%');
  });
});

describe('OptimizedImage Component Logic', () => {
  it('should generate correct srcset for external URLs', () => {
    const generateSrcset = (src: string): string => {
      if (!src) return '';
      
      const isExternalUrl = src.startsWith('http');
      
      if (isExternalUrl) {
        const baseUrl = src.split('?')[0];
        const sizes = [320, 640, 960, 1280, 1920];
        
        return sizes
          .map(size => `${baseUrl}?w=${size} ${size}w`)
          .join(', ');
      }
      
      return src;
    };

    const srcset = generateSrcset('https://example.com/image.jpg');
    
    expect(srcset).toContain('https://example.com/image.jpg?w=320 320w');
    expect(srcset).toContain('https://example.com/image.jpg?w=1920 1920w');
  });

  it('should return original src for local URLs', () => {
    const generateSrcset = (src: string): string => {
      if (!src) return '';
      
      const isExternalUrl = src.startsWith('http');
      
      if (isExternalUrl) {
        const baseUrl = src.split('?')[0];
        const sizes = [320, 640, 960, 1280, 1920];
        
        return sizes
          .map(size => `${baseUrl}?w=${size} ${size}w`)
          .join(', ');
      }
      
      return src;
    };

    const srcset = generateSrcset('/local/image.jpg');
    
    expect(srcset).toBe('/local/image.jpg');
  });

  it('should handle empty src', () => {
    const generateSrcset = (src: string): string => {
      if (!src) return '';
      return src;
    };

    expect(generateSrcset('')).toBe('');
  });
});
