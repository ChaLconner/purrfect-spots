import { ref, computed, type Ref, type ComputedRef } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/store/authStore';
import { ProfileService } from '@/services/profileService';
import { isDev } from '@/utils/env';
import { useSeo } from '@/composables/useSeo';
import type { User } from '@/types/auth';
import type { CatLocation } from '@/types/api';

export function useProfileData(): {
  viewedUser: Ref<User | null>;
  loadingUser: Ref<boolean>;
  isOwnProfile: ComputedRef<boolean>;
  uploads: Ref<CatLocation[]>;
  uploadsLoading: Ref<boolean>;
  uploadsError: Ref<string | null>;
  loadProfileData: (onLoadComplete?: () => void, externalUserId?: string | null) => Promise<void>;
} {
  const authStore = useAuthStore();
  const router = useRouter();
  const route = useRoute();
  const { t } = useI18n();
  const { setMetaTags } = useSeo();

  const viewedUser = ref<User | null>(null);
  const loadingUser = ref(true);
  const uploads = ref<CatLocation[]>([]);
  const uploadsLoading = ref(false);
  const uploadsError = ref<string | null>(null);

  const ensureOwnProfileSession = async (): Promise<boolean> => {
    if (!authStore.isAuthenticated) {
      return false;
    }

    if (authStore.token) {
      return true;
    }

    await authStore.initializeAuth();
    return !!authStore.token;
  };

  const isOwnProfile = computed(() => {
    if (!route.params.id) return true;
    if (!authStore.user) return false;
    if (route.params.id === authStore.user.id) return true;
    if (authStore.user.username && route.params.id === authStore.user.username) return true;
    return false;
  });

  const loadProfileData = async (
    onLoadComplete?: () => void,
    externalUserId?: string | null
  ): Promise<void> => {
    loadingUser.value = true;
    uploadsLoading.value = true;
    uploadsError.value = null;

    try {
      const targetUserId = externalUserId || (route.params.id as string);

      const checkIsOwnProfile = (): boolean => {
        if (!targetUserId) return true;
        if (!authStore.user) return false;
        if (targetUserId === authStore.user.id) return true;
        if (authStore.user.username && targetUserId === authStore.user.username) return true;
        return false;
      };

      const isActuallyOwn = checkIsOwnProfile();

      if (isActuallyOwn) {
        if (!(await ensureOwnProfileSession())) {
          router.push('/login');
          return;
        }
        viewedUser.value = authStore.user;
        uploads.value = await ProfileService.getUserUploads();
      } else {
        if (!targetUserId) return;
        viewedUser.value = await ProfileService.getPublicProfile(targetUserId);
        uploads.value = await ProfileService.getPublicUserUploads(targetUserId);
      }

      if (viewedUser.value) {
        setMetaTags({
          title: `${viewedUser.value.name || t('profile.unknownUser')} | Purrfect Spots`,
          description: viewedUser.value.bio || t('profile.defaultDescription'),
          image: viewedUser.value.picture,
        });
      }

      if (onLoadComplete) {
        onLoadComplete();
      }
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

  return {
    viewedUser,
    loadingUser,
    isOwnProfile,
    uploads,
    uploadsLoading,
    uploadsError,
    loadProfileData,
  };
}
