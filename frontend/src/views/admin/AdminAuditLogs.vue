<template>
  <div class="admin-audit-shell">
    <div class="admin-audit-header">
      <h2 class="admin-audit-title">{{ t('admin.audit.title') }}</h2>
      <div class="admin-audit-filters">
        <input
          v-model="userIdFilter"
          type="text"
          :placeholder="t('admin.audit.filters.userId')"
          class="admin-audit-filter-input admin-audit-user-filter"
          @change="loadLogs(1)"
        />
        <select
          v-model="actionFilter"
          class="admin-audit-filter-input admin-audit-action-filter"
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
      </div>
    </div>

    <div class="admin-audit-table-scroll">
      <table class="admin-audit-table">
        <thead class="admin-audit-table-head">
          <tr>
            <th class="admin-audit-head-cell">
              {{ t('admin.audit.table.date') }}
            </th>
            <th class="admin-audit-head-cell">
              {{ t('admin.audit.table.user') }}
            </th>
            <th class="admin-audit-head-cell">
              {{ t('admin.audit.table.action') }}
            </th>
            <th class="admin-audit-head-cell">
              {{ t('admin.audit.table.resource') }}
            </th>
            <th class="admin-audit-head-cell">
              {{ t('admin.audit.table.details') }}
            </th>
          </tr>
        </thead>
        <tbody class="admin-audit-table-body">
          <tr v-for="log in logs" :key="log.id" class="admin-audit-row">
            <td class="admin-audit-cell admin-audit-cell-nowrap admin-audit-cell-muted">
              {{ formatTimestamp(log.created_at, locale) }}
            </td>
            <td class="admin-audit-cell admin-audit-cell-nowrap admin-audit-cell-primary">
              <div v-if="log.users">
                <div class="admin-audit-user-name">{{ log.users.name || t('common.unknown') }}</div>
                <div class="admin-audit-user-email">{{ log.users.email }}</div>
              </div>
              <span v-else class="admin-audit-system-user">{{ t('admin.audit.table.system') }}</span>
            </td>
            <td class="admin-audit-cell admin-audit-cell-nowrap">
              <span class="admin-audit-action-badge">
                {{ t(`admin.audit.actions.${log.action}`) }}
              </span>
            </td>
            <td class="admin-audit-cell admin-audit-cell-nowrap admin-audit-cell-muted">
              {{ log.resource }}
            </td>
            <td class="admin-audit-cell admin-audit-cell-muted">
              <button class="admin-audit-view-details" @click="viewDetails(log)">
                {{ t('common.viewDetails') }}
              </button>
            </td>
          </tr>
          <tr v-if="logs.length === 0 && !isLoading">
            <td colspan="5" class="admin-audit-empty-cell">
              {{ t('admin.audit.table.noLogs') }}
            </td>
          </tr>
          <TableSkeleton v-if="isLoading" :columns="5" :avatar-column="2" />
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
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

    <!-- Details Modal -->
    <div
      v-if="selectedLog"
      class="admin-audit-modal-overlay"
      @click="selectedLog = null"
    >
      <div class="admin-audit-modal" @click.stop>
        <div class="admin-audit-modal-header">
          <h3 class="admin-audit-modal-title">{{ t('admin.audit.modal.title') }}</h3>
          <button class="admin-audit-modal-close" @click="selectedLog = null">
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

        <div class="admin-audit-modal-content">
          <div class="admin-audit-modal-grid">
            <div>
              <span class="admin-audit-modal-label">{{ t('admin.audit.table.action') }}</span>
              <span class="admin-audit-modal-value">{{ selectedLog.action }}</span>
            </div>
            <div>
              <span class="admin-audit-modal-label">{{ t('admin.audit.table.resource') }}</span>
              <span class="admin-audit-modal-value">{{ selectedLog.resource }}</span>
            </div>
            <div>
              <span class="admin-audit-modal-label">{{ t('admin.audit.table.user') }}</span>
              <span class="admin-audit-modal-value">
                {{ selectedLog.users?.email || t('admin.audit.table.system') }}
              </span>
            </div>
            <div>
              <span class="admin-audit-modal-label">{{ t('admin.audit.table.date') }}</span>
              <span class="admin-audit-modal-value">
                {{ formatTimestamp(selectedLog.created_at, locale) }}
              </span>
            </div>
          </div>

          <div>
            <span class="admin-audit-modal-label admin-audit-modal-label-payload">{{
              t('admin.audit.modal.changesPayload')
            }}</span>
            <div class="admin-audit-json-box">
              <pre>{{ JSON.stringify(selectedLog.changes, null, 2) }}</pre>
              <button
                class="admin-audit-copy-json"
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
import RefreshButton from '@/components/ui/RefreshButton.vue';
import AdminPagination from '@/components/ui/AdminPagination.vue';
import { formatTimestamp } from '@/utils/date';

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

<style scoped>
.admin-audit-shell {
  background: #fff;
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  border: 1px solid #f2ece8;
  overflow: hidden;
}

.admin-audit-header {
  padding: 1.5rem;
  border-bottom: 1px solid #f2ece8;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.admin-audit-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2f231f;
}

.admin-audit-filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.admin-audit-filter-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d6d3d1;
  border-radius: 0.5rem;
  color: #6a5a53;
  background: #fff;
  font-size: 0.875rem;
}

.admin-audit-filter-input:focus {
  outline: none;
  border-color: #c15f36;
  box-shadow: 0 0 0 2px rgba(193, 95, 54, 0.2);
}

.admin-audit-user-filter {
  width: 10rem;
}

.admin-audit-action-filter {
  padding-right: 2.5rem;
}

.admin-audit-table-scroll {
  overflow-x: auto;
}

.admin-audit-table {
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.admin-audit-table-head {
  background: #faf8f5;
}

.admin-audit-head-cell {
  padding: 0.75rem 1.5rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6a5a53;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e7e5e4;
}

.admin-audit-table-body {
  background: #fff;
}

.admin-audit-row {
  transition: background-color 0.2s ease;
}

.admin-audit-row:hover {
  background: #faf8f5;
}

.admin-audit-cell {
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  border-bottom: 1px solid #e7e5e4;
}

.admin-audit-cell-nowrap {
  white-space: nowrap;
}

.admin-audit-cell-primary {
  color: #2f231f;
}

.admin-audit-cell-muted {
  color: #6a5a53;
}

.admin-audit-user-name {
  font-weight: 500;
}

.admin-audit-user-email {
  font-size: 0.75rem;
  color: #6a5a53;
}

.admin-audit-system-user {
  color: #9ca3af;
}

.admin-audit-action-badge {
  display: inline-flex;
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
  line-height: 1.25rem;
  font-weight: 600;
  border-radius: 9999px;
  background: #dbeafe;
  color: #1e40af;
}

.admin-audit-view-details {
  color: #4f46e5;
  font-weight: 500;
  transition: color 0.2s ease;
}

.admin-audit-view-details:hover {
  color: #312e81;
}

.admin-audit-empty-cell {
  padding: 3rem 1.5rem;
  text-align: center;
  color: #6a5a53;
}

.admin-audit-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 50;
}

.admin-audit-modal {
  background: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
  max-width: 42rem;
  width: 100%;
  padding: 1.5rem;
}

.admin-audit-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.admin-audit-modal-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #2f231f;
}

.admin-audit-modal-close {
  color: #9ca3af;
  transition: color 0.2s ease;
}

.admin-audit-modal-close:hover {
  color: #4b5563;
}

.admin-audit-modal-content {
  display: grid;
  gap: 1rem;
}

.admin-audit-modal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  font-size: 0.875rem;
}

.admin-audit-modal-label {
  display: block;
  color: #6b7280;
}

.admin-audit-modal-label-payload {
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

.admin-audit-modal-value {
  font-weight: 500;
  color: #2f231f;
}

.admin-audit-json-box {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 0.75rem;
  overflow: auto;
  max-height: 24rem;
  position: relative;
}

.admin-audit-copy-json {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.25rem;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.25rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  opacity: 0;
  transition: opacity 0.2s ease, background-color 0.2s ease;
}

.admin-audit-json-box:hover .admin-audit-copy-json {
  opacity: 1;
}

.admin-audit-copy-json:hover {
  background: #f9fafb;
}

@media (min-width: 640px) {
  .admin-audit-header {
    flex-direction: row;
  }
}
</style>
