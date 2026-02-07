<template>
  <div class="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
    <GhibliBackground />
    <div class="max-w-5xl mx-auto relative z-10">
      <!-- Profile Card -->
      <div
        class="bg-glass rounded-3xl shadow-lg p-8 mb-12 relative overflow-hidden backdrop-blur-sm border border-white/40"
      >
        <div class="flex flex-col md:flex-row items-center gap-8 relative z-10">
          <!-- Profile Picture -->
          <div class="relative group">
            <div
              class="absolute inset-0 bg-terracotta rounded-full blur-md opacity-20 group-hover:opacity-40 transition-opacity duration-500"
            ></div>
            <img
              :src="viewedUser?.picture || '/default-avatar.svg'"
              :alt="viewedUser?.name || 'User'"
              class="w-40 h-40 rounded-full object-cover border-4 border-white shadow-md relative z-10"
              @error="handleImageError"
            />
            <button
              v-if="isOwnProfile"
              class="absolute bottom-2 right-2 p-2 bg-white text-terracotta rounded-full shadow-lg hover:bg-terracotta hover:text-white transition-all transform hover:scale-110 z-20 cursor-pointer"
              title="Edit Profile"
              @click="showEditModal = true"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
                />
              </svg>
            </button>
          </div>

          <!-- Profile Info -->
          <div class="flex-1 text-center md:text-left">
            <h1 class="text-4xl font-heading font-bold text-brown mb-1">
              {{ viewedUser?.name || 'Unknown User' }}
            </h1>
            <p
              v-if="viewedUser?.username"
              class="text-terracotta font-medium mb-4 flex items-center justify-center md:justify-start gap-2"
            >
              @{{ viewedUser.username }}
            </p>

            <p class="text-brown-light text-lg mb-4 max-w-xl font-body leading-relaxed">
              {{ viewedUser?.bio || 'Just a cat wandering through the world...' }}
            </p>

            <div
              class="flex flex-wrap items-center justify-center md:justify-start gap-4 text-sm text-gray-500 font-medium"
            >
              <div
                v-if="viewedUser?.is_pro"
                class="flex items-center px-3 py-1 bg-gradient-to-r from-yellow-400 to-orange-500 text-white rounded-full shadow-sm border border-orange-400/30"
              >
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
                </svg>
                PRO
              </div>
              <span
                class="flex items-center px-3 py-1 bg-white/50 rounded-full border border-white/60"
              >
                <svg
                  class="w-4 h-4 mr-2 text-sage-dark"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                Joined {{ formatJoinDate(viewedUser?.created_at) }}
              </span>
              <span
                class="flex items-center px-3 py-1 bg-white/50 rounded-full border border-white/60"
              >
                <svg
                  class="w-4 h-4 mr-2 text-terracotta"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                {{ uploads.length }} Uploads
              </span>
              <span
                class="flex items-center px-3 py-1 bg-orange-50 rounded-full border border-orange-200 text-orange-700 shadow-sm"
              >
                <img
                  src="/give-treat.png"
                  alt=""
                  class="w-4 h-4 mr-1.5 object-contain"
                  aria-hidden="true"
                />
                <span class="mr-1.5">Treats:</span>
                {{
                  (viewedUser as any)?.treat_balance ||
                  (viewedUser as any)?.total_treats_received ||
                  0
                }}
              </span>
            </div>

            <div class="mt-4 flex justify-center md:justify-start gap-3">
              <router-link
                v-if="isOwnProfile && !viewedUser?.is_pro"
                to="/subscription"
                class="text-xs bg-terracotta/10 text-terracotta hover:bg-terracotta hover:text-white px-3 py-1 rounded-lg transition-all font-bold border border-terracotta/20"
              >
                Upgrade to Pro
              </router-link>
              <router-link
                to="/leaderboard"
                class="text-xs bg-sage/10 text-sage-dark hover:bg-sage hover:text-white px-3 py-1 rounded-lg transition-all font-bold border border-sage/20"
              >
                Leaderboard
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Gallery Section -->
      <div class="mb-6">
        <h2
          class="text-2xl font-heading font-bold text-brown text-center md:text-left pl-2 mb-4 border-l-4 border-terracotta"
        >
          {{ isOwnProfile ? 'My Collection' : `${viewedUser?.name || 'User'}'s Collection` }}
        </h2>
      </div>

      <!-- Tab Content: Uploads -->
      <div class="min-h-[300px]">
        <!-- Loading State -->
        <!-- Loading State -->
        <div v-if="uploadsLoading" class="flex flex-col justify-center items-center py-20">
          <GhibliLoader text="Gathering memories..." />
        </div>

        <!-- Error State -->
        <ErrorState v-else-if="uploadsError" :message="uploadsError" @retry="loadProfileData" />

        <!-- No Uploads State -->
        <EmptyState
          v-else-if="uploads.length === 0"
          title="Welcome Home!"
          message="Your gallery is looking a bit quiet."
          sub-message="Help us find all the purrfect spots around town! Start your journey by sharing your first cat discovery."
          action-text="Share Your First Spot"
          action-link="/upload"
        />

        <!-- Uploads Grid (Pinterest Masonry Style) -->
        <!-- Uploads Grid (Organized Grid Style) -->
        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6 p-4">
          <button
            v-for="upload in uploads"
            :key="upload.id"
            class="group relative aspect-square rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-500 bg-stone-100 text-left"
            @click="openImageModal(upload)"
          >
            <!-- Image with Hover Zoom -->
            <img
              :src="upload.image_url"
              :alt="upload.description || 'A cat'"
              class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              loading="lazy"
            />

            <!-- Elegant Overlay -->
            <div
              class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4"
            >
              <p
                class="text-white font-heading font-bold text-sm truncate filter drop-shadow-md transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300"
              >
                {{ upload.location_name || 'Mystery Spot' }}
              </p>
              <p
                class="text-white/80 text-xs truncate filter drop-shadow-md transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300 delay-75"
              >
                {{ new Date(upload.uploaded_at).toLocaleDateString() }}
              </p>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Profile Modal -->
    <EditProfileModal
      :is-open="showEditModal"
      :initial-name="authStore.user?.name || ''"
      :initial-username="authStore.user?.username || ''"
      :initial-bio="authStore.user?.bio || ''"
      :initial-picture="authStore.user?.picture || ''"
      @close="showEditModal = false"
      @save="handleSaveProfile"
    />

    <!-- Image Modal -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="selectedImage"
        class="fixed inset-0 bg-stone-900/80 backdrop-blur-md z-50 flex items-center justify-center p-4 md:p-8"
        @click="closeImageModal"
      >
        <div
          class="relative bg-white rounded-3xl overflow-hidden shadow-2xl max-w-6xl w-full max-h-[90vh] flex flex-col md:flex-row transform transition-all"
          @click.stop
        >
          <!-- Close Button (Minimalist) -->
          <button
            class="absolute top-6 right-6 z-20 text-stone-400 hover:text-brown bg-transparent transition-colors p-1 cursor-pointer"
            @click="closeImageModal"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>

          <!-- Image Section -->
          <div
            class="w-full md:w-3/5 bg-stone-100 flex items-center justify-center relative overflow-hidden h-[45vh] md:h-auto group"
          >
            <!-- Main Image -->
            <img
              :src="selectedImage.image_url"
              class="w-full h-full object-cover z-10"
              :alt="selectedImage.description || 'A cat'"
            />
          </div>

          <!-- Details Section -->
          <div class="w-full md:w-2/5 bg-white flex flex-col h-auto md:h-auto relative">
            <div class="p-8 md:p-10 flex flex-col h-full">
              <!-- Header: User Info -->
              <div class="flex items-center gap-4 mb-8 pt-2">
                <img
                  :src="authStore.user?.picture || '/default-avatar.svg'"
                  class="w-14 h-14 rounded-full object-cover border-2 border-stone-100 shadow-sm"
                  :alt="authStore.user?.name || 'User'"
                />
                <div>
                  <h4 class="text-brown font-heading font-bold text-xl leading-none mb-1">
                    {{ authStore.user?.name }}
                  </h4>
                  <p class="text-xs text-stone-400 font-medium uppercase tracking-widest">
                    Uploaded {{ new Date(selectedImage.uploaded_at).toLocaleDateString() }}
                  </p>
                </div>
              </div>

              <!-- Content -->
              <div class="flex-grow overflow-y-auto custom-scrollbar pr-2 space-y-4">
                <div>
                  <h3
                    class="text-3xl font-heading font-extrabold text-terracotta mb-2 leading-tight"
                  >
                    {{ selectedImage.location_name || 'Unknown Spot' }}
                  </h3>
                  <div class="h-1 w-20 bg-sage/30 rounded-full"></div>
                </div>

                <p
                  v-if="selectedImage.description && selectedImage.description !== '-'"
                  class="text-brown-light font-body leading-relaxed text-lg whitespace-pre-wrap"
                >
                  {{ selectedImage.description }}
                </p>
                <p v-else class="text-stone-300 italic">No description provided.</p>
              </div>

              <!-- Footer Actions -->
              <div
                class="mt-8 pt-6 border-t border-stone-100 flex justify-between items-center text-stone-400 text-sm"
              >
                <span
                  class="flex items-center text-brown-light font-medium bg-stone-50 px-3 py-1.5 rounded-lg"
                >
                  <svg
                    class="w-4 h-4 mr-2 text-terracotta"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  {{ selectedImage.latitude ? 'Location tagged' : 'No location' }}
                </span>

                <!-- Action Buttons -->
                <div class="flex items-center gap-3">
                  <!-- Give Treat Button (Only for other users' photos) -->
                  <button
                    v-if="!isOwnProfile && authStore.isAuthenticated"
                    class="treat-btn-mini group flex flex-col items-center"
                    :disabled="isSendingTreat"
                    @click="handleGiveTreat(selectedImage)"
                  >
                    <div
                      class="relative w-12 h-12 transition-transform hover:scale-110 active:scale-95"
                    >
                      <img
                        src="/give-treat.png"
                        alt="Give Treat"
                        class="w-full h-full object-contain filter drop-shadow-sm"
                      />
                      <div
                        v-if="isSendingTreat"
                        class="absolute inset-0 flex items-center justify-center bg-white/40 rounded-full"
                      >
                        <div
                          class="w-4 h-4 border-2 border-terracotta border-t-transparent rounded-full animate-spin"
                        ></div>
                      </div>
                    </div>
                  </button>

                  <button
                    v-if="isOwnProfile"
                    class="p-2 text-stone-400 hover:text-brown transition-colors rounded-full hover:bg-stone-50 cursor-pointer"
                    title="Edit Details"
                    @click="openEditPhotoModal(selectedImage)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="w-5 h-5"
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
                  <button
                    v-if="isOwnProfile"
                    class="p-2 text-stone-400 hover:text-red-500 transition-colors rounded-full hover:bg-red-50 cursor-pointer"
                    title="Delete Photo"
                    @click="confirmDeletePhoto(selectedImage)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Edit Photo Modal -->
    <div
      v-if="showEditPhotoModal"
      class="fixed inset-0 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4"
    >
      <div class="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md relative">
        <h3 class="text-2xl font-heading font-bold text-brown mb-6">Edit Photo Details</h3>
        <form @submit.prevent="savePhotoChanges">
          <div class="mb-4">
            <label
              for="edit-location-name"
              class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-wide"
              >Location Name</label
            >
            <input
              id="edit-location-name"
              v-model="photoEditForm.location_name"
              type="text"
              class="w-full px-4 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-terracotta/20 focus:border-terracotta outline-none transition-all"
              required
              maxlength="50"
            />
          </div>
          <div class="mb-6">
            <label
              for="edit-description"
              class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-wide"
              >Description</label
            >
            <textarea
              id="edit-description"
              v-model="photoEditForm.description"
              rows="4"
              class="w-full px-4 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-terracotta/20 focus:border-terracotta outline-none transition-all resize-none"
              maxlength="500"
            ></textarea>
          </div>
          <div class="flex justify-end gap-3">
            <button
              type="button"
              class="px-4 py-2 text-stone-500 hover:text-brown font-medium transition-colors cursor-pointer"
              @click="showEditPhotoModal = false"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="isSavingPhoto"
              class="px-6 py-2 bg-terracotta hover:bg-terracotta-dark text-white rounded-xl shadow-md font-bold transition-all disabled:opacity-50 cursor-pointer"
            >
              {{ isSavingPhoto ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center z-[70] p-4"
    >
      <div
        class="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm text-center relative border-t-4 border-red-500"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-16 w-16 text-red-100 mx-auto mb-4 bg-red-50 rounded-full p-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
        <h3 class="text-xl font-heading font-bold text-brown mb-2">Delete this memory?</h3>
        <p class="text-stone-500 mb-6">
          This action cannot be undone. The photo will be permanently removed from your gallery.
        </p>

        <div class="flex justify-center gap-3">
          <button
            class="px-5 py-2 text-stone-500 hover:bg-stone-50 rounded-lg font-medium transition-colors cursor-pointer"
            @click="showDeleteConfirm = false"
          >
            Keep it
          </button>
          <button
            :disabled="isDeletingPhoto"
            class="px-5 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg shadow-md font-bold transition-all disabled:opacity-50 cursor-pointer"
            @click="executeDeletePhoto"
          >
            {{ isDeletingPhoto ? 'Deleting...' : 'Yes, Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../store/authStore';
import { showError, showSuccess } from '../store/toast';
import { ProfileService, type ProfileUpdateData } from '../services/profileService';
import { useSubscriptionStore } from '@/store/subscriptionStore';
import { TreatsService } from '../services/treatsService';
import { isDev } from '../utils/env';
import ErrorState from '@/components/ui/ErrorState.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useSeo } from '@/composables/useSeo';
import EditProfileModal from '@/components/profile/EditProfileModal.vue';
import type { User } from '@/types/auth'; // Ensure you have this type or use any

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const { setMetaTags, resetMetaTags } = useSeo();

interface Upload {
  id: string;
  image_url: string;
  description?: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  uploaded_at: string;
}

// User State
const viewedUser = ref<User | null>(null);
const loadingUser = ref(true);
const isOwnProfile = computed(() => {
  if (!authStore.user) return false;
  // If no ID param, it's my profile
  if (!route.params.id) return true;

  // Check against ID
  if (route.params.id === authStore.user.id) return true;

  // Check against Username (if available)
  if (authStore.user.username && route.params.id === authStore.user.username) return true;

  return false;
});

const uploads = ref<Upload[]>([]);
const uploadsLoading = ref(false);
const uploadsError = ref<string | null>(null);

const showEditModal = ref(false);
const selectedImage = ref<Upload | null>(null);

// Photo Edit State
const showEditPhotoModal = ref(false);
const showDeleteConfirm = ref(false);
const isSavingPhoto = ref(false);
const isDeletingPhoto = ref(false);
const isSendingTreat = ref(false);
const photoToEdit = ref<Upload | null>(null);
const photoEditForm = ref({
  location_name: '',
  description: '',
});

const openEditPhotoModal = (photo: Upload | null) => {
  if (!photo) return;
  photoToEdit.value = photo;
  photoEditForm.value = {
    location_name: photo.location_name || '',
    description: photo.description || '',
  };
  showEditPhotoModal.value = true;
};

const savePhotoChanges = async () => {
  if (!photoToEdit.value) return;
  isSavingPhoto.value = true;
  try {
    await ProfileService.updatePhoto(photoToEdit.value.id, {
      location_name: photoEditForm.value.location_name,
      description: photoEditForm.value.description,
    });
    showSuccess('Photo updated successfully');

    // Update local state
    const index = uploads.value.findIndex((p) => p.id === photoToEdit.value?.id);
    if (index !== -1 && photoToEdit.value) {
      uploads.value[index] = {
        ...uploads.value[index],
        location_name: photoEditForm.value.location_name,
        description: photoEditForm.value.description,
      };
      // Update selected image view if open
      if (selectedImage.value && selectedImage.value.id === photoToEdit.value.id) {
        selectedImage.value = uploads.value[index];
      }
    }
    showEditPhotoModal.value = false;
  } catch {
    showError('Failed to update photo');
  } finally {
    isSavingPhoto.value = false;
  }
};

const confirmDeletePhoto = (photo: Upload | null) => {
  if (!photo) return;
  photoToEdit.value = photo;
  showDeleteConfirm.value = true;
};

const executeDeletePhoto = async () => {
  if (!photoToEdit.value) return;
  isDeletingPhoto.value = true;
  try {
    await ProfileService.deletePhoto(photoToEdit.value.id);

    // Remove from local state
    uploads.value = uploads.value.filter((p) => p.id !== photoToEdit.value?.id);

    showSuccess('Photo deleted successfully');
    showDeleteConfirm.value = false;
    closeImageModal(); // Close detail view
  } catch {
    showError('Failed to delete photo');
  } finally {
    isDeletingPhoto.value = false;
  }
};

const handleGiveTreat = async (photo: Upload | null) => {
  if (!photo || !authStore.user) return;
  if (isSendingTreat.value) return;

  isSendingTreat.value = true;
  const subscriptionStore = useSubscriptionStore();

  try {
    await subscriptionStore.giveTreat(photo.id, 1);
    showSuccess('You gave a treat! 🍬');

    // Store handles authStore balance update.
    // If viewing someone else's profile, the count in our UI might need update,
    // but the backend handles the receiver's count.
  } catch (err: any) {
    const msg = err.response?.data?.detail || err.message || 'Failed to give treat';
    showError(msg);
  } finally {
    isSendingTreat.value = false;
  }
};

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement;
  // Prevent infinite loop if default-avatar also fails
  if (!target.src.endsWith('/default-avatar.svg')) {
    target.src = '/default-avatar.svg';
  }
};

const loadProfileData = async () => {
  loadingUser.value = true;
  uploadsLoading.value = true;
  uploadsError.value = null;

  try {
    const targetUserId = route.params.id as string;

    if (isOwnProfile.value) {
      // Viewing my own profile

      // Ensure auth
      if (!authStore.isUserReady) {
        // If not logged in and trying to view /profile (no id), redirect to login
        if (!targetUserId) {
          router.push('/login');
          return;
        }
        // If has ID but coincidentally matches unauthenticated state (unlikely but possible), treat as public
      }

      viewedUser.value = authStore.user;

      // Load my uploads
      const userUploads = await ProfileService.getUserUploads();
      uploads.value = userUploads;
    } else {
      // Viewing someone else's profile
      if (!targetUserId) return;

      // Load public profile
      viewedUser.value = await ProfileService.getPublicProfile(targetUserId);

      // Load public uploads
      const publicUploads = await ProfileService.getPublicUserUploads(targetUserId);
      uploads.value = publicUploads;
    }

    // Set SEO
    setMetaTags({
      title: `${viewedUser.value?.name || 'User'} | Purrfect Spots`,
      description: viewedUser.value?.bio || 'Check out this profile on Purrfect Spots',
      image: viewedUser.value?.picture,
    });
  } catch (error) {
    if (isDev()) {
      console.error('Error loading profile:', error);
    }
    uploadsError.value = 'User not found or failed to load profile.';
    uploads.value = [];
    viewedUser.value = null;
  } finally {
    loadingUser.value = false;
    uploadsLoading.value = false;
  }
};

// Sync modal state from URL
const syncStateFromUrl = () => {
  const imageId = route.query.image as string;
  if (!imageId) {
    selectedImage.value = null;
    return;
  }

  const foundImage = uploads.value.find((img) => img.id === imageId);
  if (foundImage) {
    selectedImage.value = foundImage;
  }
};

// Watch for URL changes
watch(
  () => route.query.image,
  () => {
    syncStateFromUrl();
  }
);

// Watch for Route ID changes (navigation between profiles)
watch(
  () => route.params.id,
  () => {
    loadProfileData();
  }
);

const openImageModal = (upload: Upload) => {
  router.push({ query: { ...route.query, image: upload.id } });
};

const closeImageModal = () => {
  const query = { ...route.query };
  delete query.image;
  router.push({ query });
};

const formatJoinDate = (dateString: string | undefined) => {
  if (!dateString) return 'Unknown';

  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
};

const handleSaveProfile = async (data: {
  name: string;
  username: string;
  bio: string;
  picture: string;
}) => {
  try {
    const updateData: ProfileUpdateData = {
      name: data.name,
      username: data.username,
      bio: data.bio,
      picture: data.picture,
    };

    const updatedUser = await ProfileService.updateProfile(updateData);

    // Update local store
    if (authStore.user) {
      authStore.user.name = updatedUser.name;
      authStore.user.username = updatedUser.username;
      authStore.user.bio = updatedUser.bio;
      authStore.user.picture = updatedUser.picture;
      // Update local state if viewing own profile
      if (isOwnProfile.value) {
        viewedUser.value = authStore.user; // Reactivity sync
      }

      // Update localStorage
      localStorage.setItem('user_data', JSON.stringify(authStore.user));
    }

    showEditModal.value = false;
    showSuccess('Profile updated successfully!');
  } catch (error) {
    if (isDev()) {
      console.error('Error saving profile:', error);
    }
    // Handle specific errors...
    const msg = error instanceof Error ? error.message : 'Failed to update profile';
    showError(msg);
  }
};

onMounted(async () => {
  // Load user data
  await loadProfileData();

  // Sync state from URL after data is loaded
  syncStateFromUrl();
});

// Cleanup on unmount
onUnmounted(() => {
  resetMetaTags();
});
</script>

<style scoped>
/* Scoped styles mainly for specific overrides if needed */
.aspect-square {
  aspect-ratio: 1 / 1;
}

/* Custom scrollbar for textareas if needed */
textarea::-webkit-scrollbar {
  width: 8px;
}
textarea::-webkit-scrollbar-track {
  background: #f1f1f1;
}
textarea::-webkit-scrollbar-thumb {
  background: #c97b49;
  border-radius: 4px;
}
</style>
