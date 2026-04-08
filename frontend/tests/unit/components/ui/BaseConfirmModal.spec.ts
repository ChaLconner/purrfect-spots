import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
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

  it('renders when isOpen is true', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: defaultProps,
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.find('h3').text()).toBe('Confirm Action');
    expect(wrapper.text()).toContain('Are you sure you want to do this?');
  });

  it('does not render when isOpen is false', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: { ...defaultProps, isOpen: false },
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.find('h3').exists()).toBe(false);
  });

  it('emits close event when cancel button is clicked', async () => {
    const wrapper = mount(BaseConfirmModal, {
      props: defaultProps,
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    await wrapper.find('button').trigger('click'); // First button is cancel
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('emits confirm event when confirm button is clicked', async () => {
    const wrapper = mount(BaseConfirmModal, {
      props: defaultProps,
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    const buttons = wrapper.findAll('button');
    await buttons[1].trigger('click'); // Second button is confirm
    expect(wrapper.emitted('confirm')).toBeTruthy();
  });

  it('applies danger variant classes', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: { ...defaultProps, variant: 'danger' },
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.find('.border-red-500').exists()).toBe(true);
    expect(wrapper.find('.bg-red-50').exists()).toBe(true);
    expect(wrapper.find('svg.text-red-500').exists()).toBe(true);
  });

  it('applies warning variant classes', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: { ...defaultProps, variant: 'warning' },
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.find('.border-yellow-500').exists()).toBe(true);
    expect(wrapper.find('.bg-yellow-50').exists()).toBe(true);
    expect(wrapper.find('svg.text-yellow-500').exists()).toBe(true);
  });

  it('applies info variant classes', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: { ...defaultProps, variant: 'info' },
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.find('.border-blue-500').exists()).toBe(true);
    expect(wrapper.find('.bg-blue-50').exists()).toBe(true);
    expect(wrapper.find('svg.text-blue-500').exists()).toBe(true);
  });

  it('shows loading state on confirm button', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: { ...defaultProps, isLoading: true },
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.find('svg.animate-spin').exists()).toBe(true);
    const buttons = wrapper.findAll('button');
    expect(buttons[0].attributes('disabled')).toBeDefined();
    expect(buttons[1].attributes('disabled')).toBeDefined();
  });

  it('uses custom confirm and cancel text', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: {
        ...defaultProps,
        confirmText: 'Yes, Delete',
        cancelText: 'No, Keep',
      },
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.text()).toContain('Yes, Delete');
    expect(wrapper.text()).toContain('No, Keep');
  });

  it('renders icon slot content', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: defaultProps,
      slots: {
        icon: '<div class="custom-icon"></div>',
      },
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.find('.custom-icon').exists()).toBe(true);
  });

  it('renders default slot content', () => {
    const wrapper = mount(BaseConfirmModal, {
      props: defaultProps,
      slots: {
        default: '<div class="custom-message">Custom Message</div>',
      },
      global: {
        stubs: {
          Teleport: true,
        },
      },
    });

    expect(wrapper.find('.custom-message').exists()).toBe(true);
  });
});
