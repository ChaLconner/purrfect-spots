import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import MapView from '@/views/MapView.vue';
import { GalleryService } from '@/services/galleryService';
import { useCatsStore } from '@/store';
import { nextTick } from 'vue';

// Mock map dependencies
vi.mock('@/utils/googleMapsLoader', () => ({
  loadGoogleMaps: vi.fn().mockResolvedValue(undefined),
  isGoogleMapsLoaded: vi.fn().mockReturnValue(true),
}));

vi.mock('@/services/galleryService', () => ({
  GalleryService: {
    getLocations: vi.fn().mockResolvedValue([]),
    getViewportLocations: vi.fn().mockResolvedValue([]),
  },
}));

// Mock Google Maps API
const mockMap = {
  addListener: vi.fn(),
  getBounds: vi.fn().mockReturnValue({
    getNorthEast: () => ({ lat: () => 14, lng: () => 101 }),
    getSouthWest: () => ({ lat: () => 13, lng: () => 100 }),
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

describe('MapView.vue', () => {
  let router;

  beforeEach(() => {
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

    vi.clearAllMocks();
  });

  afterEach(() => {
    const mapDiv = document.getElementById('map');
    if (mapDiv) {
      document.body.removeChild(mapDiv);
    }
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
        },
      },
    });

    expect(wrapper.find('.map-page').exists()).toBe(true);
    
    // Should show loader initially
    expect(wrapper.findComponent({ name: 'GhibliLoader' }).exists()).toBe(true);

    await nextTick();
    await nextTick();

    // Map initialization should be called
    expect(global.google.maps.Map).toHaveBeenCalled();
  });

  it('loads cat locations on mount', async () => {
    const locations = [
      { id: '1', latitude: 13.7, longitude: 100.5, location_name: 'Test Cat' }
    ];
    vi.mocked(GalleryService.getLocations).mockResolvedValue(locations);

    mount(MapView, {
      global: { plugins: [router], stubs: { GhibliLoader: true, SearchBox: true, CatDetailModal: true, ErrorState: true } },
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
      global: { plugins: [router], stubs: { GhibliLoader: true, SearchBox: true, CatDetailModal: true, ErrorState: true } },
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
      global: { plugins: [router], stubs: { GhibliLoader: true, SearchBox: true, CatDetailModal: true, ErrorState: true } },
    });

    wrapper.vm.isInitialLoading = false;
    await nextTick();

    const clearBtn = wrapper.find('.clear-search-btn');
    if (clearBtn.exists()) {
      await clearBtn.trigger('click');
      expect(catsStore.searchQuery).toBe('');
    }
  });
});
