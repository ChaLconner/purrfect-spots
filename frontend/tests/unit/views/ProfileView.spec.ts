import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import ProfileView from '@/views/ProfileView.vue';
import { useAuthStore } from '@/store/authStore';
import { ProfileService } from '@/services/profileService';
import { nextTick } from 'vue';

const mockPush = vi.fn();
const mockReplace = vi.fn();
const mockRoute = {
  params: {} as Record<string, string>,
  query: {},
  fullPath: '/profile',
};

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: (): typeof mockRoute => mockRoute,
  useRouter: (): Record<string, unknown> => ({
    push: mockPush,
    replace: mockReplace,
  }),
}));

vi.mock('vue-i18n', (): Record<string, unknown> => ({
  useI18n: (): { t: (key: string) => string } => ({ t: (key: string): string => key }),
}));

vi.mock('@/services/profileService', () => ({
  ProfileService: {
    getUserUploads: vi.fn(),
    getPublicProfile: vi.fn(),
    getPublicUserUploads: vi.fn(),
    updateProfile: vi.fn(),
    updatePhoto: vi.fn(),
    deletePhoto: vi.fn(),
  },
}));

vi.mock('@/services/authService', () => ({
  AuthService: {
    logout: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock('@/composables/useSeo', (): Record<string, unknown> => ({
  useSeo: (): Record<string, unknown> => ({
    setMetaTags: vi.fn(),
    resetMetaTags: vi.fn(),
  }),
}));

// Mock sub-components
vi.mock('@/components/profile/ProfileHeader.vue', () => ({
  default: { template: '<div></div>', props: ['uploadsCount'] },
}));
vi.mock('@/components/profile/ProfileGallery.vue', () => ({
  default: { template: '<div></div>', props: ['uploads'] },
}));
vi.mock('@/components/profile/ImageDetailModal.vue', () => ({
  default: { template: '<div></div>' },
}));
vi.mock('@/components/profile/EditProfileModal.vue', () => ({
  default: { template: '<div></div>' },
}));
vi.mock('@/components/profile/EditPhotoModal.vue', () => ({
  default: { template: '<div></div>' },
}));
vi.mock('@/components/profile/DeleteConfirmModal.vue', () => ({
  default: { template: '<div></div>' },
}));
vi.mock('@/components/ui/GhibliBackground.vue', () => ({ default: { template: '<div></div>' } }));
vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn(() => ({
      on: vi.fn().mockReturnThis(),
      subscribe: vi.fn().mockReturnThis(),
    })),
    removeChannel: vi.fn(),
  },
}));

describe('ProfileView.vue', (): void => {
  let authStore: ReturnType<typeof useAuthStore>;
 
   beforeEach((): void => {
    setActivePinia(createPinia());
    authStore = useAuthStore();
    vi.clearAllMocks();
    mockRoute.params = {};
    mockRoute.query = {};

    // Mock localStorage
    const storageMock = (() => {
      let store: Record<string, string> = {};
      return {
        getItem: vi.fn((key: string) => store[key] || null),
        setItem: vi.fn((key: string, value: string) => {
          store[key] = value.toString();
        }),
        removeItem: vi.fn((key: string) => {
          delete store[key];
        }),
        clear: vi.fn(() => {
          store = {};
        }),
        key: vi.fn(),
        length: 0,
      };
    })();

    Object.defineProperty(globalThis, 'localStorage', {
      value: storageMock,
      writable: true,
      configurable: true,
    });

    vi.mocked(ProfileService.getUserUploads).mockResolvedValue([]);
    vi.mocked(ProfileService.getPublicUserUploads).mockResolvedValue([]);
    vi.mocked(ProfileService.getPublicProfile).mockResolvedValue({
      id: 'other',
      name: 'Other',
    } as any);

    // Default logged-in state in store
    authStore.isAuthenticated = true;
    authStore.isInitialized = true;
    authStore.token = 'test-token';
    authStore.user = { id: 'test-user-id', name: 'Test User' };
    // authStore.isUserReady is likely a getter
    Object.defineProperty(authStore, 'isUserReady', {
      get: vi.fn(() => !!authStore.user),
      configurable: true,
    });
  });

  const mountProfile = (authOptions = {}): { wrapper: ReturnType<typeof shallowMount>; authStore: typeof authStore } => {
    Object.assign(authStore, authOptions);
 
    const wrapper = shallowMount(ProfileView, {
      global: {
        stubs: {
          ProfileHeader: true,
          ProfileGallery: true,
        },
        mocks: {
          $t: (msg: string): string => msg
        }
      },
    });
 
    return { wrapper, authStore };
  };

  it('renders correctly for own profile', async (): Promise<void> => {
    mockRoute.params = {}; // isOwnProfile: true
    const { wrapper } = mountProfile();

    // Explicitly call to bypass any mounting race
    await wrapper.vm.loadProfileData();
    await nextTick();

    expect(ProfileService.getUserUploads).toHaveBeenCalled();
  });

  it('loads public profile for other users', async () => {
    mockRoute.params = { id: 'other-user' }; // isOwnProfile: false
    vi.mocked(ProfileService.getPublicProfile).mockResolvedValue({
      id: 'other-user',
      name: 'Other',
    } as any);

    const { wrapper } = mountProfile();
    await wrapper.vm.loadProfileData();

    await nextTick();
    await nextTick();

    expect(ProfileService.getPublicProfile).toHaveBeenCalledWith('other-user');
    expect(ProfileService.getPublicUserUploads).toHaveBeenCalledWith('other-user');
  });

  it('redirects to login if viewing own profile but not authenticated', async () => {
    mockRoute.params = {};
    const { wrapper } = mountProfile({
      isAuthenticated: false,
      user: null,
    });

    await wrapper.vm.loadProfileData();
    await nextTick();

    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('handles logout successfully', async () => {
    const { wrapper, authStore } = mountProfile();

    await nextTick();
    await wrapper.vm.handleLogout();

    expect(mockPush).toHaveBeenCalledWith('/');
    expect(authStore.isAuthenticated).toBe(false);
  });

  it('handles profile update successfully', async () => {
    const updatedUser = {
      id: 'test-user-id',
      name: 'New Name',
      username: 'new',
      bio: 'new bio',
      picture: 'new.jpg',
    };
    vi.mocked(ProfileService.updateProfile).mockResolvedValue(updatedUser);

    const { wrapper, authStore } = mountProfile();

    await nextTick();
    await wrapper.vm.handleSaveProfile({
      name: 'New Name',
      username: 'new',
      bio: 'new bio',
      picture: 'new.jpg',
    });

    expect(ProfileService.updateProfile).toHaveBeenCalled();
    expect(authStore.user?.name).toBe('New Name');
  });

  it('handles photo deletion successfully', async () => {
    vi.mocked(ProfileService.getUserUploads).mockResolvedValue([{ id: 'photo-1' } as any]);

    const { wrapper } = mountProfile();

    await nextTick();
    await nextTick();

    wrapper.vm.photoToEdit = { id: 'photo-1' } as any;

    await wrapper.vm.executeDeletePhoto();

    expect(ProfileService.deletePhoto).toHaveBeenCalledWith('photo-1');
  });

  it('shows error state when profile fails to load', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(ProfileService.getPublicProfile).mockRejectedValue(new Error('Not found'));
    mockRoute.params = { id: 'non-existent' };

    const { wrapper } = mountProfile({
      user: { name: 'Placeholder' } // Avoid template evaluating $t on null user if it crashes
    });
    await wrapper.vm.loadProfileData();

    await nextTick();
    await nextTick();
    
    // Yield to event loop to let the un-awaited onMounted promise finish
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(wrapper.vm.uploadsError).toBe('profile.userNotFound');
    consoleErrorSpy.mockRestore();
   });
 });
