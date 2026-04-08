import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useModalFocus } from '@/composables/useModalFocus';
import { ref, defineComponent, h } from 'vue';
import { mount } from '@vue/test-utils';

describe('useModalFocus', () => {
  let container: HTMLElement;
  let button1: HTMLButtonElement;
  let button2: HTMLButtonElement;

  beforeEach(() => {
    container = document.createElement('div');
    container.tabIndex = -1;
    button1 = document.createElement('button');
    button2 = document.createElement('button');
    container.appendChild(button1);
    container.appendChild(button2);
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
    document.body.style.overflow = '';
  });

  it('traps focus forward when Tab is pressed', () => {
    const modalRef = ref(container);
    const onClose = vi.fn();
    const { trapFocus } = useModalFocus(modalRef, { onClose });

    button2.focus();
    expect(document.activeElement).toBe(button2);

    const event = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: false });
    const spy = vi.spyOn(event, 'preventDefault');

    trapFocus(event);

    expect(document.activeElement).toBe(button1);
    expect(spy).toHaveBeenCalled();
  });

  it('traps focus backward when Shift+Tab is pressed', () => {
    const modalRef = ref(container);
    const onClose = vi.fn();
    const { trapFocus } = useModalFocus(modalRef, { onClose });

    button1.focus();
    expect(document.activeElement).toBe(button1);

    const event = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true });
    const spy = vi.spyOn(event, 'preventDefault');

    trapFocus(event);

    expect(document.activeElement).toBe(button2);
    expect(spy).toHaveBeenCalled();
  });

  it('calls onClose when Escape is pressed', () => {
    const modalRef = ref(container);
    const onClose = vi.fn();
    const { handleKeydown } = useModalFocus(modalRef, { onClose });

    const event = new KeyboardEvent('keydown', { key: 'Escape' });
    handleKeydown(event);

    expect(onClose).toHaveBeenCalled();
  });

  it('calls trapFocus when Tab is pressed in handleKeydown', () => {
    const modalRef = ref(container);
    const onClose = vi.fn();
    const { handleKeydown } = useModalFocus(modalRef, { onClose });

    button2.focus();
    const event = new KeyboardEvent('keydown', { key: 'Tab' });
    const spy = vi.spyOn(event, 'preventDefault');

    handleKeydown(event);

    expect(document.activeElement).toBe(button1);
    expect(spy).toHaveBeenCalled();
  });

  it('locks scroll on mounted and restores on unmounted', async () => {
    const TestComponent = defineComponent({
      setup() {
        useModalFocus(ref(container), { onClose: () => {} });
        return () => h('div');
      }
    });

    const wrapper = mount(TestComponent);
    expect(document.body.style.overflow).toBe('hidden');

    wrapper.unmount();
    expect(document.body.style.overflow).toBe('');
  });

  it('does not lock scroll if lockScroll is false', () => {
    const TestComponent = defineComponent({
      setup() {
        useModalFocus(ref(container), { onClose: () => {}, lockScroll: false });
        return () => h('div');
      }
    });

    mount(TestComponent);
    expect(document.body.style.overflow).not.toBe('hidden');
  });

  it('handles empty focusable elements', () => {
    const emptyContainer = document.createElement('div');
    const modalRef = ref(emptyContainer);
    const { trapFocus } = useModalFocus(modalRef, { onClose: () => {} });

    const event = new KeyboardEvent('keydown', { key: 'Tab' });
    trapFocus(event);
    // Should not throw
  });

  it('handles null modalContainer', () => {
    const modalRef = ref(null);
    const { trapFocus } = useModalFocus(modalRef, { onClose: () => {} });

    const event = new KeyboardEvent('keydown', { key: 'Tab' });
    trapFocus(event);
    // Should not throw
  });
});
