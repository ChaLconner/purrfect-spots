<template>
  <div class="bg-white rounded-2xl shadow-sm border border-sand-100 overflow-hidden">
    <!-- Existing code... -->
    <div
      class="p-6 border-b border-sand-100 flex flex-col sm:flex-row justify-between items-center gap-4"
    >
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-bold text-brown-900">Users</h2>
        <button
          class="px-3 py-1.5 text-sm font-medium text-brown-600 bg-sand-50 border border-sand-200 rounded-lg hover:bg-sand-100 transition-colors flex items-center gap-2"
          @click="exportUsers"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export CSV
        </button>
      </div>
      <div class="relative max-w-xs w-full">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search users..."
          class="w-full pl-10 pr-4 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 transition-colors"
          @input="handleSearch"
        />
        <div class="absolute left-3 top-1/2 -translate-y-1/2 text-brown-400">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-sand-200">
        <thead class="bg-sand-50">
          <tr>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider cursor-pointer hover:text-brown-700 group select-none"
              @click="handleSort('name')"
            >
              <div class="flex items-center gap-1">
                User
                <span v-if="sortBy === 'name'" class="text-terracotta-500">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
                <span v-else class="opacity-0 group-hover:opacity-50 transition-opacity">↕</span>
              </div>
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              Role
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider cursor-pointer hover:text-brown-700 group select-none"
              @click="handleSort('created_at')"
            >
              <div class="flex items-center gap-1">
                Joined
                <span v-if="sortBy === 'created_at'" class="text-terracotta-500">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
                <span v-else class="opacity-0 group-hover:opacity-50 transition-opacity">↕</span>
              </div>
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-right text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-sand-200">
          <tr v-for="user in users" :key="user.id" class="hover:bg-sand-50 transition-colors">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <div class="h-10 w-10 flex-shrink-0">
                  <img
                    class="h-10 w-10 rounded-full object-cover"
                    :src="
                      user.picture ||
                      `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=random`
                    "
                    :alt="user.name"
                  />
                </div>
                <div class="ml-4">
                  <div class="text-sm font-medium text-brown-900">{{ user.name }}</div>
                  <div class="text-sm text-brown-500">{{ user.email }}</div>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div v-if="canEditRole" class="relative inline-block w-32">
                <select
                  :value="user.role?.toLowerCase()"
                  :disabled="updatingUserIds.has(user.id)"
                  class="block w-full pl-3 pr-10 py-1.5 text-xs font-semibold border-sand-200 rounded-lg bg-sand-50 focus:ring-terracotta-500 focus:border-terracotta-500 appearance-none cursor-pointer transition-all duration-200"
                  :class="[
                    isUserAdmin(user.role)
                      ? 'text-terracotta-800 bg-terracotta-50 border-terracotta-100'
                      : 'text-green-800 bg-green-50 border-green-100',
                  ]"
                  @change="(e) => handleRoleChange(user, (e.target as HTMLSelectElement).value)"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
                <div
                  class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-brown-400"
                >
                  <svg
                    v-if="!updatingUserIds.has(user.id)"
                    class="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                  <div
                    v-else
                    class="w-3 h-3 border-2 border-terracotta-600 border-t-transparent rounded-full animate-spin"
                  ></div>
                </div>
              </div>
              <span
                v-else
                class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full capitalize"
                :class="
                  isUserAdmin(user.role)
                    ? 'bg-terracotta-100 text-terracotta-800'
                    : 'bg-green-100 text-green-800'
                "
              >
                {{ formatRoleName(user.role) }}
              </span>
              <span
                v-if="user.banned_at"
                class="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-800 text-white"
              >
                BANNED
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-brown-500">
              {{ user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A' }}
            </td>
            <td
              class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex gap-2 justify-end"
            >
              <button
                v-if="canEditProfile"
                class="text-brown-600 hover:text-brown-900 font-medium transition-colors"
                @click="openProfileModal(user)"
              >
                Profile
              </button>

              <!-- Ban/Unban -->
              <button
                v-if="canBanUser(user) && !user.banned_at"
                class="text-orange-600 hover:text-orange-900 font-medium transition-colors disabled:opacity-50"
                @click="openBanModal(user)"
              >
                Ban
              </button>
              <button
                v-if="canBanUser(user) && user.banned_at"
                class="text-green-600 hover:text-green-900 font-medium transition-colors disabled:opacity-50"
                @click="confirmUnban(user)"
              >
                Unban
              </button>

              <!-- Delete -->
              <button
                v-if="canDeleteUser(user)"
                class="text-red-600 hover:text-red-900 font-medium transition-colors disabled:opacity-50"
                @click="confirmDelete(user)"
              >
                Delete
              </button>
            </td>
          </tr>
          <tr v-if="users.length === 0 && !isLoading">
            <td colspan="4" class="px-6 py-12 text-center text-brown-500">No users found.</td>
          </tr>
          <TableSkeleton v-if="isLoading" :columns="4" :avatar-column="1" />
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="users.length > 0"
      class="px-6 py-4 border-t border-sand-200 flex items-center justify-between"
    >
      <button
        :disabled="page === 1"
        class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="page > 1 && loadUsers(page - 1)"
      >
        Previous
      </button>
      <span class="text-sm text-brown-600">Page {{ page }}</span>
      <button
        :disabled="users.length < limit || page * limit >= totalUsers"
        class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="loadUsers(page + 1)"
      >
        Next
      </button>
    </div>

    <!-- Profile Edit Modal -->
    <div
      v-if="editingProfileUser"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    >
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <h3 class="text-lg font-bold text-brown-900 mb-4">
          Edit Profile: {{ editingProfileUser.name }}
        </h3>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-brown-700 mb-1">Full Name</label>
            <input
              v-model="profileForm.name"
              type="text"
              class="w-full border-sand-300 rounded-lg shadow-sm focus:border-terracotta-500 focus:ring-terracotta-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-brown-700 mb-1">Bio</label>
            <textarea
              v-model="profileForm.bio"
              rows="3"
              class="w-full border-sand-300 rounded-lg shadow-sm focus:border-terracotta-500 focus:ring-terracotta-500"
            ></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium text-brown-700 mb-1">Picture URL</label>
            <input
              v-model="profileForm.picture"
              type="text"
              class="w-full border-sand-300 rounded-lg shadow-sm focus:border-terracotta-500 focus:ring-terracotta-500"
              placeholder="https://..."
            />
            <p class="mt-1 text-xs text-brown-400">Clear to revert to default avatar.</p>
          </div>
        </div>

        <div class="flex justify-end gap-3 mt-6">
          <button
            class="px-4 py-2 border border-sand-300 rounded-lg text-brown-600 hover:bg-sand-50"
            @click="editingProfileUser = null"
          >
            Cancel
          </button>
          <button
            :disabled="isSavingProfile"
            class="px-4 py-2 bg-terracotta-600 text-white rounded-lg hover:bg-terracotta-700 disabled:opacity-50"
            @click="saveProfile"
          >
            {{ isSavingProfile ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>
    <!-- Ban User Modal -->
    <div
      v-if="banModal.isOpen"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    >
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <h3 class="text-lg font-bold text-brown-900 mb-4">Ban User: {{ banModal.user?.name }}</h3>
        <p class="text-sm text-brown-600 mb-4">Please provide a reason for banning this user.</p>
        <div class="mb-6">
          <label class="block text-sm font-medium text-brown-700 mb-2">Reason</label>
          <input
            v-model="banModal.reason"
            type="text"
            class="w-full border-sand-300 rounded-lg shadow-sm focus:border-terracotta-500 focus:ring-terracotta-500"
            placeholder="Violation of Terms of Service"
          />
        </div>
        <div class="flex justify-end gap-3">
          <button
            class="px-4 py-2 border border-sand-300 rounded-lg text-brown-600 hover:bg-sand-50"
            @click="closeBanModal"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            @click="processBan"
          >
            Ban User
          </button>
        </div>
      </div>
    </div>

    <!-- Confirmation Modal -->
    <div
      v-if="confirmModal.isOpen"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    >
      <div class="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 text-center">
        <h3 class="text-lg font-bold text-brown-900 mb-2">{{ confirmModal.title }}</h3>
        <p class="text-brown-600 mb-6">{{ confirmModal.message }}</p>
        <div class="flex justify-center gap-3">
          <button
            class="px-4 py-2 border border-sand-300 rounded-lg text-brown-600 hover:bg-sand-50"
            @click="closeConfirmModal"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 rounded-lg text-white"
            :class="
              confirmModal.isDestructive
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-green-600 hover:bg-green-700'
            "
            @click="processConfirm"
          >
            {{ confirmModal.confirmText }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { apiV1 } from '@/utils/api';
import type { User } from '@/types/auth';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/components/toast/use-toast';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';

const { toast } = useToast();

const authStore = useAuthStore();
const users = ref<User[]>([]);
const searchQuery = ref('');
const page = ref(1);
const limit = 20;
const isLoading = ref(false);
const sortBy = ref('created_at');
const sortOrder = ref('desc');
const totalUsers = ref(0);

const handleSort = (field: string): void => {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = field;
    sortOrder.value = 'desc';
  }
  loadUsers(1);
};

// Modals State
const banModal = reactive({
  isOpen: false,
  user: null as User | null,
  reason: 'Violation of Terms of Service',
});

const confirmModal = reactive({
  isOpen: false,
  title: '',
  message: '',
  confirmText: 'Confirm',
  isDestructive: false,
  onConfirm: () => {},
});

const formatRoleName = (role: string | undefined): string => {
  if (!role) return 'User';
  // Capitalize first letter and handle 'admin' vs 'super_admin' display
  const name = role.toLowerCase().replace(/_/g, ' ');
  return name.charAt(0).toUpperCase() + name.slice(1);
};

const isUserAdmin = (role: string | undefined): boolean => {
  if (!role) return false;
  return role.toLowerCase() === 'admin';
};

const loadUsers = async (newPage: number = 1): Promise<void> => {
  isLoading.value = true;
  try {
    const offset = (newPage - 1) * limit;
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
      sort: sortBy.value,
      order: sortOrder.value,
    });
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }

    const response = await apiV1.get<{ data: User[]; total: number }>(
      `/admin/users?${params.toString()}`
    );
    users.value = response.data;
    totalUsers.value = response.total;
    page.value = newPage;
  } catch (e) {
    console.error('Failed to load users', e);
  } finally {
    isLoading.value = false;
  }
};

const searchTimeoutId = ref<number | null>(null);

const handleSearch = (): void => {
  if (searchTimeoutId.value) {
    clearTimeout(searchTimeoutId.value);
  }

  // Debounce search for 300ms
  searchTimeoutId.value = window.setTimeout(() => {
    loadUsers(1);
  }, 300);
};

const exportUsers = async (): Promise<void> => {
  try {
    // Fetch a larger set for export (e.g., 1000)
    // Ideally backend should support streaming or specific export endpoint for massive data
    const response = await apiV1.get<{ data: User[]; total: number }>('/admin/users?limit=1000');
    const data = response.data;

    if (!data || data.length === 0) {
      toast({ description: 'No users to export', variant: 'default' });
      return;
    }

    // CSV Header
    const headers = ['ID', 'Name', 'Email', 'Role', 'Joined At', 'Banned At'];
    const csvContent = [
      headers.join(','),
      ...data.map((user) =>
        [
          user.id,
          `"${(user.name || '').replace(/"/g, '""')}"`,
          `"${(user.email || '').replace(/"/g, '""')}"`,
          user.role,
          user.created_at,
          user.banned_at || '',
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `users_export_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    toast({ description: 'Users exported successfully', variant: 'success' });
  } catch (e) {
    console.error('Failed to export users', e);
    toast({
      title: 'Error',
      description: 'Failed to export users',
      variant: 'destructive',
    });
  }
};

const canDeleteUser = (targetUser: User): boolean => {
  // Check if current user has delete permission
  if (!authStore.hasPermission('users:delete')) return false;
  // Prevent deleting any admin
  if (isUserAdmin(targetUser.role)) return false;
  return true;
};

const canBanUser = (targetUser: User): boolean => {
  if (!authStore.hasPermission('users:update')) return false;
  if (isUserAdmin(targetUser.role)) return false;
  return true;
};

// --- Ban Modal Logic ---
const openBanModal = (user: User): void => {
  banModal.user = user;
  banModal.reason = 'Violation of Terms of Service';
  banModal.isOpen = true;
};

const closeBanModal = (): void => {
  banModal.isOpen = false;
  banModal.user = null;
};

const processBan = async (): Promise<void> => {
  if (!banModal.user) return;
  const user = banModal.user;
  const reason = banModal.reason || 'Violation of Terms of Service';

  try {
    await apiV1.post(`/admin/users/${user.id}/ban`, { reason });
    loadUsers(page.value);
    toast({
      description: `User ${user.name} has been banned.`,
      variant: 'success',
    });
    closeBanModal();
  } catch (e) {
    toast({
      title: 'Error',
      description: 'Failed to ban user',
      variant: 'destructive',
    });
    console.error(e);
  }
};

// --- Confirmation Modal Logic ---
const openConfirmModal = (
  title: string,
  message: string,
  confirmText: string,
  isDestructive: boolean,
  onConfirm: () => void
): void => {
  confirmModal.title = title;
  confirmModal.message = message;
  confirmModal.confirmText = confirmText;
  confirmModal.isDestructive = isDestructive;
  confirmModal.onConfirm = onConfirm;
  confirmModal.isOpen = true;
};

const closeConfirmModal = (): void => {
  confirmModal.isOpen = false;
};

const processConfirm = (): void => {
  confirmModal.onConfirm();
  closeConfirmModal();
};

const confirmDelete = (user: User): void => {
  openConfirmModal(
    'Delete User',
    `Are you sure you want to PERMANENTLY DELETE user ${user.name}? This action CANNOT be undone and will remove all their data.`,
    'Yes, Delete',
    true,
    async () => {
      try {
        await apiV1.delete(`/admin/users/${user.id}`);
        // Refresh list
        loadUsers(page.value);
        toast({
          description: `User ${user.name} has been deleted.`,
          variant: 'success',
        });
      } catch (e) {
        toast({
          title: 'Error',
          description: 'Failed to delete user',
          variant: 'destructive',
        });
        console.error(e);
      }
    }
  );
};

const confirmUnban = (user: User): void => {
  openConfirmModal(
    'Unban User',
    `Are you sure you want to unban user ${user.name}?`,
    'Unban',
    false,
    async () => {
      try {
        await apiV1.post(`/admin/users/${user.id}/unban`, {});
        loadUsers(page.value);
        toast({
          description: `User ${user.name} has been unbanned.`,
          variant: 'success',
        });
      } catch (e) {
        toast({
          title: 'Error',
          description: 'Failed to unban user',
          variant: 'destructive',
        });
        console.error(e);
      }
    }
  );
};

onMounted(() => {
  loadUsers();
  loadRoles();
});

// Role Management
interface Role {
  id: string;
  name: string;
}

const updatingUserIds = ref(new Set<string>());

const handleRoleChange = async (user: User, targetRoleName: string): Promise<void> => {
  if (user.role?.toLowerCase() === targetRoleName.toLowerCase()) return;

  const roleObj = roles.value.find((r) => r.name.toLowerCase() === targetRoleName.toLowerCase());
  if (!roleObj) {
    toast({
      title: 'Error',
      description: 'Target role not found in system',
      variant: 'destructive',
    });
    return;
  }

  updatingUserIds.value.add(user.id);
  try {
    await apiV1.put(`/admin/users/${user.id}/role`, {
      role_id: roleObj.id,
    });
    user.role = targetRoleName;
    toast({
      description: `Role updated to ${formatRoleName(targetRoleName)}`,
      variant: 'success',
    });
  } catch (e) {
    console.error('Failed to update role', e);
    toast({
      title: 'Error',
      description: 'Failed to update user role',
      variant: 'destructive',
    });
  } finally {
    updatingUserIds.value.delete(user.id);
  }
};

const roles = ref<Role[]>([]);

// Profile Management
const editingProfileUser = ref<User | null>(null);
const profileForm = ref({
  name: '',
  bio: '',
  picture: '',
});
const isSavingProfile = ref(false);

const canEditRole = authStore.hasPermission('users:update');
const canEditProfile = authStore.hasPermission('users:write');

const filteredRoles = ref<Role[]>([]);

const loadRoles = async (): Promise<void> => {
  try {
    const data = await apiV1.get<Role[]>('/admin/roles');
    // Filter to only show user and admin (or super_admin) roles
    filteredRoles.value = data.filter((r) => {
      const name = r.name.toLowerCase();
      return name === 'user' || name === 'admin' || name === 'super_admin';
    });
    roles.value = data;
  } catch (e) {
    console.error('Failed to load roles', e);
  }
};

const openProfileModal = (user: User): void => {
  editingProfileUser.value = user;
  profileForm.value = {
    name: user.name || '',
    bio: user.bio || '',
    picture: user.picture || '',
  };
};

const saveProfile = async (): Promise<void> => {
  if (!editingProfileUser.value) return;

  isSavingProfile.value = true;
  try {
    const updated = await apiV1.patch(
      `/admin/users/${editingProfileUser.value.id}/profile`,
      profileForm.value
    );

    // Update local object
    Object.assign(editingProfileUser.value, updated);

    editingProfileUser.value = null;
    loadUsers(page.value);
    toast({
      description: 'User profile updated successfully',
      variant: 'success',
    });
  } catch (e) {
    console.error('Failed to update profile', e);
    toast({
      title: 'Error',
      description: 'Failed to update profile',
      variant: 'destructive',
    });
  } finally {
    isSavingProfile.value = false;
  }
};
</script>
