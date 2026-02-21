import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import GalleryView from '@/views/GalleryView.vue';
import { GalleryService } from '@/services/galleryService';
import { useCatsStore } from '@/store';
import { useAuthStore } from '@/store/authStore';
import { nextTick } from 'vue';

const mockPush = vi.fn();
const mockReplace = vi.fn();
const mockRoute = {
  params: {},
  query: {},
  fullPath: '/gallery'
};

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

vi.mock('@/services/galleryService', () => ({
  GalleryService: {
    getImages: vi.fn(),
    search: vi.fn(),
    getPhotoById: vi.fn(),
  },
}));

vi.mock('@/composables/useSeo', () => ({
  useSeo: () => ({
    setMetaTags: vi.fn(),
    resetMetaTags: vi.fn(),
  }),
}));

// Mock sub-components
vi.mock('@/components/gallery/GalleryHeader.vue', () => ({ default: { template: '<div></div>' } }));
vi.mock('@/components/gallery/GalleryGrid.vue', () => ({ default: { template: '<div></div>' } }));
vi.mock('@/components/gallery/GalleryModal.vue', () => ({ default: { template: '<div></div>' } }));
vi.mock('@/components/ui/GhibliLoader.vue', () => ({ default: { template: '<div></div>' } }));
vi.mock('@/components/ui/GhibliBackground.vue', () => ({ default: { template: '<div></div>' } }));
vi.mock('@/components/ui/ErrorState.vue', () => ({ default: { template: '<div></div>' } }));
vi.mock('@/components/ui/EmptyState.vue', () => ({ default: { template: '<div></div>' } }));

describe('GalleryView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    mockRoute.params = {};
    mockRoute.query = {};
    
    // Default success mock for GalleryService.getImages
    vi.mocked(GalleryService.getImages).mockResolvedValue({
      images: [],
      pagination: { total: 0, page: 1, limit: 20, has_more: false }
    });
  });

  it('renders correctly and fetches initial data when auth is initialized', async () => {
    const authStore = useAuthStore();
    authStore.isInitialized = true;

    const wrapper = shallowMount(GalleryView, {
      global: {
        stubs: {
          GhibliBackground: true,
          GalleryHeader: true,
          GalleryGrid: true,
          GalleryModal: true,
          ErrorState: true,
          EmptyState: true,
          GhibliLoader: true,
        },
        mocks: {
          $t: (msg: string) => msg
        }
      },
    });

    await nextTick();
    await nextTick();

    expect(wrapper.exists()).toBe(true);
    expect(GalleryService.getImages).toHaveBeenCalled();
  });

  it('shows empty state when no images are found', async () => {
    const authStore = useAuthStore();
    authStore.isInitialized = true;

    vi.mocked(GalleryService.getImages).mockResolvedValue({
      images: [],
      pagination: { total: 0, page: 1, limit: 20, has_more: false }
    });

    const wrapper = shallowMount(GalleryView, {
      global: {
        stubs: { GhibliBackground: true, GalleryHeader: true, GalleryGrid: true, GalleryModal: true, ErrorState: true, EmptyState: true, GhibliLoader: true },
        mocks: { $t: (msg: string) => msg }
      }
    });

    await nextTick();
    await nextTick();

    expect(wrapper.findComponent({ name: 'EmptyState' }).exists()).toBe(true);
  });

  it('triggers search when gallerySearchQuery in store changes', async () => {
    const authStore = useAuthStore();
    authStore.isInitialized = true;
    const catsStore = useCatsStore();

    vi.mocked(GalleryService.search).mockResolvedValue({
      results: [{ id: '1', image_url: 'test.jpg' } as any],
      total: 1,
      page: 1,
      limit: 20
    });

    shallowMount(GalleryView, {
      global: {
        stubs: { GhibliBackground: true, GalleryHeader: true, GalleryGrid: true, GalleryModal: true, ErrorState: true, EmptyState: true, GhibliLoader: true },
        mocks: { $t: (msg: string) => msg }
      }
    });

    await nextTick();
    
    // Trigger search
    catsStore.setGallerySearchQuery('cute cats');
    
    await nextTick();
    await nextTick();

    expect(mockReplace).toHaveBeenCalled();
    expect(GalleryService.search).toHaveBeenCalledWith({
      query: 'cute cats',
      page: 1,
      limit: 20
    });
  });

  it('handles loading more images', async () => {
    const authStore = useAuthStore();
    authStore.isInitialized = true;

    vi.mocked(GalleryService.getImages).mockResolvedValue({
      images: [{ id: '1' } as any],
      pagination: { total: 2, page: 1, limit: 1, has_more: true }
    });

    const wrapper = shallowMount(GalleryView, {
      global: {
        stubs: { GhibliBackground: true, GalleryHeader: true, GalleryGrid: true, GalleryModal: true, ErrorState: true, EmptyState: true, GhibliLoader: true },
        mocks: { $t: (msg: string) => msg }
      }
    });

    await nextTick();
    await nextTick();

    expect(wrapper.vm.visibleImages.length).toBe(1);

    // Mock second page
    vi.mocked(GalleryService.getImages).mockResolvedValue({
      images: [{ id: '2' } as any],
      pagination: { total: 2, page: 2, limit: 1, has_more: false }
    });

    await wrapper.vm.loadMoreImages();
    await nextTick();

    expect(wrapper.vm.visibleImages.length).toBe(2);
    expect(wrapper.vm.currentPage).toBe(2);
  });

  it('syncs state from URL for deep linked image', async () => {
    const authStore = useAuthStore();
    authStore.isInitialized = true;

    const mockPhoto = { id: 'deep-1', location_name: 'Test Spot', description: 'Deep linked cat' };
    vi.mocked(GalleryService.getPhotoById).mockResolvedValue(mockPhoto as any);

    // Simulate route param
    mockRoute.params = { id: 'deep-1' };

    const wrapper = shallowMount(GalleryView, {
      props: { id: 'deep-1' },
      global: {
        stubs: { GhibliBackground: true, GalleryHeader: true, GalleryGrid: true, GalleryModal: true, ErrorState: true, EmptyState: true, GhibliLoader: true },
        mocks: { $t: (msg: string) => msg }
      }
    });

    await nextTick();
    await nextTick();
    await nextTick();

    expect(GalleryService.getPhotoById).toHaveBeenCalledWith('deep-1');
    expect(wrapper.vm.selectedImage).toEqual(mockPhoto);
    expect(wrapper.vm.isDeepLinked).toBe(true);
  });

  it('handles error during image fetch', async () => {
    const authStore = useAuthStore();
    authStore.isInitialized = true;

    vi.mocked(GalleryService.getImages).mockRejectedValue(new Error('Network error'));

    const wrapper = shallowMount(GalleryView, {
      global: {
        stubs: { GhibliBackground: true, GalleryHeader: true, GalleryGrid: true, GalleryModal: true, ErrorState: true, EmptyState: true, GhibliLoader: true },
        mocks: { $t: (msg: string) => msg }
      }
    });

    await nextTick();
    await nextTick();

    expect(wrapper.vm.error).toBe('Network error');
    expect(wrapper.findComponent({ name: 'ErrorState' }).exists()).toBe(true);
  });
});
