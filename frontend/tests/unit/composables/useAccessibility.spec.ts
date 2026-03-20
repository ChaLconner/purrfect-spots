import { describe, it, expect, vi, afterEach } from 'vitest';
import { ref, nextTick, defineComponent } from 'vue';
import { mount } from '@vue/test-utils';
import { announce, useFocusTrap, useArrowKeyNavigation, useSkipLink, useModalFocus } from '@/composables/useAccessibility';

describe('useAccessibility composables', () => {
  afterEach(() => {
    document.body.innerHTML = '';
    vi.clearAllMocks();
  });

  describe('announce', () => {
    it('should create and update announcer element', () => {
      // Use requestAnimationFrame mock
      vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => cb(0));
      
      announce('Hello World');
      const announcer = document.getElementById('a11y-announcer');
      expect(announcer).not.toBeNull();
      expect(announcer?.textContent).toBe('Hello World');
      expect(announcer?.getAttribute('aria-live')).toBe('polite');

      announce('Alert!', 'assertive');
      expect(announcer?.textContent).toBe('Alert!');
      expect(announcer?.getAttribute('aria-live')).toBe('assertive');
      
      vi.unstubAllGlobals();
    });
  });

  describe('useFocusTrap', () => {
    it('should trap focus within container', async () => {
      const container = document.createElement('div');
      container.innerHTML = `
        <button id="b1">First</button>
        <button id="b2">Second</button>
      `;
      document.body.appendChild(container);
      
      const b1 = document.getElementById('b1') as HTMLButtonElement;
      const b2 = document.getElementById('b2') as HTMLButtonElement;
      
      // In JSDOM offsetParent is always null unless we mock it
      Object.defineProperty(b1, 'offsetParent', { get: () => document.body });
      Object.defineProperty(b2, 'offsetParent', { get: () => document.body });

      const containerRef = { value: container };
      const { activate, deactivate } = useFocusTrap(containerRef);
      
      activate();
      await nextTick();
      
      // Focus should start at first element
      expect(document.activeElement).toBe(b1);
      
      // Tab from last to first
      b2.focus();
      const tabEvent = new KeyboardEvent('keydown', { key: 'Tab' });
      document.dispatchEvent(tabEvent);
      expect(document.activeElement).toBe(b1);
      
      // Shift+Tab from first to last
      const shiftTabEvent = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true });
      document.dispatchEvent(shiftTabEvent);
      expect(document.activeElement).toBe(b2);
      
      deactivate();
      document.body.removeChild(container);
    });
  });

  describe('useArrowKeyNavigation', () => {
    it('should navigate items with arrow keys', async () => {
        const item1 = document.createElement('button');
        const item2 = document.createElement('button');
        const container = document.createElement('div');
        container.appendChild(item1);
        container.appendChild(item2);
        document.body.appendChild(container);
        
        // JSDOM mock for visibility
        Object.defineProperty(item1, 'offsetParent', { get: () => document.body });
        Object.defineProperty(item2, 'offsetParent', { get: () => document.body });

        const items = ref([item1, item2]);
        const { handleKeyDown } = useArrowKeyNavigation(items);
        
        item1.focus();
        console.log('Active after focus:', (document.activeElement as any).tagName, (document.activeElement as any).id);
        expect(document.activeElement).toBe(item1);
        
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        handleKeyDown(event);
        console.log('Active after handleKeyDown:', (document.activeElement as any).tagName, (document.activeElement as any).id);
        expect(document.activeElement).toBe(item2);
        
        const eventUp = new KeyboardEvent('keydown', { key: 'ArrowUp' });
        handleKeyDown(eventUp);
        expect(document.activeElement).toBe(item1);

        document.body.removeChild(container);
    });

    it('should loop around when loop is true', () => {
      const item1 = document.createElement('button');
      const item2 = document.createElement('button');
      document.body.appendChild(item1);
      document.body.appendChild(item2);
      Object.defineProperty(item1, 'offsetParent', { get: () => document.body });
      Object.defineProperty(item2, 'offsetParent', { get: () => document.body });
      const items = ref([item1, item2]);
      const { handleKeyDown } = useArrowKeyNavigation(items, { loop: true });
      
      item2.focus();
      const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
      handleKeyDown(event);
      expect(document.activeElement).toBe(item1);
    });

    it('should not loop around when loop is false', () => {
      const item1 = document.createElement('button');
      const item2 = document.createElement('button');
      document.body.appendChild(item1);
      document.body.appendChild(item2);
      Object.defineProperty(item1, 'offsetParent', { get: () => document.body });
      Object.defineProperty(item2, 'offsetParent', { get: () => document.body });
      const items = ref([item1, item2]);
      const { handleKeyDown } = useArrowKeyNavigation(items, { loop: false });
      
      item2.focus();
      const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
      handleKeyDown(event);
      expect(document.activeElement).toBe(item2);
    });

    it('should respect orientation', () => {
      const item1 = document.createElement('button');
      const item2 = document.createElement('button');
      document.body.appendChild(item1);
      document.body.appendChild(item2);
      Object.defineProperty(item1, 'offsetParent', { get: () => document.body });
      Object.defineProperty(item2, 'offsetParent', { get: () => document.body });
      const items = ref([item1, item2]);
      const { handleKeyDown } = useArrowKeyNavigation(items, { orientation: 'vertical' });
      
      item1.focus();
      const event = new KeyboardEvent('keydown', { key: 'ArrowRight' });
      handleKeyDown(event);
      expect(document.activeElement).toBe(item1); 
    });

    it('should handle Home and End keys', () => {
      const item1 = document.createElement('button');
      const item2 = document.createElement('button');
      const item3 = document.createElement('button');
      document.body.appendChild(item1);
      document.body.appendChild(item2);
      document.body.appendChild(item3);
      Object.defineProperty(item1, 'offsetParent', { get: () => document.body });
      Object.defineProperty(item2, 'offsetParent', { get: () => document.body });
      Object.defineProperty(item3, 'offsetParent', { get: () => document.body });
      const items = ref([item1, item2, item3]);
      const { handleKeyDown } = useArrowKeyNavigation(items);
      
      item2.focus();
      handleKeyDown(new KeyboardEvent('keydown', { key: 'Home' }));
      expect(document.activeElement).toBe(item1);

      handleKeyDown(new KeyboardEvent('keydown', { key: 'End' }));
      expect(document.activeElement).toBe(item3);
    });
  });

  describe('useSkipLink', () => {
    it('should focus target element', () => {
        const target = document.createElement('div');
        target.id = 'main-content';
        target.tabIndex = -1;
        document.body.appendChild(target);
        target.scrollIntoView = vi.fn();
        
        const { skipToContent } = useSkipLink('main-content');
        skipToContent();
        
        expect(document.activeElement).toBe(target);
        expect(target.scrollIntoView).toHaveBeenCalled();
        
        document.body.removeChild(target);
    });
  });

  describe('useModalFocus', () => {
    it('should activate and deactivate focus trap', async () => {
      const container = document.createElement('div');
      container.innerHTML = '<button id="m1">Modal Btn</button>';
      document.body.appendChild(container);
      
      const isOpen = ref(false);
      const modalRef = ref(container);
      
      const TestComponent = defineComponent({
        setup() {
          return useModalFocus(isOpen, modalRef);
        },
        template: '<div></div>'
      });
      
      const wrapper = mount(TestComponent);
      const { activateFocusTrap, deactivateFocusTrap } = wrapper.vm as any;
      
      const btn = document.getElementById('m1');
      if (btn) Object.defineProperty(btn, 'offsetParent', { get: () => document.body });

      activateFocusTrap();
      await nextTick();
      
      expect(document.activeElement).toBe(btn);
      
      deactivateFocusTrap();
      document.body.removeChild(container);
    });
  });
});
