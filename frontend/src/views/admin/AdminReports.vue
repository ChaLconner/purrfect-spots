<template>
  <div class="bg-white rounded-xl shadow-sm border border-sand-100 overflow-hidden">
    <div
      class="p-4 border-b border-sand-100 flex flex-col sm:flex-row justify-between items-center gap-4"
    >
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-bold text-brown-900">{{ t('admin.reports.title') }}</h2>
        <button
          class="px-3 py-1.5 text-sm font-medium text-brown-600 bg-sand-50 border border-sand-200 rounded-lg hover:bg-sand-100 transition-colors flex items-center gap-2"
          @click="exportReports"
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
          {{ t('admin.reports.exportCsv') }}
        </button>
      </div>
      <div class="flex gap-2">
        <select
          v-model="statusFilter"
          class="pl-3 pr-10 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-700 bg-white"
          @change="loadReports(1)"
        >
          <option value="">{{ t('admin.reports.filters.allStatuses') }}</option>
          <option value="pending">{{ t('admin.reports.filters.pending') }}</option>
          <option value="resolved">{{ t('admin.reports.filters.resolved') }}</option>
          <option value="dismissed">{{ t('admin.reports.filters.dismissed') }}</option>
        </select>
        <select
          v-model="reasonFilter"
          class="pl-3 pr-10 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-700 bg-white"
          @change="loadReports(1)"
        >
          <option value="">{{ t('admin.reports.filters.allReasons') }}</option>
          <option v-for="reason in REPORT_REASONS" :key="reason.value" :value="reason.value">
            {{ reason.label }}
          </option>
        </select>
        <div class="flex items-center gap-2">
          <input
            v-model="startDate"
            type="date"
            class="pl-3 pr-3 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-700 bg-white text-sm"
            @change="loadReports(1)"
          />
          <span class="text-brown-400">-</span>
          <input
            v-model="endDate"
            type="date"
            class="pl-3 pr-3 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-700 bg-white text-sm"
            @change="loadReports(1)"
          />
        </div>
        <div
          v-if="selectedReportIds.length > 0 && canManageReports"
          class="flex items-center bg-terracotta-50 px-3 py-1.5 rounded-lg border border-terracotta-100 gap-2"
        >
          <span class="text-xs font-medium text-terracotta-700">
            {{ t('admin.reports.selectedCount', { count: selectedReportIds.length }) }}
          </span>
          <button
            class="text-xs px-2 py-1 bg-white border border-terracotta-200 rounded hover:bg-terracotta-100 text-terracotta-700 font-medium"
            @click="openBulkActionModal('resolve')"
          >
            {{ t('admin.reports.actions.resolve') }}
          </button>
          <button
            class="text-xs px-2 py-1 bg-white border border-terracotta-200 rounded hover:bg-terracotta-100 text-terracotta-700 font-medium"
            @click="openBulkActionModal('dismiss')"
          >
            {{ t('admin.reports.actions.dismiss') }}
          </button>
        </div>
        <button
          class="p-2 rounded-lg border border-sand-300 hover:bg-sand-50 text-brown-500"
          :title="t('common.refresh')"
          @click="loadReports(1)"
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
        <thead class="bg-sand-50/50">
          <tr>
            <th class="px-6 py-4 w-10">
              <input
                type="checkbox"
                class="w-4 h-4 rounded border-sand-300 text-terracotta-600 focus:ring-terracotta-500/20 transition-all cursor-pointer"
                :checked="isAllSelected"
                @change="toggleSelectAll"
              />
            </th>
            <th
              scope="col"
              class="px-6 py-2 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.15em]"
            >
              {{ t('admin.reports.table.timestamp') }}
            </th>
            <th
              scope="col"
              class="px-6 py-2 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.15em]"
            >
              {{ t('admin.reports.table.category') }}
            </th>
            <th
              scope="col"
              class="px-6 py-2 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.15em]"
            >
              {{ t('admin.reports.table.subject') }}
            </th>
            <th
              scope="col"
              class="px-6 py-2 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.15em]"
            >
              {{ t('admin.reports.table.author') }}
            </th>
            <th
              scope="col"
              class="px-6 py-2 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.15em]"
            >
              {{ t('admin.reports.table.status') }}
            </th>
            <th
              scope="col"
              class="px-6 py-2 text-right text-[10px] font-black text-brown-400 uppercase tracking-[0.15em]"
            >
              {{ t('admin.reports.table.controls') }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-sand-200">
          <tr v-for="report in reports" :key="report.id" class="hover:bg-sand-50 transition-colors">
            <td class="px-6 py-3 w-10">
              <input
                type="checkbox"
                class="rounded border-sand-300 text-terracotta-600 focus:ring-terracotta-500"
                :checked="selectedReportIds.includes(report.id)"
                @change="toggleSelection(report.id)"
              />
            </td>
            <td class="px-6 py-3 whitespace-nowrap text-sm text-brown-500">
              {{ new Date(report.created_at).toLocaleDateString(locale) }}<br />
              <span class="text-xs text-brown-400">{{
                new Date(report.created_at).toLocaleTimeString(locale)
              }}</span>
            </td>
            <td class="px-6 py-4">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize"
                :class="{
                  'bg-red-100 text-red-800': ['nudity', 'violence', 'harassment'].includes(
                    report.reason
                  ),
                  'bg-yellow-100 text-yellow-800': report.reason === 'spam',
                  'bg-gray-100 text-gray-800':
                    report.reason === 'other' || report.reason === 'not_a_cat',
                }"
              >
                {{ t('admin.reports.reasons.' + report.reason) }}
              </span>
              <div
                v-if="report.details"
                class="mt-1 text-xs text-brown-500 max-w-xs truncate"
                :title="report.details"
              >
                "{{ report.details }}"
              </div>
            </td>
            <td class="px-6 py-3 whitespace-nowrap">
              <div class="flex items-center">
                <div
                  class="h-10 w-10 flex-shrink-0 cursor-pointer"
                  @click="openImage(report.photo?.image_url)"
                >
                  <OptimizedImage
                    v-if="report.photo?.image_url"
                    class="h-10 w-10 rounded-md border border-sand-200"
                    :src="report.photo.image_url"
                    alt="Reported content"
                    :width="40"
                    :height="40"
                  />
                  <div
                    v-else
                    class="h-10 w-10 bg-gray-200 rounded-md flex items-center justify-center text-xs text-gray-400"
                  >
                    {{ t('admin.reports.table.deleted') }}
                  </div>
                </div>
                <div class="ml-4">
                  <a
                    :href="`/gallery/${report.photo_id}`"
                    target="_blank"
                    class="text-sm font-medium text-indigo-600 hover:text-indigo-900"
                  >
                    {{ t('admin.reports.table.view') }} <span class="sr-only">content</span>
                  </a>
                </div>
              </div>
            </td>
            <td class="px-6 py-3 whitespace-nowrap text-sm text-brown-600">
              {{ report.reporter?.email || t('admin.audit.unknown') }}
            </td>
            <td class="px-6 py-3 whitespace-nowrap">
              <span
                class="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider leading-none shadow-sm border"
                :class="{
                  'bg-yellow-50 text-yellow-700 border-yellow-100': report.status === 'pending',
                  'bg-green-50 text-green-700 border-green-100': report.status === 'resolved',
                  'bg-gray-50 text-gray-700 border-gray-100': report.status === 'dismissed',
                }"
              >
                {{ t('admin.reports.statuses.' + report.status) }}
              </span>
            </td>
            <td class="px-6 py-3 whitespace-nowrap text-right text-sm font-medium">
              <div
                v-if="report.status === 'pending' && canManageReports"
                class="flex justify-end gap-2"
              >
                <button
                  class="text-green-600 hover:text-green-900"
                  :title="t('admin.reports.actions.resolve')"
                  @click="openActionModal(report, 'resolve')"
                >
                  {{ t('admin.reports.actions.resolve') }}
                </button>
                <button
                  class="text-gray-600 hover:text-gray-900"
                  :title="t('admin.reports.actions.dismiss')"
                  @click="openActionModal(report, 'dismiss')"
                >
                  {{ t('admin.reports.actions.dismiss') }}
                </button>
                <button
                  class="text-red-600 hover:text-red-900 ml-2"
                  :title="t('admin.reports.actions.delete')"
                  @click="openActionModal(report, 'delete')"
                >
                  {{ t('admin.reports.actions.delete') }}
                </button>
              </div>
              <span v-else class="text-brown-400 text-xs">
                {{ t('admin.reports.actions.noActions') }}
              </span>
            </td>
          </tr>
          <tr v-if="reports.length === 0 && !isLoading">
            <td colspan="6" class="px-6 py-12 text-center text-brown-500">
              {{ t('admin.reports.table.noReports') }}
            </td>
          </tr>
          <TableSkeleton v-if="isLoading" :columns="7" :checkbox-column="1" :avatar-column="4" />
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="reports.length > 0"
      class="px-6 py-4 border-t border-sand-200 flex items-center justify-between"
    >
      <button
        :disabled="page === 1"
        class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="page > 1 && loadReports(page - 1)"
      >
        {{ t('common.previous') }}
      </button>
      <span class="text-sm text-brown-600">{{ t('common.page', { n: page }) }}</span>
      <button
        :disabled="reports.length < limit || page * limit >= totalReports"
        class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="loadReports(page + 1)"
      >
        {{ t('common.next') }}
      </button>
    </div>

    <!-- Image Preview Modal -->
    <div
      v-if="previewImageUrl"
      class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center p-4 z-50 transition-opacity"
      @click="previewImageUrl = null"
    >
      <div class="relative">
        <OptimizedImage
          :src="previewImageUrl"
          class="max-w-full max-h-[90vh] rounded-lg shadow-2xl"
          alt="Preview"
          :lazy="false"
        />
        <button
          class="absolute -top-4 -right-4 bg-white text-black rounded-full p-1 hover:text-gray-300 shadow-lg"
          @click.stop="previewImageUrl = null"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
    <!-- Resolution/Action Modal -->
    <div
      v-if="selectedReport"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 class="text-lg font-bold text-brown-900 mb-4">
          {{
            isBulkAction
              ? t('admin.reports.modal.bulkTitle', {
                  action: t(`admin.reports.modal.bulkLabel`, { action: actionType }),
                  count: selectedReportIds.length,
                })
              : actionType === 'delete'
                ? t('admin.reports.modal.deleteTitle')
                : actionType === 'resolve'
                  ? t('admin.reports.modal.resolveTitle')
                  : t('admin.reports.modal.dismissTitle')
          }}
        </h3>

        <div v-if="actionType === 'delete'" class="mb-4 text-sm text-red-600 font-medium">
          {{ t('admin.reports.modal.deleteWarning') }}
        </div>

        <div class="mb-4">
          <label for="resolution-reason" class="block text-sm font-medium text-brown-700 mb-1">{{
            t('admin.reports.modal.reasonLabel')
          }}</label>
          <select
            id="resolution-reason"
            v-model="selectedReason"
            class="w-full border border-sand-300 rounded-md shadow-sm p-2 focus:ring-terracotta-500 focus:border-terracotta-500"
          >
            <option value="">{{ t('admin.reports.modal.reasonPlaceholder') }}</option>
            <option v-for="reason in filteredReasons" :key="reason.value" :value="reason.value">
              {{ t('admin.reports.resolutionReasons.' + reason.value) }}
            </option>
          </select>
        </div>

        <div class="mb-6">
          <label for="resolution-note" class="block text-sm font-medium text-brown-700 mb-1">
            {{ t('admin.reports.modal.notesLabel') }}
          </label>
          <textarea
            id="resolution-note"
            v-model="resolutionNote"
            rows="3"
            class="w-full border border-sand-300 rounded-md shadow-sm p-2 focus:ring-terracotta-500 focus:border-terracotta-500"
            :placeholder="t('admin.reports.modal.notesPlaceholder')"
          ></textarea>
        </div>

        <div class="flex justify-end gap-3">
          <button
            class="px-4 py-2 border border-sand-300 rounded-md text-brown-700 hover:bg-sand-50"
            @click="closeActionModal"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            class="px-4 py-2 rounded-md text-white font-medium"
            :class="
              actionType === 'delete'
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-terracotta-600 hover:bg-terracotta-700'
            "
            :disabled="!selectedReason"
            @click="confirmAction"
          >
            {{ t('common.confirm') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { RESOLUTION_REASONS, REPORT_REASONS } from '@/constants/moderation';
import { useToast } from '@/components/toast/use-toast';
import { useAuthStore } from '@/store/authStore';
import { useAdminTable } from '@/composables/useAdminTable';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';
import { OptimizedImage } from '@/components/ui';

const { t, locale } = useI18n();
const { toast } = useToast();
const authStore = useAuthStore();

interface Report {
  id: string;
  photo_id: string;
  reporter_id: string;
  reason: string;
  details: string;
  status: 'pending' | 'resolved' | 'dismissed';
  created_at: string;
  photo?: {
    image_url: string;
    location_name: string;
  };
  reporter?: {
    email: string;
  };
}

const statusFilter = ref('');
const reasonFilter = ref('');
const startDate = ref('');
const endDate = ref('');
const previewImageUrl = ref<string | null>(null);

const {
  items: reports,
  totalItems: totalReports,
  page,
  limit,
  isLoading,
  selectedIds: selectedReportIds,
  isAllSelected,
  toggleSelection,
  toggleSelectAll,
  loadData,
  exportData,
} = useAdminTable<Report>({
  endpoint: '/admin/reports',
  exportHeaders: ['ID', 'Date', 'Type', 'Status', 'Reporter', 'Details', 'Image URL'],
  exportFileNamePrefix: 'reports_export',
  formatExportRow: (r) => [
    r.id,
    r.created_at,
    r.reason,
    r.status,
    r.reporter?.email || t('profile.unknownUser'),
    `"${(r.details || '').replace(/"/g, '""')}"`,
    r.photo?.image_url || '',
  ],
  limit: 50,
});

const loadReports = (newPage: number = 1): void => {
  loadData(newPage, {
    status: statusFilter.value,
    reason: reasonFilter.value,
    start_date: startDate.value,
    end_date: endDate.value,
  });
};

const exportReports = (): void => {
  exportData({
    status: statusFilter.value,
    reason: reasonFilter.value,
    start_date: startDate.value,
    end_date: endDate.value,
  });
};

// Action Modal State
const isBulkAction = ref(false);
const selectedReport = ref<Report | null>(null);
const actionType = ref<'resolve' | 'dismiss' | 'delete'>('resolve');
const selectedReason = ref('');
const resolutionNote = ref('');

const filteredReasons = computed(() => {
  const typeFilter = actionType.value === 'dismiss' ? 'dismissed' : 'resolved';
  return RESOLUTION_REASONS.filter((r) => r.type === typeFilter);
});

const canManageReports = authStore.hasPermission('content:delete');

const openActionModal = (report: Report, type: 'resolve' | 'dismiss' | 'delete'): void => {
  if (!canManageReports) return;
  selectedReport.value = report;
  isBulkAction.value = false;
  actionType.value = type;
  selectedReason.value = '';
  resolutionNote.value = '';
};

const openBulkActionModal = (type: 'resolve' | 'dismiss' | 'delete'): void => {
  if (!canManageReports || selectedReportIds.value.length === 0) return;
  selectedReport.value = reports.value.find((r) => r.id === selectedReportIds.value[0]) || null;
  isBulkAction.value = true;
  actionType.value = type;
  selectedReason.value = 'Bulk Action';
  resolutionNote.value = '';
};

const closeActionModal = (): void => {
  selectedReport.value = null;
  isBulkAction.value = false;
  selectedReason.value = '';
  resolutionNote.value = '';
};

const confirmAction = async (): Promise<void> => {
  if (!selectedReport.value || !selectedReason.value) return;

  const finalNote = resolutionNote.value
    ? `${t('admin.reports.resolutionReasons.' + selectedReason.value)}: ${resolutionNote.value}`
    : t('admin.reports.resolutionReasons.' + selectedReason.value);

  try {
    if (isBulkAction.value) {
      await apiV1.post('/admin/reports/bulk', {
        report_ids: selectedReportIds.value,
        status: actionType.value === 'dismiss' ? 'dismissed' : 'resolved',
        resolution_notes: finalNote,
        delete_content: actionType.value === 'delete',
      });
      toast({
        description: t('admin.reports.actions.bulkSuccess', {
          count: selectedReportIds.value.length,
        }),
        variant: 'default',
      });
    } else {
      if (actionType.value === 'delete') {
        await apiV1.put(`/admin/reports/${selectedReport.value.id}`, {
          status: 'resolved',
          resolution_notes: finalNote,
          delete_content: true,
        });
      } else {
        await apiV1.put(`/admin/reports/${selectedReport.value.id}`, {
          status: actionType.value === 'dismiss' ? 'dismissed' : 'resolved',
          resolution_notes: finalNote,
        });
      }
      toast({
        description: t('admin.reports.actions.success'),
        variant: 'default',
      });
    }

    closeActionModal();
    loadReports(page.value);
  } catch (e) {
    console.error('Failed to perform action', e);
    toast({
      title: t('common.error'),
      description: t('admin.reports.actions.failed'),
      variant: 'destructive',
    });
  }
};

const openImage = (url?: string): void => {
  if (url) previewImageUrl.value = url;
};

onMounted(() => {
  loadReports();
});
</script>
