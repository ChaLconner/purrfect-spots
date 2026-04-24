import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useProfileData } from '@/composables/useProfileData';
import { ProfileService } from '@/services/profileService';

const mocks = vi.hoisted(() => ({
  authStore: {
    isAuthenticated: true,
    token: 'token-123',
    user: {
      id: 'user-1',
      username: 'meow',
      name: 'Test User',
      email: 'test@example.com',
      bio: 'Cat spotter',
      picture: 'https://example.com/avatar.jpg',
    },
    initializeAuth: vi.fn(),
  },
  route: {
    params: {} as Record<string, string | undefined>,
  },
  router: {
    push: vi.fn(),
  },
  setMetaTags: vi.fn(),
  t: vi.fn((key: string) => key),
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => mocks.authStore,
}));

vi.mock('vue-router', () => ({
  useRoute: () => mocks.route,
  useRouter: () => mocks.router,
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: mocks.t }),
  createI18n: vi.fn(() => ({})),
}));

vi.mock('@/composables/useSeo', () => ({
  useSeo: () => ({ setMetaTags: mocks.setMetaTags }),
}));

vi.mock('@/utils/env', () => ({
  isDev: () => false,
}));

vi.mock('@/services/profileService', () => ({
  ProfileService: {
    getUserUploads: vi.fn(),
    getPublicProfileBundle: vi.fn(),
  },
}));

function mountComposable() {
  let composable!: ReturnType<typeof useProfileData>;

  const wrapper = mount(
    defineComponent({
      setup() {
        composable = useProfileData();
        return () => null;
      },
    })
  );

  return { composable, wrapper };
}

describe('useProfileData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.route.params = {};
    mocks.authStore.isAuthenticated = true;
    mocks.authStore.token = 'token-123';
    mocks.authStore.user = {
      id: 'user-1',
      username: 'meow',
      name: 'Test User',
      email: 'test@example.com',
      bio: 'Cat spotter',
      picture: 'https://example.com/avatar.jpg',
    };
    mocks.authStore.initializeAuth.mockResolvedValue(undefined);
  });

  it('loads the current user profile and uploads when no route id is present', async () => {
    const uploads = [{ id: 'cat-1', location_name: 'Park' }];
    vi.mocked(ProfileService.getUserUploads).mockResolvedValue(uploads as never);
    const onLoadComplete = vi.fn();
    const { composable, wrapper } = mountComposable();

    await composable.loadProfileData(onLoadComplete);

    expect(ProfileService.getUserUploads).toHaveBeenCalled();
    expect(composable.viewedUser.value).toEqual(mocks.authStore.user);
    expect(composable.uploads.value).toEqual(uploads);
    expect(composable.loadingUser.value).toBe(false);
    expect(composable.uploadsLoading.value).toBe(false);
    expect(composable.uploadsError.value).toBeNull();
    expect(mocks.setMetaTags).toHaveBeenCalledWith({
      title: 'Test User | Purrfect Spots',
      description: 'Cat spotter',
      image: 'https://example.com/avatar.jpg',
    });
    expect(onLoadComplete).toHaveBeenCalled();

    wrapper.unmount();
  });

  it('recognizes own profile routes by user id and username', () => {
    mocks.route.params = { id: 'user-1' };
    const byId = mountComposable();

    expect(byId.composable.isOwnProfile.value).toBe(true);
    byId.wrapper.unmount();

    mocks.route.params = { id: 'meow' };
    const byUsername = mountComposable();

    expect(byUsername.composable.isOwnProfile.value).toBe(true);
    byUsername.wrapper.unmount();
  });

  it('treats a routed profile as public when no authenticated user is available', () => {
    mocks.route.params = { id: 'public-user' };
    mocks.authStore.user = null;
    const { composable, wrapper } = mountComposable();

    expect(composable.isOwnProfile.value).toBe(false);

    wrapper.unmount();
  });

  it('refreshes auth before loading an own profile when the token is missing', async () => {
    mocks.authStore.token = null;
    mocks.authStore.initializeAuth.mockImplementation(async () => {
      mocks.authStore.token = 'fresh-token';
    });
    vi.mocked(ProfileService.getUserUploads).mockResolvedValue([]);
    const { composable, wrapper } = mountComposable();

    await composable.loadProfileData();

    expect(mocks.authStore.initializeAuth).toHaveBeenCalled();
    expect(mocks.router.push).not.toHaveBeenCalled();
    expect(ProfileService.getUserUploads).toHaveBeenCalled();

    wrapper.unmount();
  });

  it('redirects own profile loading to login when no authenticated session exists', async () => {
    mocks.authStore.isAuthenticated = false;
    mocks.authStore.token = null;
    const { composable, wrapper } = mountComposable();

    await composable.loadProfileData();

    expect(mocks.router.push).toHaveBeenCalledWith('/login');
    expect(ProfileService.getUserUploads).not.toHaveBeenCalled();
    expect(composable.loadingUser.value).toBe(false);
    expect(composable.uploadsLoading.value).toBe(false);

    wrapper.unmount();
  });

  it('loads public profile bundle for a different route id', async () => {
    mocks.route.params = { id: 'public-user' };
    const publicProfile = {
      id: 'public-user',
      username: 'visitor',
      name: '',
      email: 'visitor@example.com',
      bio: '',
      picture: undefined,
    };
    const uploads = [{ id: 'cat-2', location_name: 'Cafe' }];
    vi.mocked(ProfileService.getPublicProfileBundle).mockResolvedValue({
      profile: publicProfile,
      uploads,
      count: 1,
    } as never);
    const { composable, wrapper } = mountComposable();

    await composable.loadProfileData();

    expect(composable.isOwnProfile.value).toBe(false);
    expect(ProfileService.getPublicProfileBundle).toHaveBeenCalledWith('public-user');
    expect(composable.viewedUser.value).toEqual(publicProfile);
    expect(composable.uploads.value).toEqual(uploads);
    expect(mocks.setMetaTags).toHaveBeenCalledWith({
      title: 'profile.unknownUser | Purrfect Spots',
      description: 'profile.defaultDescription',
      image: undefined,
    });

    wrapper.unmount();
  });

  it('uses an external user id over the route param when loading public data', async () => {
    mocks.route.params = { id: 'route-user' };
    vi.mocked(ProfileService.getPublicProfileBundle).mockResolvedValue({
      profile: { id: 'external-user', name: 'External', email: 'external@example.com' },
      uploads: [],
      count: 0,
    } as never);
    const { composable, wrapper } = mountComposable();

    await composable.loadProfileData(undefined, 'external-user');

    expect(ProfileService.getPublicProfileBundle).toHaveBeenCalledWith('external-user');

    wrapper.unmount();
  });

  it('treats an external id matching the current user as own profile', async () => {
    mocks.route.params = { id: 'public-user' };
    vi.mocked(ProfileService.getUserUploads).mockResolvedValue([]);
    const { composable, wrapper } = mountComposable();

    await composable.loadProfileData(undefined, 'meow');

    expect(ProfileService.getUserUploads).toHaveBeenCalled();
    expect(ProfileService.getPublicProfileBundle).not.toHaveBeenCalled();
    expect(composable.viewedUser.value).toEqual(mocks.authStore.user);

    wrapper.unmount();
  });

  it('clears profile state and exposes a translated error when loading fails', async () => {
    vi.mocked(ProfileService.getUserUploads).mockRejectedValue(new Error('failed'));
    const { composable, wrapper } = mountComposable();

    await composable.loadProfileData();

    expect(composable.viewedUser.value).toBeNull();
    expect(composable.uploads.value).toEqual([]);
    expect(composable.uploadsError.value).toBe('profile.userNotFound');
    expect(composable.loadingUser.value).toBe(false);
    expect(composable.uploadsLoading.value).toBe(false);

    wrapper.unmount();
  });
});
