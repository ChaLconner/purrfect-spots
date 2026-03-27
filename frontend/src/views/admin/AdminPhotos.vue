<template>
  <div class="bg-white rounded-2xl shadow-sm border border-sand-200 overflow-hidden">
    <div
      class="p-6 border-b border-sand-100 flex flex-col sm:flex-row justify-between items-center gap-4 bg-white"
    >
      <div>
        <h2 class="text-xl font-bold text-brown-900">{{ $t('admin.photos.title') }}</h2>
        <p class="text-sm text-brown-500">{{ $t('admin.photos.subtitle') }}</p>
      </div>
      <div class="relative max-w-xs w-full">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="$t('admin.photos.search_placeholder')"
          class="w-full pl-10 pr-4 py-2 border border-sand-300 rounded-xl focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 transition-colors text-brown-900 bg-sand-50/50"
          @input="handleSearch"
        />
        <div class="absolute left-3 top-1/2 -translate-y-1/2 text-brown-400">
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
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-sand-200">
        <thead class="bg-sand-50/50">
          <tr>
            <th
              scope="col"
              class="px-6 py-4 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.2em]"
            >
              {{ $t('admin.photos.table.media') }}
            </th>
            <th
              scope="col"
              class="px-6 py-4 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.2em]"
            >
              {{ $t('admin.photos.table.owner') }}
            </th>
            <th
              scope="col"
              class="px-6 py-4 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.2em]"
            >
              {{ $t('admin.photos.table.location_profile') }}
            </th>
            <th
              scope="col"
              class="px-6 py-4 text-left text-[10px] font-black text-brown-400 uppercase tracking-[0.2em]"
            >
              {{ $t('admin.photos.table.timeline') }}
            </th>
            <th
              scope="col"
              class="px-6 py-4 text-right text-[10px] font-black text-brown-400 uppercase tracking-[0.2em]"
            >
              {{ $t('admin.photos.table.actions') }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-sand-100">
          <tr
            v-for="adminPhoto in photos"
            :key="adminPhoto.id"
            class="hover:bg-sand-50/30 transition-colors"
          >
            <td class="px-6 py-5 whitespace-nowrap">
              <div
                class="h-16 w-16 flex-shrink-0 cursor-pointer group/img relative"
                @click="openImage(adminPhoto)"
              >
                <OptimizedImage
                  class="h-16 w-16 rounded-xl border border-sand-200 shadow-sm transition-transform group-hover/img:scale-105"
                  :src="adminPhoto.image_url"
                  :alt="adminPhoto.location_name"
                  :width="64"
                  :height="64"
                />
                <div
                  class="absolute inset-0 bg-black/20 opacity-0 group-hover/img:opacity-100 rounded-xl transition-opacity flex items-center justify-center"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5 text-white"
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
                </div>
              </div>
            </td>
            <td class="px-6 py-5 whitespace-nowrap">
              <div class="flex flex-col">
                <div class="text-sm font-black text-brown-900 font-display">
                  {{ adminPhoto.users?.name || $t('social.anonymous') }}
                </div>
                <div class="text-[10px] text-brown-400 font-bold uppercase tracking-widest mt-0.5">
                  {{ adminPhoto.users?.email || 'N/A' }}
                </div>
              </div>
            </td>
            <td class="px-6 py-5">
              <div v-if="editingPhotoId === adminPhoto.id" class="space-y-3 max-w-xs">
                <input
                  v-model="editForm.location_name"
                  type="text"
                  class="w-full text-sm font-medium border border-sand-300 rounded-xl py-2 px-3 focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 text-brown-900 bg-white shadow-sm"
                  :placeholder="$t('admin.photos.edit.location_placeholder')"
                />
                <textarea
                  v-model="editForm.description"
                  rows="3"
                  class="w-full text-sm text-brown-700 border border-sand-300 rounded-xl py-2 px-3 focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 bg-white shadow-sm"
                  :placeholder="$t('admin.photos.edit.description_placeholder')"
                ></textarea>
                <div class="flex gap-2">
                  <button
                    :disabled="isSaving"
                    class="flex-1 text-sm bg-terracotta-600 text-white px-4 py-2 rounded-xl hover:bg-terracotta-700 disabled:opacity-50 font-semibold transition-colors shadow-sm"
                    @click="saveEdit(adminPhoto)"
                  >
                    {{ isSaving ? '...' : $t('admin.photos.edit.save') }}
                  </button>
                  <button
                    class="flex-1 text-sm bg-sand-200 text-brown-700 px-4 py-2 rounded-xl hover:bg-sand-300 font-semibold transition-colors shadow-sm"
                    @click="cancelEdit"
                  >
                    {{ $t('admin.photos.edit.cancel') }}
                  </button>
                </div>
              </div>
              <div
                v-else
                class="relative group cursor-pointer"
                @click="canWriteContent && startEdit(adminPhoto)"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-bold text-brown-900 truncate">
                      {{ adminPhoto.location_name }}
                    </div>
                    <div
                      class="text-xs text-brown-500 line-clamp-2 mt-1 leading-relaxed"
                      :title="adminPhoto.description"
                    >
                      {{ adminPhoto.description || $t('profile.noDescription') }}
                    </div>
                  </div>
                  <button
                    v-if="canWriteContent"
                    class="mt-0.5 p-1.5 text-brown-400 hover:text-terracotta-600 transition-colors rounded-lg hover:bg-sand-100 flex-shrink-0"
                    :title="$t('admin.photos.edit.title')"
                    @click.stop="startEdit(adminPhoto)"
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
                        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </td>
            <td class="px-6 py-5 whitespace-nowrap text-xs font-medium text-brown-400">
              {{ new Date(adminPhoto.uploaded_at).toLocaleDateString() }}
            </td>
            <td class="px-6 py-5 whitespace-nowrap text-right h-24">
              <div class="flex gap-3 justify-end items-center h-full">
                <a
                  :href="`/gallery/${adminPhoto.id}`"
                  target="_blank"
                  class="p-2 text-brown-400 hover:text-terracotta-600 hover:bg-sand-100 rounded-lg transition-colors"
                  :title="$t('admin.photos.view_public')"
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
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
                <button
                  v-if="canDeleteContent"
                  class="px-3 py-1.5 text-xs font-bold text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100"
                  @click="confirmDelete(adminPhoto)"
                >
                  {{ $t('common.delete') }}
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="photos.length === 0 && !isLoading">
            <td colspan="5" class="px-6 py-16 text-center">
              <div class="flex flex-col items-center justify-center opacity-40">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-12 w-12 text-brown-300 mb-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <p class="text-brown-500 font-medium">{{ $t('admin.photos.no_photos') }}</p>
              </div>
            </td>
          </tr>
          <TableSkeleton v-if="isLoading" :columns="5" :avatar-column="1" />
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="photos.length > 0"
      class="px-6 py-4 border-t border-sand-100 flex items-center justify-between bg-white"
    >
      <button
        :disabled="page === 1"
        class="px-4 py-2 border border-sand-300 rounded-xl text-sm font-semibold text-brown-600 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
        @click="page > 1 && loadPhotos(page - 1)"
      >
        {{ $t('admin.pagination.previous') }}
      </button>
      <span class="text-sm font-bold text-brown-400 tabular-nums">
        {{ $t('admin.pagination.page') }} {{ page }}
      </span>
      <button
        :disabled="photos.length < limit || page * limit >= totalPhotos"
        class="px-4 py-2 border border-sand-300 rounded-xl text-sm font-semibold text-brown-600 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
        @click="loadPhotos(page + 1)"
      >
        {{ $t('admin.pagination.next') }}
      </button>
    </div>

    <!-- Image Preview Modal -->
    <div
      v-if="previewImage"
      class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center p-4 z-50 transition-opacity"
      @click="previewImage = null"
    >
      <div class="relative">
        <OptimizedImage
          :src="previewImage.image_url"
          class="max-w-full max-h-[90vh] rounded-lg shadow-2xl"
          :alt="previewImage.location_name"
          :lazy="false"
        />
        <button
          class="absolute -top-4 -right-4 bg-white text-black rounded-full p-1 hover:text-gray-300 shadow-lg"
          @click.stop="previewImage = null"
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

    <!-- Confirm Delete Modal -->
    <BaseConfirmModal
      :is-open="deleteConfirmOpen"
      :title="t('admin.photos.delete.title')"
      :message="t('admin.photos.delete.confirm', { location: photoToDelete?.location_name })"
      :confirm-text="$t('common.delete')"
      variant="danger"
      :is-loading="isDeleting"
      @close="deleteConfirmOpen = false"
      @confirm="executeDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/components/toast/use-toast';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';
import { BaseConfirmModal, OptimizedImage } from '@/components/ui';

const { t } = useI18n();

const { toast } = useToast();

const authStore = useAuthStore();

interface AdminPhoto {
  id: string;
  image_url: string;
  description: string;
  location_name: string;
  uploaded_at: string;
  status: string;
  user_id: string;
  users?: {
    email: string;
    name: string;
  };
}

const photos = ref<AdminPhoto[]>([]);
const totalPhotos = ref(0);
const searchQuery = ref('');
const page = ref(1);
const limit = 20;
const isLoading = ref(false);
const previewImage = ref<AdminPhoto | null>(null);

const canDeleteContent = computed(
  (): boolean => authStore.hasPermission('content:delete') || authStore.isAdmin
);
const canWriteContent = computed(
  (): boolean => authStore.hasPermission('content:write') || authStore.isAdmin
);
const searchTimeoutId = ref<ReturnType<typeof setTimeout> | null>(null);

// Editing state
const editingPhotoId = ref<string | null>(null);
const isSaving = ref(false);
const editForm = ref({
  location_name: '',
  description: '',
});

// Delete state
const deleteConfirmOpen = ref(false);
const photoToDelete = ref<AdminPhoto | null>(null);
const isDeleting = ref(false);

const startEdit = (photo: AdminPhoto): void => {
  if (!canWriteContent.value) {
    console.warn('User does not have content:write permission');
    toast({
      title: t('admin.photos.action_denied'),
      description: t('admin.photos.no_permission'),
      variant: 'destructive',
    });
    return;
  }
  editingPhotoId.value = photo.id;
  editForm.value = {
    location_name: photo.location_name,
    description: photo.description,
  };
};

const cancelEdit = (): void => {
  editingPhotoId.value = null;
};

const saveEdit = async (photo: AdminPhoto): Promise<void> => {
  if (!editForm.value.location_name.trim()) return;

  isSaving.value = true;
  try {
    const updated = await apiV1.patch(`/admin/photos/${photo.id}`, editForm.value);
    photo.location_name = updated.location_name;
    photo.description = updated.description;

    editingPhotoId.value = null;
    toast({
      description: t('admin.photos.edit.success'),
      variant: 'success',
    });
  } catch (e) {
    console.error('Failed to update photo', e);
    toast({
      title: t('common.error'),
      description: t('admin.photos.edit.error'),
      variant: 'destructive',
    });
  } finally {
    isSaving.value = false;
  }
};

const loadPhotos = async (newPage: number = 1): Promise<void> => {
  isLoading.value = true;
  try {
    const offset = (newPage - 1) * limit;
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }

    const response = await apiV1.get<{ data: AdminPhoto[]; total: number }>(
      `/admin/photos?${params.toString()}`
    );
    photos.value = response.data;
    totalPhotos.value = response.total;
    page.value = newPage;
  } catch (e) {
    console.error('Failed to load photos', e);
  } finally {
    isLoading.value = false;
  }
};

const handleSearch = (): void => {
  // Simple debounce 300ms mechanism
  if (searchTimeoutId.value) {
    clearTimeout(searchTimeoutId.value);
  }

  searchTimeoutId.value = setTimeout(() => {
    loadPhotos(1);
  }, 300);
};

const openImage = (photo: AdminPhoto): void => {
  previewImage.value = photo;
};

const confirmDelete = (photo: AdminPhoto): void => {
  if (!canDeleteContent.value) return;
  photoToDelete.value = photo;
  deleteConfirmOpen.value = true;
};

const executeDelete = async (): Promise<void> => {
  if (!photoToDelete.value) return;

  isDeleting.value = true;
  try {
    await apiV1.delete(`/admin/photos/${photoToDelete.value.id}`);
    loadPhotos(page.value);
    toast({
      description: t('admin.photos.delete.success'),
      variant: 'success',
    });
    deleteConfirmOpen.value = false;
    photoToDelete.value = null;
  } catch (e) {
    toast({
      title: t('common.error'),
      description: t('admin.photos.delete.error'),
      variant: 'destructive',
    });
    console.error(e);
  } finally {
    isDeleting.value = false;
  }
};

onMounted(() => {
  loadPhotos();
});
</script>
