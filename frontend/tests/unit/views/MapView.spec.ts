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

vi.mock('@/utils/env', () => ({
  getEnvVar: vi.fn((key: string) => {
    console.log('getEnvVar called with:', key);
    if (key === 'VITE_GOOGLE_MAPS_API_KEY') return 'test-key';
    return '';
  }),
}));

vi.mock('@/composables/useMapMarkers', () => ({
  useMapMarkers: vi.fn(() => ({
    markers: { value: new Map() },
    userMarker: { value: null },
    updateMarkers: vi.fn(),
    updateUserMarker: vi.fn(),
    clearMarkers: vi.fn(),
  })),
}));


vi.mock('@/services/galleryService', () => {
  return {
    GalleryService: {
      getLocations: vi.fn().mockResolvedValue([]),
      getViewportLocations: vi.fn().mockResolvedValue([]),
      getPhotoById: vi.fn().mockResolvedValue(null),
    },
  };
});

vi.mock('@googlemaps/markerclusterer', () => ({
  MarkerClusterer: class {
    addMarkers = vi.fn();
    removeMarkers = vi.fn();
    clearMarkers = vi.fn();
    setMap = vi.fn();
    render = vi.fn();
  },
  SuperClusterAlgorithm: class {},
}));

// Mock Google Maps API
const mockMap = {
  addListener: vi.fn(),
  getBounds: vi.fn().mockImplementation(() => ({
    getNorthEast: () => ({ lat: (): number => 14, lng: (): number => 101 }),
    getSouthWest: () => ({ lat: (): number => 13, lng: (): number => 100 }),
  })),
  getZoom: vi.fn().mockImplementation(() => 15),
  fitBounds: vi.fn(),
  panTo: vi.fn(),
  setZoom: vi.fn(),
};

global.google = {
  maps: {
    Map: vi.fn(class {
      constructor() {
        return mockMap;
      }
    }),
    LatLngBounds: vi.fn(class {
      extend = vi.fn();
    }),
    Marker: vi.fn(class {
      setMap = vi.fn();
      setPosition = vi.fn();
      addListener = vi.fn().mockReturnValue({ remove: vi.fn() });
      setOptions = vi.fn();
      setIcon = vi.fn();
      setValues = vi.fn();
      // Ensure it uses the global Image stub if it internally creates one
      static MAX_ZINDEX = 1000000;
    }),
    InfoWindow: vi.fn(class {
      open = vi.fn();
      close = vi.fn();
      setContent = vi.fn();
    }),
    OverlayView: class {},
    Size: vi.fn(class {
      constructor(public width: number, public height: number) {}
    }),
    Point: vi.fn(class {
      constructor(public x: number, public y: number) {}
    }),
    SymbolPath: { CIRCLE: 0 },
    event: {
      addListener: vi.fn().mockReturnValue({ remove: vi.fn() }),
      removeListener: vi.fn(),
      trigger: vi.fn(),
    },
  },
} as any;


const mockGeolocation = {
  getCurrentPosition: vi.fn(),
  watchPosition: vi.fn().mockReturnValue(1),
  clearWatch: vi.fn(),
};


describe('MapView.vue', () => {
  let router: Router;

  beforeEach(async () => {
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
      routes: [{ path: '/map', name: 'Map', component: MapView }, { path: '/', component: { template: '<div>Home</div>' } }],
    });
    
    await router.push('/map');
    await router.isReady();

    // Mock requestAnimationFrame for deterministic tests
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => cb(Date.now()));

    // Mock env var manually if stubEnv is not available
    process.env.VITE_GOOGLE_MAPS_API_KEY = 'test-key';
  });

  let wrapper: any;

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
    document.body.innerHTML = ''; // Clear the DOM after each test
    delete process.env.VITE_GOOGLE_MAPS_API_KEY;
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('renders correctly and initializes map', async () => {
    wrapper = mount(MapView, {
      attachTo: document.body,
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
          $t: (msg: string): string => msg,
          catIcon: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        }
      },
    });

    expect(wrapper.exists()).toBe(true);
    
    await nextTick();
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 300));

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
    vi.mocked(GalleryService.getViewportLocations).mockResolvedValue(locations);

    wrapper = mount(MapView, {
      attachTo: document.body,
      global: { 
        plugins: [router], 
        stubs: { 
          GhibliLoader: true, 
          SearchBox: true, 
          CatDetailModal: true, 
          ErrorState: true, 
          'i18n-t': true, 
          OnboardingBanner: true, 
          MapSearchBadge: true 
        }, 
        mocks: { 
          $t: (msg: string): string => msg,
          catIcon: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        } 
      },
    });

    // Wait for map initialization and listener attachment
    await nextTick();
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 500));
    await nextTick();

    // The component fetches on map 'idle' event which we trigger in the mock
    const idleCallback = mockMap.addListener.mock.calls.find(call => call[0] === 'idle')?.[1];
    expect(idleCallback, 'Map idle callback should be registered').toBeDefined();
    
    if (idleCallback) {
      idleCallback();
    }

    // Advance for debounced fetch (300ms)
    await new Promise(resolve => setTimeout(resolve, 500));
    
    expect(GalleryService.getViewportLocations).toHaveBeenCalled();
    
    const catsStore = useCatsStore();
    expect(catsStore.locations).toEqual(expect.arrayContaining(locations));
  });

  it('handles map errors gracefully', async () => {
    vi.mocked(GalleryService.getViewportLocations).mockRejectedValue(new Error('Fetch failed'));
    
    wrapper = mount(MapView, {
      attachTo: document.body,
      global: { 
        plugins: [router], 
        stubs: { 
          GhibliLoader: true, 
          SearchBox: true, 
          CatDetailModal: true, 
          ErrorState: true, 
          'i18n-t': true, 
          OnboardingBanner: true, 
          MapSearchBadge: true 
        }, 
        mocks: { 
          $t: (msg: string): string => msg,
          catIcon: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        } 
      },
    });

    await nextTick();
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 500));

    const idleCallback = mockMap.addListener.mock.calls.find(call => call[0] === 'idle')?.[1];
    if (idleCallback) {
      idleCallback();
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    expect(wrapper.findComponent({ name: 'ErrorState' }).exists()).toBe(true);
  });

  it('clears search when clear button is clicked', async () => {
    const catsStore = useCatsStore();
    catsStore.setSearchQuery('test search');
    
    wrapper = mount(MapView, {
      attachTo: document.body,
      global: { 
        plugins: [router], 
        stubs: { 
          GhibliLoader: true, 
          SearchBox: true, 
          CatDetailModal: true, 
          ErrorState: true, 
          'i18n-t': true, 
          OnboardingBanner: true, 
          MapSearchBadge: true 
        }, 
        mocks: { 
          $t: (msg: string): string => msg,
          catIcon: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        } 
      },
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
