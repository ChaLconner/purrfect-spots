<template>
  <div class="flex flex-col gap-4">
    <AdminPageHeader
      v-model="searchQuery"
      :title="t('admin.comments.title')"
      :subtitle="t('admin.comments.subtitle')"
      show-search
      :search-placeholder="t('admin.comments.search')"
    >
      <template #actions>
        <div class="flex p-1.5 border border-sand-200/95 rounded-2xl bg-sand-100/50">
          <button
            class="px-5 py-2 rounded-lg text-xs font-medium uppercase tracking-[0.08em] transition-all"
            :class="
              !showReportedOnly
                ? 'bg-white text-terracotta-600 shadow-sm'
                : 'text-brown-400 hover:text-brown-600'
            "
            @click="showReportedOnly = false"
          >
            {{ t('admin.comments.all') }}
          </button>
          <button
            class="inline-flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-medium uppercase tracking-[0.08em] transition-all"
            :class="
              showReportedOnly
                ? 'bg-white text-terracotta-600 shadow-sm'
                : 'text-brown-400 hover:text-brown-600'
            "
            @click="showReportedOnly = true"
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
                d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"
              />
            </svg>
            {{ t('admin.comments.reported') }}
          </button>
        </div>
      </template>
    </AdminPageHeader>

    <!-- Bulk Actions -->
    <div
      v-if="selectedCommentIds.length > 0"
      class="flex items-center justify-between p-4 border border-terracotta-100 rounded-xl bg-terracotta-50 animate-fadeIn"
    >
      <span class="text-sm font-bold text-terracotta-900">
        {{ t('admin.comments.selected_count', { count: selectedCommentIds.length }) }}
      </span>
      <div class="flex items-center gap-3">
        <button
          class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium transition-all bg-red-50 text-red-600 border-red-200 hover:bg-red-500 hover:text-white"
          @click="bulkAction('delete')"
        >
          {{ t('admin.comments.bulk_delete') }}
        </button>
        <button
          class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium transition-all bg-green-50 text-green-600 border-green-200 hover:bg-green-500 hover:text-white"
          @click="bulkAction('dismiss')"
        >
          {{ t('admin.comments.bulk_dismiss') }}
        </button>
      </div>
    </div>

    <!-- Comments List -->
    <div class="overflow-hidden border border-sand-200 rounded-xl bg-white shadow-sm">
      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center p-12 text-brown-400">
        <div
          class="w-12 h-12 border-4 border-sand-100 border-t-terracotta-500 rounded-full animate-spin mb-6"
        ></div>
        <p class="text-sm text-brown-500">{{ t('common.loading') }}</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="comments.length === 0" class="flex flex-col items-center justify-center p-12 text-center">
        <div class="flex items-center justify-center w-24 h-24 mb-6 rounded-full bg-sand-50">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-12 w-12 text-sand-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
        <h3 class="mb-2 text-xl font-bold text-brown-800">
          {{ t('admin.comments.no_results') }}
        </h3>
        <p class="max-w-sm font-medium text-brown-500">{{ t('admin.comments.no_results_desc') }}</p>
      </div>

      <!-- Scrollable Table -->
      <div v-else class="h-[700px]">
        <RecycleScroller
          v-slot="{ item: comment }"
          class="scroller h-full"
          :items="comments"
          :item-size="160"
          key-field="id"
        >
          <div
            class="relative flex flex-col sm:flex-row gap-6 p-4 px-6 border-b border-sand-200/95 transition-colors hover:bg-sand-50"
            :class="selectedCommentIds.includes(comment.id) ? 'bg-terracotta-50/30' : ''"
          >
            <!-- Checkbox -->
            <div class="flex-shrink-0 pt-1.5">
              <input
                type="checkbox"
                class="w-5 h-5 rounded-lg border-sand-200 text-terracotta-500 focus:ring-terracotta-400/20 focus:ring-offset-0 cursor-pointer transition-all bg-sand-50"
                :checked="selectedCommentIds.includes(comment.id)"
                @change="toggleSelection(comment.id)"
              />
            </div>

            <!-- Content -->
            <div class="flex-1 flex flex-col justify-between min-w-0">
              <div>
                <div class="flex flex-wrap items-center gap-2 mb-2">
                  <div class="flex flex-col flex-1 min-w-[200px]">
                    <div class="flex items-center gap-2">
                      <span class="overflow-hidden text-ellipsis whitespace-nowrap text-sm font-medium text-brown-900">
                        {{ comment.user_email || t('admin.comments.unknown_user') }}
                      </span>
                      <span
                        v-if="comment.is_user_banned"
                        class="px-2 py-0.5 border border-red-200 rounded-full bg-red-50 text-red-500 text-xs font-semibold"
                      >
                        {{ t('admin.comments.banned_status') }}
                      </span>
                    </div>
                  </div>

                  <div
                    v-if="comment.report_count > 0"
                    class="inline-flex items-center gap-2 px-3 py-1.5 border border-red-200 rounded-full bg-red-50 text-red-600 text-xs font-semibold whitespace-nowrap cursor-pointer transition-all hover:bg-red-500 hover:text-white"
                    @click="viewReports(comment)"
                  >
                    {{ t('admin.comments.reported') }} ({{ comment.report_count }})
                  </div>
                </div>
                <p class="text-sm leading-relaxed font-medium text-brown-700 break-words">
                  {{ comment.content }}
                </p>
              </div>

              <div class="flex items-center justify-end gap-2 mt-4 pt-2 border-t border-sand-200/95">
                <button
                  v-if="!comment.is_user_banned"
                  class="inline-flex items-center gap-2 rounded-lg text-sm font-medium text-brown-600 transition-colors hover:text-red-600"
                  @click="handleBanUser(comment)"
                >
                  {{ t('admin.comments.ban_user') }}
                </button>

                <button
                  v-if="comment.report_count > 0"
                  class="inline-flex items-center gap-2 px-3 py-1.5 border rounded-lg text-sm font-medium transition-all bg-green-50 text-green-600 border-green-200 hover:bg-green-500 hover:text-white"
                  @click="dismissReports(comment)"
                >
                  {{ t('admin.comments.dismiss') }}
                </button>

                <button
                  class="inline-flex items-center gap-2 px-3 py-1.5 border rounded-lg text-sm font-medium transition-all bg-red-50 text-red-600 border-red-200 hover:bg-red-500 hover:text-white"
                  @click="confirmDelete(comment)"
                >
                  {{ t('common.delete') }}
                </button>
              </div>
            </div>

            <span class="absolute top-4 right-6 text-xs font-medium text-brown-500 opacity-80">
              {{ formatTimestampWithLocale(comment.created_at) }}
            </span>
          </div>
        </RecycleScroller>
      </div>

      <!-- Pagination -->
      <AdminPagination
        v-model:page="currentPage"
        :limit="limit"
        :total-items="totalItems"
        :items-length="comments.length"
        @update:page="fetchComments"
      />
    </div>

    <!-- Modals -->
    <Teleport to="body">
      <!-- Delete Modal -->
      <ActionModal
        v-model="deleteModalOpen"
        :title="t('admin.comments.delete_confirm')"
        :confirm-text="t('common.delete')"
        confirm-button-class="bg-red-600 hover:bg-red-700"
        @confirm="executeDelete"
      >
        <p class="text-sm text-brown-600 mb-4">{{ t('admin.comments.delete_desc') }}</p>
        <div class="bg-sand-50 rounded-lg p-4 italic text-sm text-brown-700">
          "{{ commentToDelete?.content }}"
        </div>
      </ActionModal>

      <!-- Ban Confirm Modal -->
      <BaseConfirmModal
        :is-open="banConfirmOpen"
        :title="t('admin.comments.ban_user')"
        :message="t('admin.comments.ban_confirm')"
        :confirm-text="t('admin.comments.ban_user')"
        variant="danger"
        :is-loading="banning"
        @close="banConfirmOpen = false"
        @confirm="executeBan"
      />

      <!-- Bulk Action Modal -->
      <BaseConfirmModal
        :is-open="bulkConfirmOpen"
        :title="currentBulkType === 'delete' ? t('admin.comments.bulk_delete') : t('admin.comments.bulk_dismiss')"
        :message="t(`admin.comments.bulk_${currentBulkType}_confirm`, { count: selectedCommentIds.length })"
        variant="danger"
        :is-loading="bulkProcessing"
        @close="bulkConfirmOpen = false"
        @confirm="executeBulkAction"
      />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { RecycleScroller } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import { apiV1 } from '@/utils/api';
import { useToast } from '@/composables/useToast';
import { BaseConfirmModal } from '@/components/ui';
import AdminPagination from '@/components/ui/AdminPagination.vue';
import ActionModal from '@/components/ui/ActionModal.vue';
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue';
import { useAdminTable } from '@/composables/useAdminTable';
import { formatTimestamp } from '@/utils/date';

interface AdminComment {
  id: string;
  user_id: string;
  content: string;
  created_at: string;
  report_count: number;
  user_email: string | null;
  is_user_banned: boolean;
}

const { t } = useI18n();
const { toast } = useToast();
const router = useRouter();

// Local formatTimestamp removed, using imported one with locale
const formatTimestampWithLocale = (date: string): string => formatTimestamp(date, useI18n().locale.value);

const searchQuery = ref('');
const showReportedOnly = ref(false);

const {
  items: comments,
  totalItems,
  page: currentPage,
  limit,
  isLoading: loading,
  selectedIds: selectedCommentIds,
  toggleSelection,
  loadData,
} = useAdminTable<AdminComment>({
  endpoint: '/admin/comments',
  exportHeaders: ['ID', 'User', 'Content', 'Reports', 'Created At'],
  exportFileNamePrefix: 'comments_export',
  formatExportRow: (c) => [c.id, c.user_email || 'N/A', c.content, c.report_count.toString(), c.created_at],
  limit: 50,
  exportMaxRows: 1000,
  exportConcurrentBatches: 2,
});

const fetchComments = (newPage: number = 1): void => {
  loadData(newPage, {
    search: searchQuery.value,
    reported_only: showReportedOnly.value ? 'true' : 'false',
  });
};

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null;
watch(searchQuery, () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => fetchComments(1), 300);
});
watch(showReportedOnly, () => fetchComments(1));

onMounted(() => fetchComments());
onUnmounted(() => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
  searchDebounceTimer = null;
});

// Delete Logic
const deleteModalOpen = ref(false);
const commentToDelete = ref<AdminComment | null>(null);
const confirmDelete = (comment: AdminComment): void => {
  commentToDelete.value = comment;
  deleteModalOpen.value = true;
};
const executeDelete = async (): Promise<void> => {
  if (!commentToDelete.value) return;
  try {
    await apiV1.delete(`/admin/comments/${commentToDelete.value.id}`);
    toast({ description: t('admin.comments.delete_success'), variant: 'success' });
    deleteModalOpen.value = false;
    fetchComments(currentPage.value);
  } catch {
    toast({ description: t('admin.comments.delete_error'), variant: 'destructive' });
  }
};

// Ban Logic
const banConfirmOpen = ref(false);
const commentToBan = ref<AdminComment | null>(null);
const banning = ref(false);
const handleBanUser = (comment: AdminComment): void => {
  commentToBan.value = comment;
  banConfirmOpen.value = true;
};
const executeBan = async (): Promise<void> => {
  if (!commentToBan.value) return;
  banning.value = true;
  try {
    await apiV1.post(`/admin/comments/${commentToBan.value.id}/ban-user`, {});
    toast({ description: t('admin.comments.user_banned'), variant: 'success' });
    banConfirmOpen.value = false;
    fetchComments(currentPage.value);
  } finally {
    banning.value = false;
  }
};

// Bulk Actions
const bulkConfirmOpen = ref(false);
const currentBulkType = ref<'delete' | 'dismiss'>('delete');
const bulkProcessing = ref(false);
const bulkAction = (type: 'delete' | 'dismiss'): void => {
  currentBulkType.value = type;
  bulkConfirmOpen.value = true;
};
const executeBulkAction = async (): Promise<void> => {
  bulkProcessing.value = true;
  try {
    const endpoint = currentBulkType.value === 'delete' ? '/admin/comments/bulk-delete' : '/admin/comments/bulk-resolve';
    await apiV1.post(endpoint, { comment_ids: selectedCommentIds.value });
    toast({ description: t('admin.comments.bulk_action_success'), variant: 'success' });
    bulkConfirmOpen.value = false;
    selectedCommentIds.value = [];
    fetchComments(1);
  } finally {
    bulkProcessing.value = false;
  }
};

// Dismiss Reports
const dismissReports = async (comment: AdminComment): Promise<void> => {
  try {
    await apiV1.put(`/admin/comments/${comment.id}/resolve`, {});
    toast({ description: t('admin.comments.dismiss_success'), variant: 'success' });
    fetchComments(currentPage.value);
  } catch {
    toast({ description: t('admin.comments.dismiss_error'), variant: 'destructive' });
  }
};

const viewReports = (comment: AdminComment): void => {
  void router.push({
    name: 'AdminReports',
    query: {
      status: 'pending',
      source: 'comments',
      commentId: comment.id,
    },
  });
};
</script>
