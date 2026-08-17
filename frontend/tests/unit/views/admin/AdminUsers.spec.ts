import { describe, expect, it, vi, beforeEach } from 'vitest';
import { defineComponent } from 'vue';
import { flushPromises, shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import AdminUsers from '@/views/admin/AdminUsers.vue';
import { apiV1 } from '@/utils/api';
import { useAuthStore } from '@/stores/authStore';

vi.mock('@/utils/api', async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    apiV1: {
      ...(actual.apiV1 as Record<string, unknown>),
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    },
  };
});

const testUser = {
  id: 'user-1',
  name: 'Test User',
  email: 'user@example.com',
  role: 'super_admin',
  created_at: '2026-01-01T00:00:00.000Z',
  banned_at: null,
  bio: null,
  picture: null,
};

describe('AdminUsers.vue', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    vi.clearAllMocks();
    pinia = createPinia();
    setActivePinia(pinia);

    const authStore = useAuthStore();
    authStore.user = {
      id: 'viewer-1',
      email: 'viewer@example.com',
      name: 'Viewer',
      role: 'admin',
      permissions: ['roles:read'],
    } as any;

    (apiV1.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/admin/roles')) {
        return Promise.resolve([{ id: 'admin', name: 'Admin' }]);
      }

      return Promise.resolve({
        data: [testUser],
        total: 1,
      });
    });
  });

  it('loads users and roles, formats normalized roles, and exports CSV data', async () => {
    const wrapper = shallowMount(AdminUsers, {
      global: {
        plugins: [pinia],
        stubs: {
          AdminPageHeader: defineComponent({
            template: '<div><slot name="actions" /></div>',
          }),
          ActionModal: true,
          AdminPagination: true,
          OptimizedImage: true,
          TableSkeleton: true,
        },
      },
    });

    await flushPromises();

    expect(apiV1.get).toHaveBeenCalledWith(expect.stringContaining('/admin/users'), expect.anything());
    expect(apiV1.get).toHaveBeenCalledWith('/admin/roles');
    expect(wrapper.text()).toContain('Super admin');

    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    await wrapper.find('button').trigger('click');
    await flushPromises();
    clickSpy.mockRestore();

    expect(apiV1.get).toHaveBeenCalledTimes(3);

    const viewModel = wrapper.vm as any;
    viewModel.handleSort('created_at');
    viewModel.handleSort('created_at');
    viewModel.handleSort('name');

    (apiV1.post as ReturnType<typeof vi.fn>).mockResolvedValue({});
    (apiV1.put as ReturnType<typeof vi.fn>).mockResolvedValue({});
    (apiV1.patch as ReturnType<typeof vi.fn>).mockResolvedValue({ bio: 'Updated bio' });

    viewModel.openBanModal(testUser);
    await viewModel.processBan();
    viewModel.confirmDelete(testUser);
    viewModel.processConfirm();
    viewModel.confirmUnban(testUser);
    viewModel.processConfirm();
    viewModel.handleRoleChange(testUser, 'admin');
    viewModel.processConfirm();
    await flushPromises();
    viewModel.openProfileModal(testUser);
    viewModel.profileForm.name = 'Updated User';
    await viewModel.saveProfile();
    viewModel.closeBanModal();
    viewModel.closeConfirmModal();

    expect(apiV1.post).toHaveBeenCalledWith('/admin/users/user-1/ban', expect.anything());
    expect(apiV1.put).toHaveBeenCalledWith('/admin/users/user-1/role', { role_id: 'admin' });
    expect(apiV1.patch).toHaveBeenCalledWith(
      '/admin/users/user-1/profile',
      expect.objectContaining({ name: 'Updated User' })
    );
  });
});
