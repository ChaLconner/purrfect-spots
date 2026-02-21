<template>
  <div class="bg-white rounded-2xl shadow-sm border border-sand-100 overflow-hidden">
    <div
      class="p-6 border-b border-sand-100 flex flex-col sm:flex-row justify-between items-center gap-4"
    >
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-bold text-brown-900">User Reports</h2>
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
          Export CSV
        </button>
      </div>
      <div class="flex gap-2">
        <select
          v-model="statusFilter"
          class="pl-3 pr-10 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-700 bg-white"
          @change="loadReports(1)"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <select
          v-model="reasonFilter"
          class="pl-3 pr-10 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-700 bg-white"
          @change="loadReports(1)"
        >
          <option value="">All Reasons</option>
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
          <span class="text-xs font-medium text-terracotta-700">{{ selectedReportIds.length }} Selected</span>
          <button
            class="text-xs px-2 py-1 bg-white border border-terracotta-200 rounded hover:bg-terracotta-100 text-terracotta-700 font-medium"
            @click="openBulkActionModal('resolve')"
          >
            Resolve
          </button>
          <button
            class="text-xs px-2 py-1 bg-white border border-terracotta-200 rounded hover:bg-terracotta-100 text-terracotta-700 font-medium"
            @click="openBulkActionModal('dismiss')"
          >
            Dismiss
          </button>
        </div>
        <button
          class="p-2 rounded-lg border border-sand-300 hover:bg-sand-50 text-brown-500"
          title="Refresh"
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
        <thead class="bg-sand-50">
          <tr>
            <th class="px-6 py-3 w-10">
              <input
                type="checkbox"
                class="rounded border-sand-300 text-terracotta-600 focus:ring-terracotta-500"
                :checked="isAllSelected"
                @change="toggleSelectAll"
              />
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              Date
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              Reason
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              Content
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              Reporter
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
            >
              Status
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
          <tr v-for="report in reports" :key="report.id" class="hover:bg-sand-50 transition-colors">
            <td class="px-6 py-4 w-10">
              <input
                type="checkbox"
                class="rounded border-sand-300 text-terracotta-600 focus:ring-terracotta-500"
                :checked="selectedReportIds.includes(report.id)"
                @change="toggleSelection(report.id)"
              />
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-brown-500">
              {{ new Date(report.created_at).toLocaleDateString() }}<br />
              <span class="text-xs text-brown-400">{{
                new Date(report.created_at).toLocaleTimeString()
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
                {{ report.reason.replace('_', ' ') }}
              </span>
              <div
                v-if="report.details"
                class="mt-1 text-xs text-brown-500 max-w-xs truncate"
                :title="report.details"
              >
                "{{ report.details }}"
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <div
                  class="h-10 w-10 flex-shrink-0 cursor-pointer"
                  @click="openImage(report.photo?.image_url)"
                >
                  <img
                    v-if="report.photo?.image_url"
                    class="h-10 w-10 rounded-md object-cover border border-sand-200"
                    :src="report.photo.image_url"
                    alt="Reported content"
                  />
                  <div
                    v-else
                    class="h-10 w-10 bg-gray-200 rounded-md flex items-center justify-center text-xs text-gray-400"
                  >
                    Deleted
                  </div>
                </div>
                <div class="ml-4">
                  <a
                    :href="`/gallery/${report.photo_id}`"
                    target="_blank"
                    class="text-sm font-medium text-indigo-600 hover:text-indigo-900"
                  >
                    View <span class="sr-only">content</span>
                  </a>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-brown-600">
              {{ report.reporter?.email || 'Anonymous' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize"
                :class="{
                  'bg-yellow-100 text-yellow-800': report.status === 'pending',
                  'bg-green-100 text-green-800': report.status === 'resolved',
                  'bg-gray-100 text-gray-800': report.status === 'dismissed',
                }"
              >
                {{ report.status }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <div
                v-if="report.status === 'pending' && canManageReports"
                class="flex justify-end gap-2"
              >
                <button
                  class="text-green-600 hover:text-green-900"
                  title="Mark as Resolved"
                  @click="openActionModal(report, 'resolve')"
                >
                  Resolve
                </button>
                <button
                  class="text-gray-600 hover:text-gray-900"
                  title="Dismiss Report"
                  @click="openActionModal(report, 'dismiss')"
                >
                  Dismiss
                </button>
                <button
                  class="text-red-600 hover:text-red-900 ml-2"
                  title="Delete Content & Resolve"
                  @click="openActionModal(report, 'delete')"
                >
                  Delete Content
                </button>
              </div>
              <span v-else class="text-brown-400 text-xs"> No actions </span>
            </td>
          </tr>
          <tr v-if="reports.length === 0 && !isLoading">
            <td colspan="6" class="px-6 py-12 text-center text-brown-500">No reports found.</td>
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
        Previous
      </button>
      <span class="text-sm text-brown-600">Page {{ page }}</span>
      <button
        :disabled="reports.length < limit || page * limit >= totalReports"
        class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="loadReports(page + 1)"
      >
        Next
      </button>
    </div>

    <!-- Image Preview Modal -->
    <div
      v-if="previewImageUrl"
      class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center p-4 z-50 transition-opacity"
      @click="previewImageUrl = null"
    >
      <div class="relative">
        <img
          :src="previewImageUrl"
          class="max-w-full max-h-[90vh] rounded-lg shadow-2xl"
          alt="Preview"
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
              ? `Bulk ${actionType === 'delete' ? 'Delete & Resolve' : actionType === 'resolve' ? 'Resolve' : 'Dismiss'} (${selectedReportIds.length} Reports)`
              : actionType === 'delete'
                ? 'Delete Content & Resolve'
                : actionType === 'resolve'
                  ? 'Resolve Report'
                  : 'Dismiss Report'
          }}
        </h3>

        <div v-if="actionType === 'delete'" class="mb-4 text-sm text-red-600 font-medium">
          Warning: This content will be permanently deleted.
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-brown-700 mb-1">Standard Reason</label>
          <select
            v-model="selectedReason"
            class="w-full border border-sand-300 rounded-md shadow-sm p-2 focus:ring-terracotta-500 focus:border-terracotta-500"
          >
            <option value="">Select a reason...</option>
            <option v-for="reason in filteredReasons" :key="reason.value" :value="reason.label">
              {{ reason.label }}
            </option>
          </select>
        </div>

        <div class="mb-6">
          <label class="block text-sm font-medium text-brown-700 mb-1">Additional Notes (Optional)</label>
          <textarea
            v-model="resolutionNote"
            rows="3"
            class="w-full border border-sand-300 rounded-md shadow-sm p-2 focus:ring-terracotta-500 focus:border-terracotta-500"
            placeholder="Add specific details for the user..."
          ></textarea>
        </div>

        <div class="flex justify-end gap-3">
          <button
            class="px-4 py-2 border border-sand-300 rounded-md text-brown-700 hover:bg-sand-50"
            @click="closeActionModal"
          >
            Cancel
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
            Confirm
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { apiV1 } from '@/utils/api';
import { RESOLUTION_REASONS, REPORT_REASONS } from '@/constants/moderation';
import { useToast } from '@/components/toast/use-toast';
import { useAuthStore } from '@/store/authStore';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';

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

const reports = ref<Report[]>([]);
const totalReports = ref(0);
const statusFilter = ref('');
const reasonFilter = ref('');
const startDate = ref('');
const endDate = ref('');
const page = ref(1);
const limit = 20;
const isLoading = ref(false);
const previewImageUrl = ref<string | null>(null);
const selectedReportIds = ref<string[]>([]);
const isBulkAction = ref(false);

const isAllSelected = computed(() => {
  return reports.value.length > 0 && selectedReportIds.value.length === reports.value.length;
});

const toggleSelection = (id: string) => {
  if (selectedReportIds.value.includes(id)) {
    selectedReportIds.value = selectedReportIds.value.filter((item) => item !== id);
  } else {
    selectedReportIds.value.push(id);
  }
};

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedReportIds.value = [];
  } else {
    selectedReportIds.value = reports.value.map((r) => r.id);
  }
};

// Action Modal State
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
  selectedReport.value = reports.value.find((r) => r.id === selectedReportIds.value[0]) || null; // Just for context if needed, though bulk action ignores single report
  isBulkAction.value = true;
  actionType.value = type;
  selectedReason.value = 'Bulk Action'; // Default for bulk
  resolutionNote.value = '';
};

const closeActionModal = (): void => {
  selectedReport.value = null;
  isBulkAction.value = false;
  selectedReason.value = '';
  resolutionNote.value = '';
};

const exportReports = async (): Promise<void> => {
  try {
    const params = new URLSearchParams({ limit: '1000', offset: '0' });
    if (statusFilter.value) params.append('status', statusFilter.value);
    if (reasonFilter.value) params.append('reason', reasonFilter.value);
    if (startDate.value) params.append('start_date', startDate.value);
    if (endDate.value) params.append('end_date', endDate.value);

    const response = await apiV1.get<{ data: Report[]; total: number }>(
      `/admin/reports?${params.toString()}`
    );
    const data = response.data;

    if (!data || data.length === 0) {
      toast({ description: 'No reports to export', variant: 'default' });
      return;
    }

    const headers = ['ID', 'Date', 'Type', 'Status', 'Reporter', 'Details', 'Image URL'];
    const csvContent = [
      headers.join(','),
      ...data.map((r) =>
        [
          r.id,
          r.created_at,
          r.reason,
          r.status,
          r.reporter?.email || 'Anonymous',
          `"${(r.details || '').replace(/"/g, '""')}"`,
          r.photo?.image_url || '',
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `reports_export_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    toast({ description: 'Reports exported successfully', variant: 'success' });
  } catch (e) {
    console.error('Failed to export reports', e);
    toast({
      title: 'Error',
      description: 'Failed to export reports',
      variant: 'destructive',
    });
  }
};

const loadReports = async (newPage: number = 1): Promise<void> => {
  isLoading.value = true;
  try {
    const offset = (newPage - 1) * limit;
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (statusFilter.value) params.append('status', statusFilter.value);
    if (reasonFilter.value) params.append('reason', reasonFilter.value);
    if (startDate.value) params.append('start_date', startDate.value);
    if (endDate.value) params.append('end_date', endDate.value);

    const response = await apiV1.get<{ data: Report[]; total: number }>(
      `/admin/reports?${params.toString()}`
    );
    reports.value = response.data;
    totalReports.value = response.total;
    selectedReportIds.value = []; // Clear selection on new load
    page.value = newPage;
  } catch (e) {
    console.error('Failed to load reports', e);
  } finally {
    isLoading.value = false;
  }
};

const confirmAction = async (): Promise<void> => {
  if (!selectedReport.value || !selectedReason.value) return;

  const finalNote = resolutionNote.value
    ? `${selectedReason.value}: ${resolutionNote.value}`
    : selectedReason.value;

  try {
    if (isBulkAction.value) {
      // Bulk Action Logic
      await apiV1.post('/admin/reports/bulk', {
        report_ids: selectedReportIds.value,
        status: actionType.value === 'dismiss' ? 'dismissed' : 'resolved',
        resolution_notes: finalNote,
        delete_content: actionType.value === 'delete',
      });
      toast({
        description: `Successfully processed ${selectedReportIds.value.length} reports`,
        variant: 'default',
      });
      selectedReportIds.value = [];
    } else {
      // Single Action Logic
      if (actionType.value === 'delete') {
        // Resolve Report WITH Content Deletion (Atomic)
        await apiV1.put(`/admin/reports/${selectedReport.value.id}`, {
          status: 'resolved',
          resolution_notes: finalNote,
          delete_content: true,
        });
      } else {
        // Resolve or Dismiss
        await apiV1.put(`/admin/reports/${selectedReport.value.id}`, {
          status: actionType.value === 'dismiss' ? 'dismissed' : 'resolved',
          resolution_notes: finalNote,
        });
      }
      toast({
        description: 'Action completed successfully',
        variant: 'default',
      });
    }

    closeActionModal();
    loadReports(page.value);
  } catch (e) {
    console.error('Failed to perform action', e);
    toast({
      title: 'Error',
      description: 'Action failed. Please try again.',
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
