import { describe, expect, it, vi, beforeEach } from 'vitest';
import { flushPromises, shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import AdminRoles from '@/views/admin/AdminRoles.vue';
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
    },
  };
});

describe('AdminRoles.vue', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    vi.clearAllMocks();
    pinia = createPinia();
    setActivePinia(pinia);

    const authStore = useAuthStore();
    authStore.user = {
      id: 'admin-1',
      email: 'admin@example.com',
      name: 'Admin',
      role: 'admin',
      permissions: ['roles:read', 'roles:manage'],
    } as any;

    (apiV1.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url === '/admin/roles') {
        return Promise.resolve([{ id: 'moderator', name: 'Moderator', permission_count: 1 }]);
      }
      if (url === '/admin/roles/permissions') {
        return Promise.resolve([
          {
            id: 'permission-1',
            code: 'users:read',
            description: 'Read users',
            group: 'User Management',
          },
        ]);
      }
      return Promise.resolve(['permission-1']);
    });
  });

  it('normalizes permission groups and renders the labeled permission search', async () => {
    const wrapper = shallowMount(AdminRoles, {
      global: {
        plugins: [pinia],
        stubs: {
          AdminPageHeader: true,
          BaseConfirmModal: true,
        },
      },
    });

    await flushPromises();

    const role = wrapper.find('.cursor-pointer');
    expect(role.exists()).toBe(true);
    await role.trigger('click');
    await flushPromises();

    expect(wrapper.find('#admin-permission-search').exists()).toBe(true);
    expect(wrapper.text()).toContain('Users');
    expect(apiV1.get).toHaveBeenCalledWith('/admin/roles/moderator/permissions');

    const viewModel = wrapper.vm as any;
    const permissionGroup = Object.values(viewModel.formattedGroupedPermissions)[0] as any[];
    viewModel.toggleGroup(permissionGroup, false);
    viewModel.toggleGroup(permissionGroup, true);
    viewModel.markDirty();
    viewModel.selectRole({ id: 'moderator', name: 'Moderator', permission_count: 1 });
    await viewModel.executeSelectRole();
    await flushPromises();

    (apiV1.post as ReturnType<typeof vi.fn>).mockResolvedValue({});
    viewModel.markDirty();
    await viewModel.savePermissions();
    viewModel.resetToOriginal();

    expect(apiV1.post).toHaveBeenCalledWith(
      '/admin/roles/moderator/permissions',
      expect.objectContaining({ role_id: 'moderator' })
    );
  });
});
