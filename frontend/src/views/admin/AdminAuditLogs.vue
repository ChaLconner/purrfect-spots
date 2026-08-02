<template>
  <div class="flex flex-col gap-4">
    <AdminPageHeader :title="t('admin.audit.title')">
      <template #actions>
        <input
          v-model="userIdFilter"
          type="text"
          :placeholder="t('admin.audit.filters.userId')"
          :aria-label="t('admin.audit.filters.userId')"
          class="w-full sm:w-52 px-4 py-3 border border-sand-300 rounded-xl text-[#6a5a53] bg-white text-sm outline-none focus:border-terracotta-500 focus:ring-2 focus:ring-terracotta-100"
          @change="loadLogs(1)"
        />
        <select
          v-model="actionFilter"
          :aria-label="t('admin.audit.filters.allActions')"
          class="w-full sm:min-w-[18rem] sm:w-auto px-4 py-3 pr-10 border border-sand-300 rounded-xl text-[#6a5a53] bg-white text-sm outline-none focus:border-terracotta-500 focus:ring-2 focus:ring-terracotta-100"
          @change="loadLogs(1)"
        >
          <option value="">{{ t('admin.audit.filters.allActions') }}</option>
          <option value="LOGIN">{{ t('admin.audit.actions.LOGIN') }}</option>
          <option value="LOGOUT">{{ t('admin.audit.actions.LOGOUT') }}</option>
          <option value="DELETE_USER">{{ t('admin.audit.actions.DELETE_USER') }}</option>
          <option value="UPDATE_ROLE">{{ t('admin.audit.actions.UPDATE_ROLE') }}</option>
          <option value="BAN_USER">{{ t('admin.audit.actions.BAN_USER') }}</option>
          <option value="UNBAN_USER">{{ t('admin.audit.actions.UNBAN_USER') }}</option>
          <option value="DELETE_PHOTO_VIA_REPORT">
            {{ t('admin.audit.actions.DELETE_PHOTO_VIA_REPORT') }}
          </option>
          <option value="DELETE_PHOTO_VIA_BULK_REPORT">
            {{ t('admin.audit.actions.DELETE_PHOTO_VIA_BULK_REPORT') }}
          </option>
        </select>
        <RefreshButton
          :title="t('common.refresh')"
          @refresh="loadLogs(1, true)"
        />
      </template>
    </AdminPageHeader>

    <div class="overflow-hidden border border-sand-200/95 rounded-xl bg-white shadow-sm">
      <div class="overflow-x-auto">
        <table class="min-w-full border-separate border-spacing-0">
        <thead class="bg-[#faf8f5]">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-[#6a5a53] uppercase tracking-wider border-b border-sand-200">
              {{ t('admin.audit.table.date') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-[#6a5a53] uppercase tracking-wider border-b border-sand-200">
              {{ t('admin.audit.table.user') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-[#6a5a53] uppercase tracking-wider border-b border-sand-200">
              {{ t('admin.audit.table.action') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-[#6a5a53] uppercase tracking-wider border-b border-sand-200">
              {{ t('admin.audit.table.resource') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-[#6a5a53] uppercase tracking-wider border-b border-sand-200">
              {{ t('admin.audit.table.details') }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white">
          <tr v-for="log in logs" :key="log.id" class="transition-colors hover:bg-[#faf8f5]">
            <td class="px-6 py-4 text-sm border-b border-sand-200 whitespace-nowrap text-[#6a5a53]">
              {{ formatTimestamp(log.created_at, locale) }}
            </td>
            <td class="px-6 py-4 text-sm border-b border-sand-200 whitespace-nowrap text-[#2f231f]">
              <div v-if="log.users">
                <div class="font-medium">{{ log.users.name || t('common.unknown') }}</div>
                <div class="text-xs text-[#6a5a53]">{{ log.users.email }}</div>
              </div>
              <span v-else class="text-gray-400">{{ t('admin.audit.table.system') }}</span>
            </td>
            <td class="px-6 py-4 text-sm border-b border-sand-200 whitespace-nowrap">
              <span class="inline-flex px-2 py-0.5 text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-700">
                {{ t(`admin.audit.actions.${log.action}`) }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm border-b border-sand-200 whitespace-nowrap text-[#6a5a53]">
              {{ log.resource }}
            </td>
            <td class="px-6 py-4 text-sm border-b border-sand-200 text-[#6a5a53]">
              <button class="font-medium text-indigo-600 transition-colors hover:text-indigo-900" @click="viewDetails(log)">
                {{ t('common.viewDetails') }}
              </button>
            </td>
          </tr>
          <tr v-if="logs.length === 0 && !isLoading">
            <td colspan="5" class="p-12 px-6 text-center text-[#6a5a53]">
              {{ t('admin.audit.table.noLogs') }}
            </td>
          </tr>
          <TableSkeleton v-if="isLoading" :columns="5" :avatar-column="2" />
        </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <AdminPagination
        v-model:page="page"
        :limit="limit"
        :total-items="totalLogs"
        :items-length="logs.length"
        :previous-text="t('common.previous')"
        :next-text="t('common.next')"
        :page-text="t('common.page', { n: page })"
        @update:page="loadLogs"
      />
    </div>

    <!-- Details Modal -->
    <div
      v-if="selectedLog"
      class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      @click="selectedLog = null"
    >
      <div class="w-full max-w-2xl p-6 bg-white rounded-xl shadow-2xl" @click.stop>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-[#2f231f]">{{ t('admin.audit.modal.title') }}</h3>
          <button class="text-gray-400 transition-colors hover:text-gray-600" @click="selectedLog = null">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div class="grid gap-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="block text-gray-500">{{ t('admin.audit.table.action') }}</span>
              <span class="font-medium text-[#2f231f]">{{ selectedLog.action }}</span>
            </div>
            <div>
              <span class="block text-gray-500">{{ t('admin.audit.table.resource') }}</span>
              <span class="font-medium text-[#2f231f]">{{ selectedLog.resource }}</span>
            </div>
            <div>
              <span class="block text-gray-500">{{ t('admin.audit.table.user') }}</span>
              <span class="font-medium text-[#2f231f]">
                {{ selectedLog.users?.email || t('admin.audit.table.system') }}
              </span>
            </div>
            <div>
              <span class="block text-gray-500">{{ t('admin.audit.table.date') }}</span>
              <span class="font-medium text-[#2f231f]">
                {{ formatTimestamp(selectedLog.created_at, locale) }}
              </span>
            </div>
          </div>

          <div>
            <span class="block mb-1 text-sm text-gray-500">{{
              t('admin.audit.modal.changesPayload')
            }}</span>
            <div class="group relative max-h-96 overflow-auto rounded-lg bg-gray-50 p-4 font-mono text-xs">
              <pre>{{ JSON.stringify(selectedLog.changes, null, 2) }}</pre>
              <button
                class="absolute top-2 right-2 p-1 bg-white border border-gray-200 rounded shadow-sm opacity-0 transition-opacity group-hover:opacity-100 hover:bg-gray-50"
                :title="t('common.copyJson')"
                @click="copyToClipboard(JSON.stringify(selectedLog.changes, null, 2))"
              >
                <svg
                  class="w-4 h-4 text-gray-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

import { useToast } from '@/composables/useToast';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';
import RefreshButton from '@/components/ui/RefreshButton.vue';
import AdminPagination from '@/components/ui/AdminPagination.vue';
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue';
import { formatTimestamp } from '@/utils/date';
import { useAdminTable } from '@/composables/useAdminTable';

interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource: string;
  changes: Record<string, unknown>;
  created_at: string;
  users?: {
    email: string;
    name: string;
  };
}

const { t, locale } = useI18n();

const userIdFilter = ref('');
const actionFilter = ref('');
const selectedLog = ref<AuditLog | null>(null);

const { toast } = useToast();

const {
  items: logs,
  totalItems: totalLogs,
  page,
  limit,
  isLoading,
  loadData,
} = useAdminTable<AuditLog>({
  endpoint: '/admin/audit-logs',
  limit: 50,
  exportHeaders: [],
  formatExportRow: () => [],
  exportFileNamePrefix: 'audit_logs',
});

const loadLogs = (newPage: number = 1, forceRefresh: boolean = false): void => {
  const extraParams: Record<string, string> = {};
  if (userIdFilter.value) extraParams.user_id = userIdFilter.value;
  if (actionFilter.value) extraParams.action = actionFilter.value;
  if (forceRefresh) extraParams.cache_bust = Date.now().toString();
  loadData(newPage, extraParams);
};

const viewDetails = (log: AuditLog): void => {
  selectedLog.value = log;
};

const copyToClipboard = async (text: string): Promise<void> => {
  try {
    await navigator.clipboard.writeText(text);
    toast({ description: t('common.copiedToClipboard'), variant: 'success' });
  } catch (err) {
    console.error('Failed to copy', err);
  }
};

onMounted(() => {
  loadLogs();
});
</script>
