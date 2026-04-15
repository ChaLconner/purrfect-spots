<template>
  <div class="bg-white rounded-2xl shadow-sm border border-sand-100 overflow-hidden">
    <div
      class="p-6 border-b border-sand-100 flex flex-col sm:flex-row justify-between items-center gap-4"
    >
      <h2 class="text-xl font-bold text-brown-900">{{ t('admin.audit.title') }}</h2>
      <div class="flex gap-2">
        <input
          v-model="userIdFilter"
          type="text"
          :placeholder="t('admin.audit.filters.userId')"
          class="pl-3 pr-3 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-700 bg-white text-sm w-40"
          @change="loadLogs(1)"
        />
        <select
          v-model="actionFilter"
          class="pl-3 pr-10 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-700 bg-white text-sm"
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
        <button
          class="p-2 rounded-lg border border-sand-300 hover:bg-sand-50 text-brown-500"
          :title="t('common.refresh')"
          @click="loadLogs(1, true)"
        >
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
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </button>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-sand-200">
        <thead class="bg-sand-50">
          <tr>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              {{ t('admin.audit.table.date') }}
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              {{ t('admin.audit.table.user') }}
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              {{ t('admin.audit.table.action') }}
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              {{ t('admin.audit.table.resource') }}
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              {{ t('admin.audit.table.details') }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-sand-200">
          <tr v-for="log in logs" :key="log.id" class="hover:bg-sand-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-brown-500">
              {{ new Date(log.created_at).toLocaleString(locale) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-brown-900">
              <div v-if="log.users">
                <div class="font-medium">{{ log.users.name || t('common.unknown') }}</div>
                <div class="text-xs text-brown-500">{{ log.users.email }}</div>
              </div>
              <span v-else class="text-gray-400">{{ t('admin.audit.table.system') }}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span
                class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800"
              >
                {{ t(`admin.audit.actions.${log.action}`) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-brown-500">
              {{ log.resource }}
            </td>
            <td class="px-6 py-4 text-sm text-brown-500">
              <button
                class="text-indigo-600 hover:text-indigo-900 font-medium"
                @click="viewDetails(log)"
              >
                {{ t('common.viewDetails') }}
              </button>
            </td>
          </tr>
          <tr v-if="logs.length === 0 && !isLoading">
            <td colspan="5" class="px-6 py-12 text-center text-brown-500">
              {{ t('admin.audit.table.noLogs') }}
            </td>
          </tr>
          <TableSkeleton v-if="isLoading" :columns="5" :avatar-column="2" />
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="logs.length > 0"
      class="px-6 py-4 border-t border-sand-200 flex items-center justify-between"
    >
      <button
        :disabled="page === 1"
        class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 hover:bg-sand-50 disabled:opacity-50"
        @click="loadLogs(page - 1)"
      >
        {{ t('common.previous') }}
      </button>
      <span class="text-sm text-brown-600">{{ t('common.page', { n: page }) }}</span>
      <button
        :disabled="logs.length < limit || page * limit >= totalLogs"
        class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 hover:bg-sand-50 disabled:opacity-50"
        @click="loadLogs(page + 1)"
      >
        {{ t('common.next') }}
      </button>
    </div>

    <!-- Details Modal -->
    <div
      v-if="selectedLog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click="selectedLog = null"
    >
      <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6" @click.stop>
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold text-brown-900">{{ t('admin.audit.modal.title') }}</h3>
          <button class="text-gray-400 hover:text-gray-600" @click="selectedLog = null">
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

        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="block text-gray-500">{{ t('admin.audit.table.action') }}</span>
              <span class="font-medium text-brown-900">{{ selectedLog.action }}</span>
            </div>
            <div>
              <span class="block text-gray-500">{{ t('admin.audit.table.resource') }}</span>
              <span class="font-medium text-brown-900">{{ selectedLog.resource }}</span>
            </div>
            <div>
              <span class="block text-gray-500">{{ t('admin.audit.table.user') }}</span>
              <span class="font-medium text-brown-900">
                {{ selectedLog.users?.email || t('admin.audit.table.system') }}
              </span>
            </div>
            <div>
              <span class="block text-gray-500">{{ t('admin.audit.table.date') }}</span>
              <span class="font-medium text-brown-900">
                {{ new Date(selectedLog.created_at).toLocaleString(locale) }}
              </span>
            </div>
          </div>

          <div>
            <span class="block text-gray-500 mb-1 text-sm">{{
              t('admin.audit.modal.changesPayload')
            }}</span>
            <div
              class="bg-gray-50 rounded-lg p-4 font-mono text-xs overflow-auto max-h-96 relative group"
            >
              <pre>{{ JSON.stringify(selectedLog.changes, null, 2) }}</pre>
              <button
                class="absolute top-2 right-2 p-1 bg-white border border-gray-200 rounded shadow-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-50"
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

import { apiV1 } from '@/utils/api';
import { useToast } from '@/components/toast/use-toast';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';

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
const logs = ref<AuditLog[]>([]);
const page = ref(1);
const limit = 50;
const isLoading = ref(false);
const totalLogs = ref(0);
const userIdFilter = ref('');
const actionFilter = ref('');
const selectedLog = ref<AuditLog | null>(null);

const { toast } = useToast();

const loadLogs = async (newPage: number = 1, forceRefresh: boolean = false): Promise<void> => {
  isLoading.value = true;
  try {
    const offset = (newPage - 1) * limit;
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (userIdFilter.value) params.append('user_id', userIdFilter.value);
    if (actionFilter.value) params.append('action', actionFilter.value);
    if (forceRefresh) params.append('cache_bust', Date.now().toString());

    const response = await apiV1.get<{ data: AuditLog[]; total: number }>(
      `/admin/audit-logs?${params.toString()}`
    );
    logs.value = response.data;
    totalLogs.value = response.total;
    page.value = newPage;
  } catch (e) {
    console.error('Failed to load audit logs', e);
    toast({
      title: t('common.error'),
      description: t('admin.audit.failedToLoad'),
      variant: 'destructive',
    });
  } finally {
    isLoading.value = false;
  }
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
