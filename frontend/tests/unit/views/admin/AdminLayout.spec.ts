import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import AdminLayout from '@/views/admin/AdminLayout.vue';
import { useAuthStore } from '@/store/authStore';

const subscribeToReports = vi.fn();
const unsubscribeReports = vi.fn();

vi.mock('@/store/adminStore', () => ({
  useAdminStore: () => ({
    stats: {
      pending_reports: 0,
    },
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
  });

  it('subscribes to report updates for users who can read reports', () => {
    const authStore = useAuthStore();
    authStore.user = {
      id: 'report-reader',
      email: 'reader@example.com',
      name: 'Reader',
      permissions: ['reports:read'],
    } as any;

    shallowMount(AdminLayout, {
      global: {
        stubs: {
          RouterLink: true,
          RouterView: true,
        },
      },
    });

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

    shallowMount(AdminLayout, {
      global: {
        stubs: {
          RouterLink: true,
          RouterView: true,
        },
      },
    });

    expect(subscribeToReports).toHaveBeenCalledWith(false);
  });
});
