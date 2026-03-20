<template>
  <div class="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
    <GhibliBackground />
    <div class="max-w-5xl mx-auto relative z-10">
      <!-- Profile Header -->
      <ProfileHeader
        :name="viewedUser?.name || $t('profile.unknownUser')"
        :username="viewedUser?.username"
        :bio="viewedUser?.bio"
        :picture="viewedUser?.picture"
        :created-at="viewedUser?.created_at"
        :uploads-count="uploads.length"
        :is-pro="viewedUser?.is_pro"
        :treat-balance="viewedUser?.treat_balance || viewedUser?.total_treats_received"
        :is-own-profile="isOwnProfile"
        @edit="showEditModal = true"
        @logout="handleLogout"
      />

      <!-- Gallery Section -->
      <ProfileGallery
        :uploads="uploads"
        :is-loading="uploadsLoading"
        :error="uploadsError"
        :is-own-profile="isOwnProfile"
        :user-name="viewedUser?.name"
        @open-image="openImageModal"
        @retry="loadProfileData"
      />
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

    <!-- Image Detail Modal -->
    <ImageDetailModal
      :is-open="!!selectedImage"
      :image="selectedImage"
      :user="viewedUser"
      :current-user="authStore.user"
      :is-own-profile="isOwnProfile"
      :is-sending-treat="isSendingTreat"
      @close="closeImageModal"
      @give-treat="handleGiveTreat"
      @edit="openEditPhotoModal"
      @delete="confirmDeletePhoto"
    />

    <!-- Edit Photo Modal -->
    <EditPhotoModal
      :is-open="showEditPhotoModal"
      :initial-location-name="photoToEdit?.location_name"
      :initial-description="photoToEdit?.description"
      :is-saving="isSavingPhoto"
      @close="showEditPhotoModal = false"
      @save="savePhotoChanges"
    />

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmModal
      :is-open="showDeleteConfirm"
      :is-deleting="isDeletingPhoto"
      @close="showDeleteConfirm = false"
      @confirm="executeDeletePhoto"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../store/authStore';
import { showError, showSuccess } from '../store/toast';
import { ProfileService, type ProfileUpdateData } from '../services/profileService';
import { AuthService } from '../services/authService';
import { useSubscriptionStore } from '@/store/subscriptionStore';
import { isDev } from '../utils/env';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useSeo } from '@/composables/useSeo';
import type { User } from '@/types/auth';
import type { CatLocation } from '@/types/api';

// Sub-components
import ProfileHeader from '@/components/profile/ProfileHeader.vue';
import ProfileGallery from '@/components/profile/ProfileGallery.vue';
import ImageDetailModal from '@/components/profile/ImageDetailModal.vue';
import EditProfileModal from '@/components/profile/EditProfileModal.vue';
import EditPhotoModal from '@/components/profile/EditPhotoModal.vue';
import DeleteConfirmModal from '@/components/profile/DeleteConfirmModal.vue';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const { t } = useI18n();
const { setMetaTags, resetMetaTags } = useSeo();
const subscriptionStore = useSubscriptionStore();

// User State
const viewedUser = ref<User | null>(null);
const loadingUser = ref(true);
const isOwnProfile = computed(() => {
  // If no ID param, it's intended to be my profile (even if not logged in yet)
  if (!route.params.id) return true;

  if (!authStore.user) return false;

  // Check against ID
  if (route.params.id === authStore.user.id) return true;

  // Check against Username (if available)
  if (authStore.user.username && route.params.id === authStore.user.username) return true;

  return false;
});

const uploads = ref<CatLocation[]>([]);
const uploadsLoading = ref(false);
const uploadsError = ref<string | null>(null);

const showEditModal = ref(false);
const selectedImage = ref<CatLocation | null>(null);

// Photo Edit State
const showEditPhotoModal = ref(false);
const showDeleteConfirm = ref(false);
const isSavingPhoto = ref(false);
const isDeletingPhoto = ref(false);
const isSendingTreat = ref(false);
const photoToEdit = ref<CatLocation | null>(null);

const openEditPhotoModal = (photo: CatLocation): void => {
  photoToEdit.value = photo;
  showEditPhotoModal.value = true;
};

const savePhotoChanges = async (data: {
  location_name: string;
  description: string;
}): Promise<void> => {
  if (!photoToEdit.value) return;
  isSavingPhoto.value = true;
  try {
    await ProfileService.updatePhoto(photoToEdit.value.id, {
      location_name: data.location_name,
      description: data.description,
    });
    showSuccess(t('profile.photoUpdated'));

    // Update local state
    const index = uploads.value.findIndex((p) => p.id === photoToEdit.value?.id);
    if (index !== -1 && photoToEdit.value) {
      const updatedUpload = {
        ...uploads.value[index],
        location_name: data.location_name,
        description: data.description,
      };

      uploads.value[index] = updatedUpload;

      // Update selected image view if open
      // Important: replace the reference so it triggers reactivity if needed
      if (selectedImage.value && selectedImage.value.id === photoToEdit.value.id) {
        selectedImage.value = updatedUpload;
      }
    }
    showEditPhotoModal.value = false;
  } catch {
    showError(t('profile.photoUpdateFailed'));
  } finally {
    isSavingPhoto.value = false;
  }
};

const confirmDeletePhoto = (photo: CatLocation): void => {
  photoToEdit.value = photo;
  showDeleteConfirm.value = true;
};

const executeDeletePhoto = async (): Promise<void> => {
  if (!photoToEdit.value) return;
  isDeletingPhoto.value = true;
  try {
    await ProfileService.deletePhoto(photoToEdit.value.id);

    // Remove from local state
    uploads.value = uploads.value.filter((p) => p.id !== photoToEdit.value?.id);

    showSuccess(t('profile.photoDeleted'));
    showDeleteConfirm.value = false;
    closeImageModal(); // Close detail view
  } catch {
    showError(t('profile.photoDeleteFailed'));
  } finally {
    isDeletingPhoto.value = false;
  }
};

const handleGiveTreat = async (photo: CatLocation): Promise<void> => {
  if (!photo) return;
  if (!authStore.isAuthenticated) {
    showError(t('profile.signInToGiveTreats'));
    return;
  }
  if (isSendingTreat.value) return;

  isSendingTreat.value = true;

  try {
    await subscriptionStore.giveTreat(photo.id, 1);
    showSuccess(t('profile.treatGiven'));
    // Backend handles the balance transaction
  } catch (err: unknown) {
    const msg =
      (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
      (err as Error).message ||
      t('profile.treatFailed');
    showError(msg);
  } finally {
    isSendingTreat.value = false;
  }
};

const handleLogout = async (): Promise<void> => {
  try {
    await AuthService.logout();
    authStore.clearAuth();
    showSuccess(t('profile.loggedOut'));
    router.push('/');
  } catch (error) {
    if (isDev()) console.error('Logout error:', error);
    authStore.clearAuth();
    router.push('/');
  }
};

const loadProfileData = async (): Promise<void> => {
  loadingUser.value = true;
  uploadsLoading.value = true;
  uploadsError.value = null;

  try {
    // Load profile data
    const targetUserId = route.params.id as string;

    if (isOwnProfile.value) {
      // Viewing my own profile
      if (!authStore.isAuthenticated && !targetUserId) {
        router.push('/login');
        return;
      }

      viewedUser.value = authStore.user;
      uploads.value = await ProfileService.getUserUploads();
    } else {
      // Viewing someone else's profile
      if (!targetUserId) return;
      viewedUser.value = await ProfileService.getPublicProfile(targetUserId);
      uploads.value = await ProfileService.getPublicUserUploads(targetUserId);
    }

    // Set SEO
    if (viewedUser.value) {
      setMetaTags({
        title: `${viewedUser.value.name || t('profile.unknownUser')} | Purrfect Spots`,
        description: viewedUser.value.bio || t('profile.defaultDescription'),
        image: viewedUser.value.picture,
      });
    }

    // Sync from URL AFTER data is loaded
    syncStateFromUrl();
  } catch (error) {
    if (isDev()) {
      console.error('Error loading profile:', error);
    }
    uploadsError.value = t('profile.userNotFound');
    uploads.value = [];
    viewedUser.value = null;
  } finally {
    loadingUser.value = false;
    uploadsLoading.value = false;
  }
};

// Sync modal state from URL
const syncStateFromUrl = (): void => {
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

const openImageModal = (upload: CatLocation): void => {
  router.push({ query: { ...route.query, image: upload.id } });
};

const closeImageModal = (): void => {
  const query = { ...route.query };
  delete query.image;
  router.push({ query });
};

const handleSaveProfile = async (data: {
  name: string;
  username: string;
  bio: string;
  picture: string;
}): Promise<void> => {
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
    }

    // Update local state if viewing own profile
    if (isOwnProfile.value) {
      viewedUser.value = authStore.user;
    }

    showSuccess(t('profile.photoUpdated').replace('Photo', 'Profile'));
    showEditModal.value = false;
  } catch (error) {
    if (isDev()) {
      console.error('Error saving profile:', error);
    }
    // Handle specific errors...
    const msg =
      error instanceof Error
        ? error.message
        : t('profile.photoUpdateFailed').replace('photo', 'profile');
    showError(msg);
  }
};

// Initialization logic
onMounted(() => {
  // If auth is already initialized, load data immediately
  // Otherwise, the watcher below will handle it
  if (authStore.isInitialized) {
    loadProfileData();
  }
});

// Re-load data when auth initializes or route changes
watch(
  [(): boolean => authStore.isInitialized, (): string | string[] => route.params.id],
  ([isInit]): void => {
    // Only fetch if initialized
    if (isInit) {
      loadProfileData();
    }
  },
  { immediate: false }
);

// Cleanup on unmount
onUnmounted(() => {
  resetMetaTags();
});
</script>
