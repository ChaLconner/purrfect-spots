<template>
  <div class="bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden">
    <div
      class="p-6 border-b border-stone-100 flex flex-col sm:flex-row justify-between items-center gap-4"
    >
      <h2 class="text-xl font-bold text-stone-900">Content Management</h2>
      <div class="relative max-w-xs w-full">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search photos..."
          class="w-full pl-10 pr-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors"
          @input="handleSearch"
        />
        <div class="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400">
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
      <table class="min-w-full divide-y divide-stone-200">
        <thead class="bg-stone-50">
          <tr>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-stone-500 uppercase tracking-wider"
            >
              Photo
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-stone-500 uppercase tracking-wider"
            >
              Uploaded By
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-stone-500 uppercase tracking-wider"
            >
              Location / Desc
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-stone-500 uppercase tracking-wider"
            >
              Date
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-right text-xs font-medium text-stone-500 uppercase tracking-wider"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-stone-200">
          <tr
            v-for="adminPhoto in photos"
            :key="adminPhoto.id"
            class="hover:bg-stone-50 transition-colors"
          >
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="h-16 w-16 flex-shrink-0 cursor-pointer" @click="openImage(adminPhoto)">
                <img
                  class="h-16 w-16 rounded-lg object-cover border border-stone-200"
                  :src="adminPhoto.image_url"
                  :alt="adminPhoto.location_name"
                />
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-stone-900">
                {{ adminPhoto.users?.name || 'Unknown' }}
              </div>
              <div class="text-sm text-stone-500">{{ adminPhoto.users?.email || 'N/A' }}</div>
            </td>
            <td class="px-6 py-4">
              <div v-if="editingPhotoId === adminPhoto.id" class="space-y-2 max-w-xs">
                <input
                  v-model="editForm.location_name"
                  type="text"
                  class="w-full text-sm font-medium border border-stone-300 rounded-md py-1 px-2 focus:ring-orange-500 focus:border-orange-500 text-stone-900 bg-white"
                  placeholder="Location Name"
                />
                <textarea
                  v-model="editForm.description"
                  rows="2"
                  class="w-full text-sm text-stone-500 border border-stone-300 rounded-md py-1 px-2 focus:ring-orange-500 focus:border-orange-500 bg-white"
                  placeholder="Description"
                ></textarea>
                <div class="flex gap-2">
                  <button
                    :disabled="isSaving"
                    class="text-xs bg-orange-600 text-white px-3 py-1.5 rounded hover:bg-orange-700 disabled:opacity-50 font-medium"
                    @click="saveEdit(adminPhoto)"
                  >
                    {{ isSaving ? '...' : 'Save' }}
                  </button>
                  <button
                    class="text-xs bg-stone-200 text-stone-700 px-3 py-1.5 rounded hover:bg-stone-300 font-medium"
                    @click="cancelEdit"
                  >
                    Cancel
                  </button>
                </div>
              </div>
              <div
                v-else
                class="relative group cursor-pointer"
                @click="canWriteContent && startEdit(adminPhoto)"
              >
                <div class="flex items-start justify-between gap-2">
                  <div class="flex-1">
                    <div class="text-sm font-medium text-stone-900">
                      {{ adminPhoto.location_name }}
                    </div>
                    <div
                      class="text-sm text-stone-500 line-clamp-2"
                      :title="adminPhoto.description"
                    >
                      {{ adminPhoto.description }}
                    </div>
                  </div>
                  <button
                    v-if="canWriteContent"
                    class="mt-0.5 p-1 text-stone-400 hover:text-orange-600 transition-colors rounded-md hover:bg-stone-100"
                    title="Edit Content"
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
            <td class="px-6 py-4 whitespace-nowrap text-sm text-stone-500">
              {{ new Date(adminPhoto.uploaded_at).toLocaleDateString() }}
            </td>
            <td
              class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex gap-2 justify-end items-center h-24"
            >
              <a
                :href="`/gallery/${adminPhoto.id}`"
                target="_blank"
                class="text-indigo-600 hover:text-indigo-900"
                title="View Public Page"
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
                class="text-red-600 hover:text-red-900 transition-colors disabled:opacity-50"
                @click="confirmDelete(adminPhoto)"
              >
                Delete
              </button>
            </td>
          </tr>
          <tr v-if="photos.length === 0 && !isLoading">
            <td colspan="5" class="px-6 py-12 text-center text-stone-500">No photos found.</td>
          </tr>
          <TableSkeleton v-if="isLoading" :columns="5" :avatar-column="1" />
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="photos.length > 0"
      class="px-6 py-4 border-t border-stone-200 flex items-center justify-between"
    >
      <button
        :disabled="page === 1"
        class="px-4 py-2 border border-stone-300 rounded-md text-sm font-medium text-stone-700 bg-white hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="page > 1 && loadPhotos(page - 1)"
      >
        Previous
      </button>
      <span class="text-sm text-stone-600">Page {{ page }}</span>
      <button
        :disabled="photos.length < limit || page * limit >= totalPhotos"
        class="px-4 py-2 border border-stone-300 rounded-md text-sm font-medium text-stone-700 bg-white hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="loadPhotos(page + 1)"
      >
        Next
      </button>
    </div>

    <!-- Image Preview Modal -->
    <div
      v-if="previewImage"
      class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center p-4 z-50 transition-opacity"
      @click="previewImage = null"
    >
      <div class="relative">
        <img
          :src="previewImage.image_url"
          class="max-w-full max-h-[90vh] rounded-lg shadow-2xl"
          :alt="previewImage.location_name"
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { apiV1 } from '@/utils/api';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/components/toast/use-toast';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';

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
const searchTimeoutId = ref<number | null>(null);

// Editing state
const editingPhotoId = ref<string | null>(null);
const isSaving = ref(false);
const editForm = ref({
  location_name: '',
  description: '',
});

const startEdit = (photo: AdminPhoto): void => {
  if (!canWriteContent.value) {
    console.warn('User does not have content:write permission');
    toast({
      title: 'Action Denied',
      description: 'You do not have permission to edit content.',
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
      description: 'Photo details updated successfully',
      variant: 'success',
    });
  } catch (e) {
    console.error('Failed to update photo', e);
    toast({
      title: 'Error',
      description: 'Failed to update photo details',
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

  searchTimeoutId.value = window.setTimeout(() => {
    loadPhotos(1);
  }, 300);
};

const openImage = (photo: AdminPhoto): void => {
  previewImage.value = photo;
};

const confirmDelete = async (photo: AdminPhoto): Promise<void> => {
  if (!canDeleteContent.value) return;
  if (
    // eslint-disable-next-line no-alert
    window.confirm(
      `Are you sure you want to delete this photo at ${photo.location_name}? This action cannot be undone.`
    )
  ) {
    try {
      await apiV1.delete(`/admin/photos/${photo.id}`);
      // Optimistic or refresh
      loadPhotos(page.value);
      toast({
        description: 'Photo deleted successfully',
        variant: 'success',
      });
    } catch (e) {
      toast({
        title: 'Error',
        description: 'Failed to delete photo',
        variant: 'destructive',
      });
      console.error(e);
    }
  }
};

onMounted(() => {
  loadPhotos();
});
</script>
