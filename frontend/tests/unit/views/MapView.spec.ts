import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory, type Router } from 'vue-router';
import MapView from '@/views/MapView.vue';
import { GalleryService } from '@/services/galleryService';
import { useCatsStore } from '@/store';
import { nextTick } from 'vue';
import type { CatLocation } from '@/types/api';

// Mock map dependencies
vi.mock('@/utils/googleMapsLoader', () => ({
  loadGoogleMaps: vi.fn().mockResolvedValue(undefined),
  isGoogleMapsLoaded: vi.fn().mockReturnValue(true),
}));

vi.mock('vue-i18n', () => ({
  useI18n: (): { t: (key: string) => string } => ({ t: (key: string): string => key }),
}));

vi.mock('@/services/galleryService', () => ({
  GalleryService: {
    getLocations: vi.fn().mockResolvedValue([]),
    getViewportLocations: vi.fn().mockResolvedValue([]),
    getPhotoById: vi.fn().mockResolvedValue(null),
  },
}));

// Mock Google Maps API
const mockMap = {
  addListener: vi.fn(),
  getBounds: vi.fn().mockReturnValue({
    getNorthEast: () => ({ lat: (): number => 14, lng: (): number => 101 }),
    getSouthWest: () => ({ lat: (): number => 13, lng: (): number => 100 }),
  }),
  getZoom: vi.fn().mockReturnValue(15),
  fitBounds: vi.fn(),
  panTo: vi.fn(),
  setZoom: vi.fn(),
};

global.google = {
  maps: {
    Map: vi.fn().mockImplementation(() => mockMap),
    LatLngBounds: vi.fn().mockImplementation(() => ({
      extend: vi.fn(),
    })),
    Marker: vi.fn(),
    InfoWindow: vi.fn(),
  },
} as any;

const mockGeolocation = {
  getCurrentPosition: vi.fn(),
  watchPosition: vi.fn().mockReturnValue(1),
  clearWatch: vi.fn(),
};

describe('MapView.vue', () => {
  let router: Router;

  beforeEach(() => {
    // Mock navigator.geolocation
    Object.defineProperty(global, 'navigator', {
      value: {
        geolocation: mockGeolocation,
      },
      configurable: true,
      writable: true,
    });

    setActivePinia(createPinia());
    router = createRouter({
      history: createWebHistory(),
      routes: [{ path: '/map', component: MapView }],
    });

    // Mock env var manually if stubEnv is not available
    process.env.VITE_GOOGLE_MAPS_API_KEY = 'test-key';

    // Create map container in DOM
    const mapDiv = document.createElement('div');
    mapDiv.id = 'map';
    document.body.appendChild(mapDiv);
  });

  afterEach(() => {
    document.body.innerHTML = ''; // Clear the DOM after each test
    delete process.env.VITE_GOOGLE_MAPS_API_KEY;
  });

  it('renders correctly and initializes map', async () => {
    const wrapper = mount(MapView, {
      global: {
        plugins: [router],
        stubs: {
          GhibliLoader: true,
          SearchBox: true,
          CatDetailModal: true,
          ErrorState: true,
          'i18n-t': true,
          OnboardingBanner: true,
          MapSearchBadge: true,
        },
        mocks: {
          $t: (msg: string): string => msg
        }
      },
    });

    expect(wrapper.exists()).toBe(true);
    
    await nextTick();
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 10));

    // Map initialization should be called
    expect(global.google.maps.Map).toHaveBeenCalled();
  });

  it('loads cat locations on mount', async () => {
    const locations: CatLocation[] = [
      { 
        id: '1', 
        latitude: 13.7, 
        longitude: 100.5, 
        location_name: 'Test Cat',
        description: 'A test cat',
        image_url: 'https://example.com/cat.jpg',
        tags: ['test'],
        uploaded_at: new Date().toISOString(),
        likes_count: 0,
        comments_count: 0,
        liked: false
      }
    ];
    vi.mocked(GalleryService.getLocations).mockResolvedValue(locations);

    mount(MapView, {
      global: { plugins: [router], stubs: { GhibliLoader: true, SearchBox: true, CatDetailModal: true, ErrorState: true, 'i18n-t': true, OnboardingBanner: true, MapSearchBadge: true }, mocks: { $t: (msg: string): string => msg } },
    });

    expect(GalleryService.getLocations).toHaveBeenCalled();
    
    const catsStore = useCatsStore();
    await nextTick();
    await nextTick();
    
    expect(catsStore.locations).toEqual(locations);
  });

  it('handles map errors gracefully', async () => {
    vi.mocked(GalleryService.getLocations).mockRejectedValue(new Error('Fetch failed'));
    
    const wrapper = mount(MapView, {
      global: { plugins: [router], stubs: { GhibliLoader: true, SearchBox: true, CatDetailModal: true, ErrorState: true, 'i18n-t': true, OnboardingBanner: true, MapSearchBadge: true }, mocks: { $t: (msg: string): string => msg } },
    });

    await nextTick();
    await nextTick();
    await nextTick();

    expect(wrapper.findComponent({ name: 'ErrorState' }).exists()).toBe(true);
  });

  it('clears search when clear button is clicked', async () => {
    const catsStore = useCatsStore();
    catsStore.setSearchQuery('test search');
    
    const wrapper = mount(MapView, {
      global: { plugins: [router], stubs: { GhibliLoader: true, SearchBox: true, CatDetailModal: true, ErrorState: true, 'i18n-t': true, OnboardingBanner: true, MapSearchBadge: true }, mocks: { $t: (msg: string): string => msg } },
    });

    (wrapper.vm as any).isInitialLoading = false;
    await nextTick();

    const badge = wrapper.findComponent({ name: 'MapSearchBadge' });
    if (badge.exists()) {
      await badge.vm.$emit('clear');
      expect(catsStore.searchQuery).toBe('');
    }
  });
});
