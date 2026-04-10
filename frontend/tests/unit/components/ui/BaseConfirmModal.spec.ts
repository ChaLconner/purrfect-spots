import { describe, it, expect, vi, afterEach } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import BaseConfirmModal from '@/components/ui/BaseConfirmModal.vue';

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}));

describe('BaseConfirmModal Component', () => {
  const defaultProps = {
    isOpen: true,
    title: 'Confirm Action',
    message: 'Are you sure you want to do this?',
  };

  let wrapper: VueWrapper;

  afterEach(() => {
    wrapper?.unmount();
    // Clean up any teleported content left on the body
    document.body.innerHTML = '';
  });

  // Instead of stubbing Teleport (which triggers the Vue 3.5 ce=null bug),
  // let it teleport into document.body in JSDOM. We then query document.body
  // for the teleported content directly.
  const mountModal = (props = {}, slots = {}) => {
    wrapper = mount(BaseConfirmModal, {
      props: { ...defaultProps, ...props },
      slots,
      attachTo: document.body,
    });
    return wrapper;
  };

  // Helper: query the teleported DOM (lives in document.body, not wrapper root)
  const body = () => document.body;

  it('renders when isOpen is true', () => {
    mountModal();

    expect(body().querySelector('h3')?.textContent).toBe('Confirm Action');
    expect(body().textContent).toContain('Are you sure you want to do this?');
  });

  it('does not render when isOpen is false', () => {
    mountModal({ isOpen: false });

    expect(body().querySelector('h3')).toBeNull();
  });

  it('emits close event when cancel button is clicked', async () => {
    mountModal();

    const buttons = body().querySelectorAll('button');
    buttons[0]?.click();
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('emits confirm event when confirm button is clicked', async () => {
    mountModal();

    const buttons = body().querySelectorAll('button');
    buttons[1]?.click();
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('confirm')).toBeTruthy();
  });

  it('applies danger variant classes', () => {
    mountModal({ variant: 'danger' });

    expect(body().querySelector('.border-red-500')).not.toBeNull();
    expect(body().querySelector('.bg-red-50')).not.toBeNull();
    expect(body().querySelector('svg.text-red-500')).not.toBeNull();
  });

  it('applies warning variant classes', () => {
    mountModal({ variant: 'warning' });

    expect(body().querySelector('.border-yellow-500')).not.toBeNull();
    expect(body().querySelector('.bg-yellow-50')).not.toBeNull();
    expect(body().querySelector('svg.text-yellow-500')).not.toBeNull();
  });

  it('applies info variant classes', () => {
    mountModal({ variant: 'info' });

    expect(body().querySelector('.border-blue-500')).not.toBeNull();
    expect(body().querySelector('.bg-blue-50')).not.toBeNull();
    expect(body().querySelector('svg.text-blue-500')).not.toBeNull();
  });

  it('shows loading state on confirm button', () => {
    mountModal({ isLoading: true });

    expect(body().querySelector('svg.animate-spin')).not.toBeNull();
    const buttons = body().querySelectorAll('button');
    expect(buttons[0]?.hasAttribute('disabled')).toBe(true);
    expect(buttons[1]?.hasAttribute('disabled')).toBe(true);
  });

  it('uses custom confirm and cancel text', () => {
    mountModal({ confirmText: 'Yes, Delete', cancelText: 'No, Keep' });

    expect(body().textContent).toContain('Yes, Delete');
    expect(body().textContent).toContain('No, Keep');
  });

  it('renders icon slot content', () => {
    mountModal({}, { icon: '<div class="custom-icon"></div>' });

    expect(body().querySelector('.custom-icon')).not.toBeNull();
  });

  it('renders default slot content', () => {
    mountModal({}, { default: '<div class="custom-message">Custom Message</div>' });

    expect(body().querySelector('.custom-message')).not.toBeNull();
  });
});
