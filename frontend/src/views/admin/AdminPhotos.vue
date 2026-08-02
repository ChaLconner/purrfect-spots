<template>
  <div class="grid gap-4 font-body">
    <AdminPageHeader
      v-model="searchQuery"
      :title="t('admin.photos.title')"
      :subtitle="t('admin.photos.subtitle')"
      show-search
      :search-placeholder="t('admin.photos.search_placeholder')"
    />

    <div class="overflow-hidden border border-sand-200 rounded-xl bg-white shadow-sm">
      <div class="overflow-x-auto">
        <table class="min-w-full border-separate border-spacing-0">
          <thead class="bg-sand-50/85">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-[0.08em] border-b border-sand-200">
                {{ t('admin.photos.table.media') }}
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-[0.08em] border-b border-sand-200">
                {{ t('admin.photos.table.owner') }}
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-[0.08em] border-b border-sand-200">
                {{ t('admin.photos.table.location_profile') }}
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-[0.08em] border-b border-sand-200">
                {{ t('admin.photos.table.timeline') }}
              </th>
              <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-brown-500 uppercase tracking-[0.08em] border-b border-sand-200">
                {{ t('admin.photos.table.actions') }}
              </th>
            </tr>
          </thead>
          <tbody class="bg-white">
            <template v-if="!isLoading">
              <tr v-for="photo in photos" :key="photo.id" class="transition-colors hover:bg-sand-50/55">
                <td class="p-3 px-6 border-b border-[#f2ece8] align-middle whitespace-nowrap">
                  <div class="w-16 h-16 cursor-pointer" @click="previewImage = photo">
                    <OptimizedImage
                      class="w-16 h-16 rounded-xl border border-sand-200 shadow-sm transition-transform hover:scale-105"
                      :src="photo.image_url"
                      :alt="photo.location_name"
                      :width="64"
                      :height="64"
                    />
                  </div>
                </td>
                <td class="p-3 px-6 border-b border-[#f2ece8] align-middle">
                  <div class="flex flex-col">
                    <span class="text-sm font-medium text-brown-900">{{ photo.users?.name || t('social.anonymous') }}</span>
                    <span class="text-sm text-brown-500">{{ photo.users?.email || 'N/A' }}</span>
                  </div>
                </td>
                <td class="p-3 px-6 border-b border-[#f2ece8] align-middle">
                  <div v-if="editingPhotoId === photo.id" class="grid gap-2 max-w-xs">
                    <input v-model="editForm.location_name" type="text" class="w-full text-sm p-2 border border-sand-300 rounded-lg" />
                    <div class="flex gap-2">
                      <button class="text-xs px-3 py-1.5 rounded-lg font-semibold bg-[#c15f36] text-white" @click="saveEdit(photo)">{{ t('admin.photos.edit.save') }}</button>
                      <button class="text-xs px-3 py-1.5 rounded-lg font-semibold bg-sand-200 text-sand-700" @click="editingPhotoId = null">{{ t('admin.photos.edit.cancel') }}</button>
                    </div>
                  </div>
                  <div v-else class="flex flex-col">
                    <span class="text-sm font-medium text-brown-900">{{ photo.location_name }}</span>
                    <span class="text-sm text-brown-500 line-clamp-1">{{ photo.description }}</span>
                    <button v-if="canWrite" class="mt-1 text-sm font-medium text-terracotta-600 text-left" @click="startEdit(photo)">{{ t('common.edit') }}</button>
                  </div>
                </td>
                <td class="p-3 px-6 border-b border-[#f2ece8] align-middle whitespace-nowrap text-sm text-brown-500">
                  {{ formatTimestamp(photo.uploaded_at, locale) }}
                </td>
                <td class="p-3 px-6 border-b border-[#f2ece8] align-middle whitespace-nowrap text-right">
                  <div class="flex justify-end gap-2">
                    <a :href="`/gallery/${photo.id}`" target="_blank" class="p-2 text-[#b49b91] transition-colors hover:text-[#c15f36]">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                    <button v-if="canDelete" class="text-sm font-medium text-red-600 px-2 py-1" @click="confirmDelete(photo)">
                      {{ t('common.delete') }}
                    </button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-if="photos.length === 0 && !isLoading">
              <td colspan="5" class="p-16 px-6 text-center text-[#b49b91]">
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
      
      <div v-if="previewImage" class="fixed inset-0 bg-black/90 flex items-center justify-center p-4 z-50" @click="previewImage = null">
        <img :src="previewImage.image_url" class="max-w-full max-h-full rounded-lg shadow-2xl" />
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from '@/composables/useToast';
import { PERMISSIONS } from '@/constants/permissions';
import { useAdminTable } from '@/composables/useAdminTable';
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue';
import AdminPagination from '@/components/ui/AdminPagination.vue';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';
import { BaseConfirmModal, OptimizedImage } from '@/components/ui';
import { formatTimestamp } from '@/utils/date';

interface AdminPhoto {
  id: string;
  image_url: string;
  description: string;
  location_name: string;
  uploaded_at: string;
  users?: { email: string; name: string };
}

const { t, locale } = useI18n();
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

const fetchPhotos = (newPage: number = 1): void => {
  loadData(newPage, { search: searchQuery.value });
};

watch(searchQuery, () => fetchPhotos(1));
onMounted(() => fetchPhotos());

// Editing
const editingPhotoId = ref<string | null>(null);
const editForm = ref({ location_name: '', description: '' });
const startEdit = (photo: AdminPhoto): void => {
  editingPhotoId.value = photo.id;
  editForm.value = { location_name: photo.location_name, description: photo.description };
};
const saveEdit = async (photo: AdminPhoto): Promise<void> => {
  try {
    const updated = await apiV1.patch<Partial<AdminPhoto>>(`/admin/photos/${photo.id}`, editForm.value);
    photo.location_name = updated.location_name ?? photo.location_name;
    photo.description = updated.description ?? photo.description;
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

function handleLightboxKeydown(e: KeyboardEvent): void {
  if (!previewImage.value) return;
  if (e.key === 'Escape') {
    previewImage.value = null;
  } else if (e.key === 'ArrowLeft') {
    const idx = photos.value.findIndex((p) => p.id === previewImage.value?.id);
    if (idx > 0) {
      previewImage.value = photos.value[idx - 1];
    }
  } else if (e.key === 'ArrowRight') {
    const idx = photos.value.findIndex((p) => p.id === previewImage.value?.id);
    if (idx >= 0 && idx < photos.value.length - 1) {
      previewImage.value = photos.value[idx + 1];
    }
  }
}

watch(previewImage, (val) => {
  if (val) {
    window.addEventListener('keydown', handleLightboxKeydown);
  } else {
    window.removeEventListener('keydown', handleLightboxKeydown);
  }
});

const confirmDelete = (photo: AdminPhoto): void => {
  photoToDelete.value = photo;
  deleteConfirmOpen.value = true;
};
const executeDelete = async (): Promise<void> => {
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
