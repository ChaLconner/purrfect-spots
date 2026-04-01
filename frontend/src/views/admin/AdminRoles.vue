<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-bold text-brown-900 font-display tracking-tight">{{ t('admin.roles.title') }}</h1>
      <p class="text-brown-500 font-medium">{{ t('admin.roles.subtitle') }}</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
      <!-- Role List -->
      <div
        class="bg-white rounded-2xl shadow-sm border border-sand-100 overflow-hidden lg:col-span-1 flex flex-col h-full"
      >
        <div class="p-6 border-b border-sand-100">
          <h3 class="text-xl font-bold text-brown-900">{{ t('admin.roles.list_title') }}</h3>
        </div>
        <div v-if="loading" class="flex flex-col items-center justify-center p-12 text-brown-400">
          <div
            class="w-8 h-8 border-4 border-sand-200 border-t-terracotta-500 rounded-full animate-spin mb-4"
          ></div>
          <span>{{ t('common.loading') }}</span>
        </div>
        <div
          v-else
          class="max-h-[calc(100vh-300px)] overflow-y-auto divide-y divide-sand-100 ghibli-soft-scroll"
        >
          <div
            v-for="role in roles"
            :key="role.id"
            class="px-6 py-5 flex justify-between items-center cursor-pointer transition-all hover:bg-sand-50/80 group relative"
            :class="{
              'bg-terracotta-50/50': selectedRole?.id === role.id,
            }"
            @click="selectRole(role)"
          >
            <!-- Selection Indicator -->
            <div 
              v-if="selectedRole?.id === role.id"
              class="absolute left-0 top-0 bottom-0 w-1.5 bg-terracotta-500 rounded-r-full"
            ></div>
            <div class="flex flex-col">
              <div class="flex items-center gap-2">
                <span
                  class="font-bold text-brown-900 text-base"
                  :class="{ 'text-terracotta-800': selectedRole?.id === role.id }"
                  >{{ role.name }}</span
                >
                <span
                  v-if="dirty && selectedRole?.id === role.id"
                  class="w-2 h-2 bg-terracotta-500 rounded-full animate-pulse"
                  :title="t('admin.roles.unsaved_changes')"
                ></span>
              </div>
              <span
                class="text-xs text-brown-500 mt-0.5 uppercase tracking-wide opacity-70 group-hover:opacity-100 transition-opacity"
                >{{ role.id }}</span
              >
            </div>
            <div class="flex items-center gap-3 text-brown-500">
              <span
                class="px-2.5 py-0.5 bg-sand-100 text-brown-600 rounded-full text-xs font-semibold transition-colors"
                :class="{ 'bg-terracotta-100 text-terracotta-700': selectedRole?.id === role.id }"
                :title="t('admin.roles.perm_count')"
              >
                {{ getRolePermissionCount(role.id) }}
              </span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4 transition-transform group-hover:translate-x-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Permission Assignment -->
      <div
        v-if="selectedRole"
        class="bg-white rounded-2xl shadow-sm border border-sand-100 lg:col-span-2 overflow-hidden flex flex-col h-full"
      >
        <div
          class="px-6 py-6 border-b border-sand-100 flex flex-col sm:flex-row sm:items-center justify-between gap-6"
        >
          <div class="flex flex-col">
            <h3 class="text-xl font-bold text-brown-900">
              <span class="opacity-50 font-medium">{{ t('admin.roles.permissions_for') }}:</span>
              <span class="text-terracotta-600 ml-2">{{ selectedRole.name }}</span>
            </h3>
            <div class="mt-3 flex">
              <span
                class="inline-flex items-center gap-2 px-3 py-1.5 bg-terracotta-50 text-terracotta-700 text-xs font-semibold rounded-full uppercase tracking-wider border border-terracotta-100/50"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-3.5 w-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
                ID: {{ selectedRole.id }}
              </span>
            </div>
          </div>

          <div class="flex items-center gap-2 sm:gap-3">
            <div class="relative group">
              <svg
                class="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-brown-400 group-focus-within:text-terracotta-500 transition-colors"
                xmlns="http://www.w3.org/2000/svg"
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
              <input
                v-model="permissionSearch"
                type="text"
                :placeholder="t('admin.roles.search_perms')"
                class="pl-10 pr-4 py-2 w-48 lg:w-64 border border-sand-300 rounded-lg bg-white focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 outline-none transition-colors font-medium text-sm text-brown-800"
              />
            </div>

            <button
              v-if="dirty"
              class="px-4 py-2 border border-sand-300 text-brown-600 rounded-lg hover:bg-sand-50 transition-colors text-sm font-medium flex items-center gap-2 shadow-sm"
              :disabled="saving"
              @click="resetToOriginal"
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
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span class="hidden md:inline">{{ t('admin.roles.reset') }}</span>
            </button>

            <button
              class="px-4 py-2 bg-terracotta-600 text-white rounded-lg hover:bg-terracotta-700 transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2 text-sm font-medium"
              :disabled="saving || !dirty"
              @click="savePermissions"
            >
              <svg
                v-if="saving"
                class="animate-spin h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4 outline-none"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"
                />
              </svg>
              {{ t('common.save') }}
            </button>
          </div>
        </div>

        <!-- Self-lockout Warning -->
        <div
          v-if="showSelfLockoutWarning"
          class="mx-6 mt-6 p-4 bg-amber-50/50 border border-amber-100 rounded-2xl flex items-start gap-4 animate-in fade-in slide-in-from-top-4 shadow-sm"
        >
          <div class="p-2 bg-amber-100 rounded-xl text-amber-600">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          <div class="flex flex-col">
            <span class="text-sm font-bold text-amber-900">{{
              t('admin.roles.self_lockout_title')
            }}</span>
            <p class="text-xs text-amber-700 font-medium leading-relaxed mt-1">
              {{ t('admin.roles.self_lockout_warning') }}
            </p>
          </div>
        </div>

        <!-- Summary Stats -->
        <div class="px-8 py-6 bg-sand-50/20 border-b border-sand-100 flex gap-10">
          <div class="flex flex-col">
            <span class="text-3xl font-bold text-brown-900 transition-all">{{ activePermissions.length }}</span>
            <span class="text-xs font-medium text-brown-500 uppercase tracking-wider">{{
              t('admin.roles.assigned')
            }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-3xl font-bold text-brown-900 transition-all">{{ totalPermissions }}</span>
            <span class="text-xs font-medium text-brown-500 uppercase tracking-wider">{{
              t('admin.roles.total')
            }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-3xl font-bold text-terracotta-600 transition-all"
              >{{
                totalPermissions > 0
                  ? Math.round((activePermissions.length / totalPermissions) * 100)
                  : 0
              }}%</span
            >
            <span class="text-xs font-medium text-brown-500 uppercase tracking-wider">{{
              t('admin.roles.coverage')
            }}</span>
          </div>
        </div>

        <div class="p-6 overflow-y-auto space-y-8 flex-1">
          <div
            v-for="(groupPermissions, group) in formattedGroupedPermissions"
            :key="group"
            class="space-y-4"
          >
            <div class="flex justify-between items-center pb-2 border-b-2 border-sand-100/50">
              <div class="flex flex-col gap-1">
                <h4 class="text-lg font-bold text-brown-900 flex items-center gap-3">
                  {{
                    t(`admin.roles.groups.${group}`) !== `admin.roles.groups.${group}`
                      ? t(`admin.roles.groups.${group}`)
                      : formatGroupName(group)
                  }}
                  <span
                    class="px-2.5 py-0.5 bg-sand-100 text-brown-500 rounded-full text-xs font-semibold tracking-wider uppercase shrink-0 leading-5"
                  >
                    {{ getSelectedCount(groupPermissions) }} / {{ groupPermissions.length }}
                  </span>
                </h4>
                <div class="flex items-center gap-3 text-xs font-medium">
                  <button
                    class="text-terracotta-500 hover:text-terracotta-600 transition-colors"
                    @click="toggleGroup(groupPermissions, true)"
                  >
                    {{ t('common.selectAll') }}
                  </button>
                  <span class="text-sand-300">/</span>
                  <button
                    class="text-brown-400 hover:text-brown-600 transition-colors"
                    @click="toggleGroup(groupPermissions, false)"
                  >
                    {{ t('common.deselectAll') }}
                  </button>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label
                v-for="perm in groupPermissions"
                :key="perm.id"
                class="flex items-start gap-3.5 p-4 rounded-2xl border-2 cursor-pointer transition-all hover:shadow-md active:scale-[0.98]"
                :class="
                  activePermissions.includes(perm.id)
                    ? 'bg-terracotta-50/30 border-terracotta-400/30 shadow-sm'
                    : 'bg-white border-sand-100 hover:border-sand-200 hover:bg-sand-50/30'
                "
                :title="perm.description"
              >
                <div class="relative flex items-center mt-0.5">
                  <input
                    v-model="activePermissions"
                    type="checkbox"
                    :value="perm.id"
                    class="peer sr-only"
                    @change="markDirty"
                  />
                  <div
                    class="w-5 h-5 border-2 rounded shrink-0 transition-colors flex items-center justify-center border-sand-300 bg-white peer-checked:border-terracotta-500 peer-checked:bg-terracotta-500"
                  >
                    <svg
                      class="w-3.5 h-3.5 text-white opacity-0 peer-checked:opacity-100 transition-opacity"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="3"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                </div>
                <div class="flex flex-col flex-1">
                  <span class="font-bold text-brown-900 text-sm leading-tight">{{
                    perm.code || perm.id
                  }}</span>
                  <p class="text-xs text-brown-500 mt-1 leading-snug">{{ perm.description }}</p>
                </div>
              </label>
            </div>
          </div>

          <div
            v-if="Object.keys(formattedGroupedPermissions).length === 0"
            class="flex flex-col items-center justify-center py-12 text-brown-400"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-12 w-12 mb-4 opacity-50"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <p class="font-bold text-lg text-brown-500">{{ t('admin.roles.no_results') }}</p>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else
        class="bg-white rounded-2xl shadow-sm border border-sand-100 lg:col-span-2 flex flex-col items-center justify-center py-12 text-center px-4"
      >
        <div class="p-6 bg-sand-50 rounded-full mb-6">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-16 w-16 text-sand-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-brown-900 mb-2">
          {{ t('admin.roles.select_prompt') }}
        </h3>
        <p class="text-brown-500 font-medium max-w-sm">{{ t('admin.roles.select_hint') }}</p>
      </div>
    </div>

    <!-- Unsaved Changes Modal -->
    <BaseConfirmModal
      :is-open="unsavedChangesConfirmOpen"
      :title="t('admin.roles.confirm_reset_title')"
      :message="t('admin.roles.confirm_reset')"
      :confirm-text="t('common.continue')"
      variant="warning"
      @close="unsavedChangesConfirmOpen = false"
      @confirm="executeSelectRole"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { useToast } from '@/components/toast/use-toast';
import { useAuthStore } from '@/store/authStore';
import { BaseConfirmModal } from '@/components/ui';

interface AdminRole {
  id: string;
  name: string;
}

interface AdminPermission {
  id: string;
  code: string;
  description: string;
  group: string | null;
}

const { t } = useI18n();
const { toast } = useToast();

const roles = ref<AdminRole[]>([]);
const permissions = ref<AdminPermission[]>([]);
const selectedRole = ref<AdminRole | null>(null);
const activePermissions = ref<string[]>([]);
const originalPermissions = ref<string[]>([]);
const rolePermissionCounts = ref<Record<string, number>>({});
const loading = ref(true);
const saving = ref(false);
const dirty = ref(false);
const permissionSearch = ref('');
const unsavedChangesConfirmOpen = ref(false);
const pendingRoleToSelect = ref<AdminRole | null>(null);

const authStore = useAuthStore();
const currentUserRole = computed(() => authStore.user?.role);

const showSelfLockoutWarning = computed(() => {
  if (!selectedRole.value || !dirty.value) return false;
  // If editing user's own role and removing manage permissions
  if (selectedRole.value.id === currentUserRole.value) {
    const hasManage = activePermissions.value.some(
      (p) => p.includes('manage') || p.includes('admin') || p.includes('*')
    );
    return !hasManage;
  }
  return false;
});

const totalPermissions = computed(() => permissions.value.length);

const getRolePermissionCount = (roleId: string): number => {
  return rolePermissionCounts.value[roleId] || 0;
};

const groupedPermissions = computed(() => {
  const groups: Record<string, AdminPermission[]> = {};
  permissions.value.forEach((p) => {
    let group = (p.group || 'general').toLowerCase().trim().replace(/ /g, '_');

    // Manual mapping for common inconsistent groups
    if (group === 'rbac' || group === 'role' || group === 'roles') group = 'access_control';
    if (group.includes('content') || group.includes('photo')) group = 'content';
    if (group.includes('user')) group = 'users';
    if (group.includes('treat')) group = 'treats';
    if (group.includes('system') || group.includes('audit')) group = 'system';

    if (!groups[group]) groups[group] = [];
    groups[group].push(p);
  });
  return groups;
});

const formatGroupName = (key: string): string => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

const formattedGroupedPermissions = computed(() => {
  const search = permissionSearch.value.toLowerCase().trim();
  const result: Record<string, AdminPermission[]> = {};

  Object.entries(groupedPermissions.value).forEach(([group, perms]) => {
    const matchingPerms = perms.filter(
      (p) =>
        p.code?.toLowerCase().includes(search) ||
        p.description.toLowerCase().includes(search) ||
        group.toLowerCase().includes(search)
    );

    if (matchingPerms.length > 0) {
      // Sort alphabetically by code
      result[group] = matchingPerms.sort((a, b) => (a.code || '').localeCompare(b.code || ''));
    }
  });

  return result;
});

const getSelectedCount = (groupPermissions: AdminPermission[]): number => {
  return groupPermissions.filter((p) => activePermissions.value.includes(p.id)).length;
};

const toggleGroup = (groupPermissions: AdminPermission[], select: boolean): void => {
  const permIds = groupPermissions.map((p) => p.id);
  if (select) {
    const toAdd = permIds.filter((id) => !activePermissions.value.includes(id));
    if (toAdd.length > 0) {
      activePermissions.value = [...activePermissions.value, ...toAdd];
      markDirty();
    }
  } else {
    const toKeep = activePermissions.value.filter((id) => !permIds.includes(id));
    if (toKeep.length !== activePermissions.value.length) {
      activePermissions.value = toKeep;
      markDirty();
    }
  }
};

const selectRole = (role: AdminRole): void => {
  if (dirty.value) {
    pendingRoleToSelect.value = role;
    unsavedChangesConfirmOpen.value = true;
    return;
  }

  void executeSelectRole(role);
};

const executeSelectRole = async (role?: AdminRole): Promise<void> => {
  const roleToSelect = role || pendingRoleToSelect.value;
  if (!roleToSelect) return;

  unsavedChangesConfirmOpen.value = false;
  selectedRole.value = roleToSelect;
  activePermissions.value = [];
  originalPermissions.value = [];
  dirty.value = false;
  permissionSearch.value = '';
  pendingRoleToSelect.value = null;

  try {
    const data = await apiV1.get<string[]>(`/admin/roles/${roleToSelect.id}/permissions`);
    activePermissions.value = data;
    originalPermissions.value = [...data];
    rolePermissionCounts.value[roleToSelect.id] = data.length;
  } catch {
    toast({
      title: t('common.error'),
      description: t('admin.roles.fetch_error'),
      variant: 'destructive',
    });
  }
};

const resetToOriginal = (): void => {
  activePermissions.value = [...originalPermissions.value];
  dirty.value = false;
  toast({
    description: t('common.refresh'),
    variant: 'default',
  });
};

const markDirty = (): void => {
  dirty.value = true;
};

const savePermissions = async (): Promise<void> => {
  if (!selectedRole.value) return;
  saving.value = true;

  try {
    await apiV1.post(`/admin/roles/${selectedRole.value.id}/permissions`, {
      role_id: selectedRole.value.id,
      permission_ids: activePermissions.value,
    });
    toast({
      description: t('admin.roles.save_success'),
      variant: 'success',
    });
    dirty.value = false;
    originalPermissions.value = [...activePermissions.value];
    rolePermissionCounts.value[selectedRole.value.id] = activePermissions.value.length;
  } catch {
    toast({
      title: t('common.error'),
      description: t('admin.roles.save_error'),
      variant: 'destructive',
    });
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  try {
    const [rolesData, permsData] = await Promise.all([
      apiV1.get<AdminRole[]>('/admin/roles'),
      apiV1.get<AdminPermission[]>('/admin/roles/permissions'),
    ]);
    roles.value = rolesData || [];
    permissions.value = permsData || [];

    for (const role of roles.value) {
      try {
        const perms = await apiV1.get<string[]>(`/admin/roles/${role.id}/permissions`);
        rolePermissionCounts.value[role.id] = perms.length;
      } catch {
        rolePermissionCounts.value[role.id] = 0;
      }
    }
  } catch {
    toast({
      title: t('common.error'),
      description: t('admin.roles.load_error'),
      variant: 'destructive',
    });
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.ghibli-soft-scroll::-webkit-scrollbar {
  width: 6px;
}
.ghibli-soft-scroll::-webkit-scrollbar-track {
  background: #f8f5f2;
}
.ghibli-soft-scroll::-webkit-scrollbar-thumb {
  background: #e2d7cc;
  border-radius: 10px;
}
.ghibli-soft-scroll::-webkit-scrollbar-thumb:hover {
  background: #d4c5b5;
}
</style>
