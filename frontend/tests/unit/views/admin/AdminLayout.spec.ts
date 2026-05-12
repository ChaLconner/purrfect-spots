import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import AdminLayout from '@/views/admin/AdminLayout.vue';
import { useAuthStore } from '@/store/authStore';

const subscribeToReports = vi.fn();
const unsubscribeReports = vi.fn();
const adminStats = {
  pending_reports: 0,
};

vi.mock('@/store/adminStore', () => ({
  useAdminStore: () => ({
    stats: adminStats,
    subscribeToReports,
    unsubscribeReports,
  }),
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}));

describe('AdminLayout.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    adminStats.pending_reports = 0;
  });

  function mountLayout() {
    return shallowMount(AdminLayout, {
      global: {
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
          RouterView: true,
        },
      },
    });
  }

  it('subscribes to report updates for users who can read reports', () => {
    const authStore = useAuthStore();
    authStore.user = {
      id: 'report-reader',
      email: 'reader@example.com',
      name: 'Reader',
      permissions: ['reports:read'],
    } as any;

    mountLayout();

    expect(subscribeToReports).toHaveBeenCalledWith(true);
  });

  it('does not subscribe to report updates for admins without report visibility', () => {
    const authStore = useAuthStore();
    authStore.user = {
      id: 'security-analyst',
      email: 'security@example.com',
      name: 'Security',
      permissions: ['system:stats'],
    } as any;

    mountLayout();

    expect(subscribeToReports).toHaveBeenCalledWith(false);
  });

  it('shows capped pending report badge for report readers', () => {
    const authStore = useAuthStore();
    authStore.user = {
      id: 'report-reader',
      email: 'reader@example.com',
      name: 'Reader',
      permissions: ['reports:read'],
    } as any;
    adminStats.pending_reports = 125;

    const wrapper = mountLayout();

    expect(wrapper.text()).toContain('99+');
  });

  it('shows exact pending report badge below the cap', () => {
    const authStore = useAuthStore();
    authStore.user = {
      id: 'report-reader',
      email: 'reader@example.com',
      name: 'Reader',
      permissions: ['reports:read'],
    } as any;
    adminStats.pending_reports = 7;

    const wrapper = mountLayout();

    expect(wrapper.text()).toContain('7');
  });

  it('toggles and closes the mobile sidebar overlay', async () => {
    const authStore = useAuthStore();
    authStore.user = {
      id: 'admin',
      email: 'admin@example.com',
      name: 'Admin',
      permissions: ['reports:read'],
    } as any;

    const wrapper = mountLayout();

    expect(wrapper.find('.fixed.inset-0').exists()).toBe(false);

    await wrapper.get('button[aria-label="Toggle Menu"]').trigger('click');
    expect(wrapper.find('.fixed.inset-0').exists()).toBe(true);

    await wrapper.get('.fixed.inset-0').trigger('click');
    expect(wrapper.find('.fixed.inset-0').exists()).toBe(false);
  });

  it('unsubscribes from report updates on unmount', () => {
    const authStore = useAuthStore();
    authStore.user = {
      id: 'report-reader',
      email: 'reader@example.com',
      name: 'Reader',
      permissions: ['reports:read'],
    } as any;

    const wrapper = mountLayout();
    wrapper.unmount();

    expect(unsubscribeReports).toHaveBeenCalledOnce();
  });
});
