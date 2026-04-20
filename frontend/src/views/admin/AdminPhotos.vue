<template>
  <div class="admin-photos-page">
    <AdminPageHeader
      v-model="searchQuery"
      :title="t('admin.photos.title')"
      :subtitle="t('admin.photos.subtitle')"
      show-search
      :search-placeholder="t('admin.photos.search_placeholder')"
    />

    <div class="admin-photos-card">
      <div class="admin-table-scroll">
        <table class="admin-photos-table">
          <thead class="admin-photos-table-head">
            <tr>
              <th scope="col" class="admin-photos-head-cell">
                {{ t('admin.photos.table.media') }}
              </th>
              <th scope="col" class="admin-photos-head-cell">
                {{ t('admin.photos.table.owner') }}
              </th>
              <th scope="col" class="admin-photos-head-cell">
                {{ t('admin.photos.table.location_profile') }}
              </th>
              <th scope="col" class="admin-photos-head-cell">
                {{ t('admin.photos.table.timeline') }}
              </th>
              <th scope="col" class="admin-photos-head-cell admin-photos-head-cell-right">
                {{ t('admin.photos.table.actions') }}
              </th>
            </tr>
          </thead>
          <tbody class="admin-photos-table-body">
            <template v-if="!isLoading">
              <tr v-for="photo in photos" :key="photo.id" class="admin-photos-row">
                <td class="admin-photos-cell admin-photos-cell-media">
                  <div class="admin-photo-thumb-wrap" @click="previewImage = photo">
                    <OptimizedImage
                      class="admin-photo-thumb"
                      :src="photo.image_url"
                      :alt="photo.location_name"
                      :width="64"
                      :height="64"
                    />
                  </div>
                </td>
                <td class="admin-photos-cell">
                  <div class="admin-photo-owner">
                    <span class="admin-photo-owner-name">{{ photo.users?.name || t('social.anonymous') }}</span>
                    <span class="admin-photo-owner-email">{{ photo.users?.email || 'N/A' }}</span>
                  </div>
                </td>
                <td class="admin-photos-cell">
                  <div v-if="editingPhotoId === photo.id" class="admin-photo-edit-form">
                    <input v-model="editForm.location_name" type="text" class="admin-photo-edit-input" />
                    <div class="admin-photo-edit-actions">
                      <button class="admin-photo-save-button" @click="saveEdit(photo)">{{ t('admin.photos.edit.save') }}</button>
                      <button class="admin-photo-cancel-button" @click="editingPhotoId = null">{{ t('admin.photos.edit.cancel') }}</button>
                    </div>
                  </div>
                  <div v-else class="admin-photo-location-block">
                    <span class="admin-photo-location-name">{{ photo.location_name }}</span>
                    <span class="admin-photo-location-description">{{ photo.description }}</span>
                    <button v-if="canWrite" class="admin-photo-edit-trigger" @click="startEdit(photo)">{{ t('common.edit') }}</button>
                  </div>
                </td>
                <td class="admin-photos-cell admin-photos-cell-date">
                  {{ new Date(photo.uploaded_at).toLocaleDateString() }}
                </td>
                <td class="admin-photos-cell admin-photos-cell-actions">
                  <div class="admin-photo-actions">
                    <a :href="`/gallery/${photo.id}`" target="_blank" class="admin-photo-link">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                    <button v-if="canDelete" class="admin-photo-delete-button" @click="confirmDelete(photo)">
                      {{ t('common.delete') }}
                    </button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-if="photos.length === 0 && !isLoading">
              <td colspan="5" class="admin-photos-empty">
                {{ t('admin.photos.no_photos') }}
              </td>
            </tr>
            <TableSkeleton v-if="isLoading" :columns="5" :avatar-column="1" />
          </tbody>
        </table>
      </div>

      <AdminPagination
        v-model:page="currentPage"
        :limit="limit"
        :total-items="totalItems"
        :items-length="photos.length"
        @update:page="fetchPhotos"
      />
    </div>

    <!-- Modals -->
    <Teleport to="body">
      <BaseConfirmModal
        :is-open="deleteConfirmOpen"
        :title="t('admin.photos.delete.title')"
        :message="t('admin.photos.delete.confirm', { location: photoToDelete?.location_name })"
        confirm-text="Delete"
        variant="danger"
        @close="deleteConfirmOpen = false"
        @confirm="executeDelete"
      />
      
      <div v-if="previewImage" class="admin-photo-preview-overlay" @click="previewImage = null">
        <img :src="previewImage.image_url" class="admin-photo-preview-image" />
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/components/toast/use-toast';
import { PERMISSIONS } from '@/constants/permissions';
import { useAdminTable } from '@/composables/useAdminTable';
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue';
import AdminPagination from '@/components/ui/AdminPagination.vue';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';
import { BaseConfirmModal, OptimizedImage } from '@/components/ui';

interface AdminPhoto {
  id: string;
  image_url: string;
  description: string;
  location_name: string;
  uploaded_at: string;
  users?: { email: string; name: string };
}

const { t } = useI18n();
const { toast } = useToast();
const authStore = useAuthStore();

const searchQuery = ref('');
const canWrite = computed(() => authStore.hasPermission(PERMISSIONS.CONTENT_WRITE) || authStore.isAdmin);
const canDelete = computed(() => authStore.hasPermission(PERMISSIONS.CONTENT_DELETE) || authStore.isAdmin);

const {
  items: photos,
  totalItems,
  page: currentPage,
  limit,
  isLoading,
  loadData,
} = useAdminTable<AdminPhoto>({
  endpoint: '/admin/photos',
  exportHeaders: ['ID', 'Location', 'User', 'Uploaded At'],
  exportFileNamePrefix: 'photos_export',
  formatExportRow: (p) => [p.id, p.location_name, p.users?.email || 'N/A', p.uploaded_at],
  limit: 50,
});

const fetchPhotos = (newPage: number = 1) => {
  loadData(newPage, { search: searchQuery.value });
};

watch(searchQuery, () => fetchPhotos(1));
onMounted(() => fetchPhotos());

// Editing
const editingPhotoId = ref<string | null>(null);
const editForm = ref({ location_name: '', description: '' });
const startEdit = (photo: AdminPhoto) => {
  editingPhotoId.value = photo.id;
  editForm.value = { location_name: photo.location_name, description: photo.description };
};
const saveEdit = async (photo: AdminPhoto) => {
  try {
    const updated = await apiV1.patch(`/admin/photos/${photo.id}`, editForm.value);
    photo.location_name = updated.location_name;
    photo.description = updated.description;
    editingPhotoId.value = null;
    toast({ description: t('admin.photos.edit.success'), variant: 'success' });
  } catch {
    toast({ description: t('admin.photos.edit.error'), variant: 'destructive' });
  }
};

// Delete
const deleteConfirmOpen = ref(false);
const photoToDelete = ref<AdminPhoto | null>(null);
const previewImage = ref<AdminPhoto | null>(null);
const confirmDelete = (photo: AdminPhoto) => {
  photoToDelete.value = photo;
  deleteConfirmOpen.value = true;
};
const executeDelete = async () => {
  if (!photoToDelete.value) return;
  try {
    await apiV1.delete(`/admin/photos/${photoToDelete.value.id}`);
    toast({ description: t('admin.photos.delete.success'), variant: 'success' });
    deleteConfirmOpen.value = false;
    fetchPhotos(currentPage.value);
  } catch {
    toast({ description: t('admin.photos.delete.error'), variant: 'destructive' });
  }
};
</script>

<style scoped>
.admin-photos-page {
  display: grid;
  gap: 1rem;
}

.admin-photos-card {
  background: #fff;
  border-radius: 0.75rem;
  border: 1px solid #e7e5e4;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.admin-table-scroll {
  overflow-x: auto;
}

.admin-photos-table {
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.admin-photos-table-head {
  background: rgba(250, 248, 245, 0.85);
}

.admin-photos-head-cell {
  padding: 0.75rem 1.5rem;
  text-align: left;
  font-size: 10px;
  font-weight: 900;
  color: #b49b91;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  border-bottom: 1px solid #e7e5e4;
}

.admin-photos-head-cell-right {
  text-align: right;
}

.admin-photos-table-body {
  background: #fff;
}

.admin-photos-row {
  transition: background-color 0.2s ease;
}

.admin-photos-row:hover {
  background: rgba(250, 248, 245, 0.55);
}

.admin-photos-cell {
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid #f2ece8;
  vertical-align: middle;
}

.admin-photos-cell-media,
.admin-photos-cell-date,
.admin-photos-cell-actions {
  white-space: nowrap;
}

.admin-photos-cell-date {
  font-size: 0.75rem;
  color: #b49b91;
}

.admin-photos-cell-actions {
  text-align: right;
}

.admin-photo-thumb-wrap {
  width: 4rem;
  height: 4rem;
  cursor: pointer;
}

.admin-photo-thumb {
  width: 4rem;
  height: 4rem;
  border-radius: 0.75rem;
  border: 1px solid #e7e5e4;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s ease;
}

.admin-photo-thumb-wrap:hover .admin-photo-thumb {
  transform: scale(1.05);
}

.admin-photo-owner {
  display: flex;
  flex-direction: column;
}

.admin-photo-owner-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: #2f231f;
}

.admin-photo-owner-email {
  font-size: 10px;
  color: #b49b91;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.admin-photo-edit-form {
  display: grid;
  gap: 0.5rem;
  max-width: 20rem;
}

.admin-photo-edit-input {
  width: 100%;
  font-size: 0.875rem;
  padding: 0.5rem;
  border: 1px solid #d6d3d1;
  border-radius: 0.5rem;
}

.admin-photo-edit-actions {
  display: flex;
  gap: 0.5rem;
}

.admin-photo-save-button,
.admin-photo-cancel-button {
  font-size: 0.75rem;
  padding: 0.375rem 0.75rem;
  border-radius: 0.5rem;
  font-weight: 600;
}

.admin-photo-save-button {
  background: #c15f36;
  color: #fff;
}

.admin-photo-cancel-button {
  background: #e7e5e4;
  color: #44403c;
}

.admin-photo-location-block {
  display: flex;
  flex-direction: column;
}

.admin-photo-location-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: #2f231f;
}

.admin-photo-location-description {
  font-size: 0.75rem;
  color: #6a5a53;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.admin-photo-edit-trigger {
  margin-top: 0.25rem;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: #d07849;
}

.admin-photo-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.admin-photo-link {
  padding: 0.5rem;
  color: #b49b91;
  transition: color 0.2s ease;
}

.admin-photo-link:hover {
  color: #c15f36;
}

.admin-photo-delete-button {
  font-size: 0.75rem;
  font-weight: 700;
  color: #dc2626;
  padding: 0.25rem 0.5rem;
}

.admin-photos-empty {
  padding: 4rem 1.5rem;
  text-align: center;
  color: #b49b91;
}

.admin-photo-preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 50;
}

.admin-photo-preview-image {
  max-width: 100%;
  max-height: 100%;
  border-radius: 0.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
}
</style>
