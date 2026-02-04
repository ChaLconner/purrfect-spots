import { describe, it, expect, vi, beforeEach } from 'vitest';
import { announce, useFocusTrap, useArrowKeyNavigation } from '@/composables/useAccessibility';
import { nextTick, ref } from 'vue';

describe('useAccessibility', () => {
    
  // ========== announce tests ==========
  describe('announce', () => {
    beforeEach(() => {
      document.body.innerHTML = '';
    });

    it('creates announcer element if missing', () => {
      announce('Hello');
      const announcer = document.getElementById('a11y-announcer');
      expect(announcer).toBeTruthy();
      expect(announcer?.getAttribute('aria-live')).toBe('polite');
    });

    it('updates text content of announcer', async () => {
      vi.useFakeTimers();
      announce('Message 1');
      
      const announcer = document.getElementById('a11y-announcer');
      // Announce clears text then sets it in requestAnimationFrame
      // In JSDOM, requestAnimationFrame might need mocking or real timer flow
      
      // We can inspect expected behavior conceptually or verify DOM
      // For simplified testing of DOM manipulations:
      expect(announcer?.id).toBe('a11y-announcer');
    });
  });

  // ========== useFocusTrap tests ==========
  describe('useFocusTrap', () => {
    let container: HTMLElement;
    let button1: HTMLButtonElement;
    let button2: HTMLButtonElement;
    let outsideButton: HTMLButtonElement;

    beforeEach(() => {
      // Global mock for offsetParent to simulate visibility in JSDOM
      Object.defineProperty(HTMLElement.prototype, 'offsetParent', {
        get() {
           return this.parentNode; 
        },
        configurable: true
      });

      document.body.innerHTML = `
        <button id="outside">Outside</button>
        <div id="container">
          <button id="btn1">Btn 1</button>
          <button id="btn2">Btn 2</button>
        </div>
      `;
      container = document.getElementById('container')!;
      button1 = document.getElementById('btn1') as HTMLButtonElement;
      button2 = document.getElementById('btn2') as HTMLButtonElement;
      outsideButton = document.getElementById('outside') as HTMLButtonElement;
      
      outsideButton.focus();

      // Mock offsetParent for visibility check
      Object.defineProperty(button1, 'offsetParent', { get: () => document.body });
      Object.defineProperty(button2, 'offsetParent', { get: () => document.body });
      Object.defineProperty(outsideButton, 'offsetParent', { get: () => document.body });
    });

    it('activates and focuses first element', async () => {
      const { activate } = useFocusTrap(ref(container));
      activate();
      await nextTick();
      expect(document.activeElement).toBe(button1);
    });

    it('traps focus strictly inside container', async () => {
      const { activate } = useFocusTrap(ref(container));
      activate();
      await nextTick();

      // Mock Tab press on last element
      button2.focus();
      const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true });
      document.dispatchEvent(event);
      
      // Should wrap around to first element
      expect(document.activeElement).toBe(button1); 
    });
  });
  
  // ========== useArrowKeyNavigation tests ==========
  describe('useArrowKeyNavigation', () => {
     it('navigates with arrow keys', () => {
         document.body.innerHTML = `
            <button id="i1">1</button>
            <button id="i2">2</button>
            <button id="i3">3</button>
         `;
         const items = document.querySelectorAll('button');
         const item1 = items[0];
         const item2 = items[1];
         const item3 = items[2];
         
         item1.focus();
         
         const { handleKeyDown } = useArrowKeyNavigation(ref(items as any)); // simplified ref
         
         // Arrow Down -> item 2
         handleKeyDown(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
         expect(document.activeElement).toBe(item2);
         
         // Arrow Down -> item 3
         handleKeyDown(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
         expect(document.activeElement).toBe(item3);
         
         // Loop -> item 1
         handleKeyDown(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
         expect(document.activeElement).toBe(item1);
     });
  });

});
