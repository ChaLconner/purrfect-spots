<template>
  <div class="admin-comments-page">
    <AdminPageHeader
      v-model="searchQuery"
      :title="t('admin.comments.title')"
      :subtitle="t('admin.comments.subtitle')"
      show-search
      :search-placeholder="t('admin.comments.search')"
    >
      <template #actions>
        <div class="admin-comments-toggle">
          <button
            class="admin-comments-toggle-button"
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
            class="admin-comments-toggle-button admin-comments-toggle-button-icon"
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
      class="admin-comments-bulk-bar"
    >
      <span class="admin-comments-bulk-count">
        {{ t('admin.comments.selected_count', { count: selectedCommentIds.length }) }}
      </span>
      <div class="admin-comments-bulk-actions">
        <button
          class="admin-comments-bulk-button admin-comments-bulk-button-danger"
          @click="bulkAction('delete')"
        >
          {{ t('admin.comments.bulk_delete') }}
        </button>
        <button
          class="admin-comments-bulk-button admin-comments-bulk-button-success"
          @click="bulkAction('dismiss')"
        >
          {{ t('admin.comments.bulk_dismiss') }}
        </button>
      </div>
    </div>

    <!-- Comments List -->
    <div class="admin-comments-shell">
      <!-- Loading State -->
      <div v-if="loading" class="admin-comments-loading">
        <div
          class="w-12 h-12 border-4 border-sand-100 border-t-terracotta-500 rounded-full animate-spin mb-6"
        ></div>
        <p class="text-sm text-brown-500">{{ t('common.loading') }}</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="comments.length === 0" class="admin-comments-empty-state">
        <div class="admin-comments-empty-icon">
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
        <h3 class="admin-comments-empty-title">
          {{ t('admin.comments.no_results') }}
        </h3>
        <p class="admin-comments-empty-copy">{{ t('admin.comments.no_results_desc') }}</p>
      </div>

      <!-- Scrollable Table -->
      <div v-else class="admin-comments-scroller-shell">
        <RecycleScroller
          v-slot="{ item: comment }"
          class="scroller h-full"
          :items="comments"
          :item-size="160"
          key-field="id"
        >
          <div
            class="admin-comment-row group/item"
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
                      <span class="admin-comment-email">
                        {{ comment.user_email || t('admin.comments.unknown_user') }}
                      </span>
                      <span
                        v-if="comment.is_user_banned"
                        class="admin-comment-banned-badge"
                      >
                        {{ t('admin.comments.banned_status') }}
                      </span>
                    </div>
                    <span class="admin-comment-timestamp">
                      {{ new Date(comment.created_at).toLocaleString() }}
                    </span>
                  </div>

                  <div
                    v-if="comment.report_count > 0"
                    class="admin-comment-report-pill"
                    @click="viewReports(comment)"
                  >
                    {{ t('admin.comments.reported') }} ({{ comment.report_count }})
                  </div>
                </div>
                <p class="admin-comment-content">
                  {{ comment.content }}
                </p>
              </div>

              <div class="admin-comment-actions">
                <button
                  v-if="!comment.is_user_banned"
                  class="admin-comment-link-action"
                  @click="handleBanUser(comment)"
                >
                  {{ t('admin.comments.ban_user') }}
                </button>

                <button
                  v-if="comment.report_count > 0"
                  class="admin-comment-solid-action admin-comment-solid-action-success"
                  @click="dismissReports(comment)"
                >
                  {{ t('admin.comments.dismiss') }}
                </button>

                <button
                  class="admin-comment-solid-action admin-comment-solid-action-danger"
                  @click="confirmDelete(comment)"
                >
                  {{ t('common.delete') }}
                </button>
              </div>
            </div>
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
import { ref, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { RecycleScroller } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import { apiV1 } from '@/utils/api';
import { useToast } from '@/components/toast/use-toast';
import { BaseConfirmModal } from '@/components/ui';
import AdminPagination from '@/components/ui/AdminPagination.vue';
import ActionModal from '@/components/ui/ActionModal.vue';
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue';
import { useAdminTable } from '@/composables/useAdminTable';

interface AdminComment {
  id: string;
  cat_photo_id: string;
  user_id: string;
  content: string;
  created_at: string;
  report_count: number;
  user_email: string | null;
  is_user_banned: boolean;
}

const { t } = useI18n();
const { toast } = useToast();

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
  limit: 100,
});

const fetchComments = (newPage: number = 1): void => {
  loadData(newPage, {
    search: searchQuery.value,
    reported_only: showReportedOnly.value ? 'true' : 'false',
  });
};

watch([searchQuery, showReportedOnly], () => fetchComments(1));

onMounted(() => fetchComments());

// Delete Logic
const deleteModalOpen = ref(false);
const commentToDelete = ref<AdminComment | null>(null);
const confirmDelete = (comment: AdminComment) => {
  commentToDelete.value = comment;
  deleteModalOpen.value = true;
};
const executeDelete = async () => {
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
const handleBanUser = (comment: AdminComment) => {
  commentToBan.value = comment;
  banConfirmOpen.value = true;
};
const executeBan = async () => {
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
const bulkAction = (type: 'delete' | 'dismiss') => {
  currentBulkType.value = type;
  bulkConfirmOpen.value = true;
};
const executeBulkAction = async () => {
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
const dismissReports = async (comment: AdminComment) => {
  try {
    await apiV1.put(`/admin/comments/${comment.id}/resolve`, {});
    toast({ description: t('admin.comments.dismiss_success'), variant: 'success' });
    fetchComments(currentPage.value);
  } catch {
    toast({ description: t('admin.comments.dismiss_error'), variant: 'destructive' });
  }
};

const viewReports = (comment: AdminComment) => {
  // Logic to view reports (can be a separate modal or redirect)
  console.log('View reports for:', comment.id);
};
</script>

<style scoped>
.admin-comments-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.admin-comments-toggle {
  display: flex;
  padding: 0.375rem;
  border: 1px solid rgba(245, 245, 244, 0.95);
  border-radius: 1rem;
  background: rgba(245, 245, 244, 0.5);
}

.admin-comments-toggle-button {
  padding: 0.5rem 1.25rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  transition: all 0.2s ease;
}

.admin-comments-toggle-button-icon {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.admin-comments-bulk-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border: 1px solid var(--color-terracotta-100, #f7ebe6);
  border-radius: 0.75rem;
  background: var(--color-terracotta-50, #fbf5f2);
  animation: fadeIn 0.2s ease;
}

.admin-comments-bulk-count {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-terracotta-900, #602f1a);
}

.admin-comments-bulk-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.admin-comments-bulk-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.admin-comments-bulk-button-danger {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;
}

.admin-comments-bulk-button-danger:hover {
  background: #ef4444;
  color: white;
}

.admin-comments-bulk-button-success {
  background: #f0fdf4;
  color: #16a34a;
  border-color: #bbf7d0;
}

.admin-comments-bulk-button-success:hover {
  background: #22c55e;
  color: white;
}

.admin-comments-shell {
  overflow: hidden;
  border: 1px solid var(--color-sand-200);
  border-radius: 0.75rem;
  background: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.admin-comments-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--color-brown-400, #a8a29e);
}

.admin-comments-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.admin-comments-empty-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 6rem;
  height: 6rem;
  margin-bottom: 1.5rem;
  border-radius: 9999px;
  background: var(--color-sand-50);
}

.admin-comments-empty-title {
  margin-bottom: 0.5rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-brown-800, #292524);
}

.admin-comments-empty-copy {
  max-width: 24rem;
  font-weight: 500;
  color: var(--color-brown-500, #78716c);
}

.admin-comments-scroller-shell {
  height: 700px;
}

.admin-comment-row {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(245, 245, 244, 0.95);
  transition: background-color 0.2s ease;
}

.admin-comment-row:hover {
  background: var(--color-sand-50);
}

.admin-comment-email {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-brown-900, #2d2420);
}

.admin-comment-banned-badge {
  padding: 0.125rem 0.5rem;
  border: 1px solid #fecaca;
  border-radius: 9999px;
  background: #fef2f2;
  color: #ef4444;
  font-size: 0.75rem;
  font-weight: 600;
}

.admin-comment-timestamp {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--color-brown-500, #78716c);
}

.admin-comment-report-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid #fecaca;
  border-radius: 9999px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s ease;
}

.admin-comment-report-pill:hover {
  background: #ef4444;
  color: white;
}

.admin-comment-content {
  font-size: 0.875rem;
  line-height: 1.6;
  font-weight: 500;
  color: var(--color-brown-700, #44403c);
  word-break: break-word;
}

.admin-comment-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(245, 245, 244, 0.95);
}

.admin-comment-link-action {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: 0.5rem;
  color: var(--color-brown-600, #57534e);
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.2s ease;
}

.admin-comment-link-action:hover {
  color: #dc2626;
}

.admin-comment-solid-action {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.admin-comment-solid-action-success {
  background: #f0fdf4;
  color: #16a34a;
  border-color: #bbf7d0;
}

.admin-comment-solid-action-success:hover {
  background: #22c55e;
  color: white;
}

.admin-comment-solid-action-danger {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;
}

.admin-comment-solid-action-danger:hover {
  background: #ef4444;
  color: white;
}

@media (min-width: 640px) {
  .admin-comment-row {
    flex-direction: row;
  }
}
</style>
