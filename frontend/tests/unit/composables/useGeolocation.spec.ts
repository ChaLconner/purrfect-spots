import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useGeolocation } from '@/composables/useGeolocation';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent } from 'vue';

// Create a wrapper component for testing lifecycle hooks
const createTestComponent = () =>
  defineComponent({
    setup() {
      return useGeolocation();
    },
    render() {
      return null;
    },
  });

describe('useGeolocation', () => {
  let mockGeolocation: {
    getCurrentPosition: ReturnType<typeof vi.fn>;
    watchPosition: ReturnType<typeof vi.fn>;
    clearWatch: ReturnType<typeof vi.fn>;
  };
  let originalGeolocation: Geolocation;

  beforeEach(() => {
    // Mock navigator.geolocation
    mockGeolocation = {
      getCurrentPosition: vi.fn(),
      watchPosition: vi.fn().mockReturnValue(123), // returns watchId
      clearWatch: vi.fn(),
    };
    originalGeolocation = navigator.geolocation;
    Object.defineProperty(navigator, 'geolocation', {
      value: mockGeolocation,
      writable: true,
      configurable: true,
    });

    // Mock fetch for IP fallback
    globalThis.fetch = vi.fn();
    vi.clearAllMocks();
  });

  afterEach(() => {
    Object.defineProperty(navigator, 'geolocation', {
      value: originalGeolocation,
      writable: true,
      configurable: true,
    });
  });

  describe('Initial State', () => {
    it('should initialize with default state', () => {
      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      expect(vm.userLocation).toBeNull();
      expect(vm.error).toBeNull();
      expect(vm.isLoading).toBe(false);
      expect(vm.permissionDenied).toBe(false);

      wrapper.unmount();
    });
  });

  describe('getCurrentPosition', () => {
    it('should get current position successfully', async () => {
      const mockPosition: GeolocationPosition = {
        coords: {
          latitude: 13.7563,
          longitude: 100.5018,
          accuracy: 10,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
        },
        timestamp: Date.now(),
      };

      mockGeolocation.getCurrentPosition.mockImplementation(
        (successCallback: PositionCallback) => {
          successCallback(mockPosition);
        }
      );

      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      const result = await vm.getCurrentPosition();

      expect(result).toEqual({ lat: 13.7563, lng: 100.5018 });
      expect(vm.userLocation).toEqual({ lat: 13.7563, lng: 100.5018 });
      expect(vm.isLoading).toBe(false);
      expect(vm.permissionDenied).toBe(false);

      wrapper.unmount();
    });

    it('should handle permission denied and fallback to IP', async () => {
      const ipLocation = { latitude: '14.0', longitude: '101.0' };

      mockGeolocation.getCurrentPosition.mockImplementation(
        (_success: PositionCallback, errorCallback: PositionErrorCallback) => {
          errorCallback({
            code: 1,
            message: 'User denied geolocation permission',
            PERMISSION_DENIED: 1,
            POSITION_UNAVAILABLE: 2,
            TIMEOUT: 3,
          });
        }
      );

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        json: () => Promise.resolve(ipLocation),
      });

      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      const result = await vm.getCurrentPosition();

      expect(vm.permissionDenied).toBe(true);
      expect(result).toEqual({ lat: 14.0, lng: 101.0 });

      wrapper.unmount();
    });

    it('should set error when both geolocation and IP fallback fail', async () => {
      mockGeolocation.getCurrentPosition.mockImplementation(
        (_success: PositionCallback, errorCallback: PositionErrorCallback) => {
          errorCallback({
            code: 2,
            message: 'Position unavailable',
            PERMISSION_DENIED: 1,
            POSITION_UNAVAILABLE: 2,
            TIMEOUT: 3,
          });
        }
      );

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Network error')
      );

      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      const result = await vm.getCurrentPosition();

      expect(result).toBeNull();
      expect(vm.error).toBe('Position unavailable');
      expect(vm.isLoading).toBe(false);

      wrapper.unmount();
    });

    it('should handle missing geolocation API', async () => {
      Object.defineProperty(navigator, 'geolocation', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Network error')
      );

      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      const result = await vm.getCurrentPosition();

      expect(result).toBeNull();
      expect(vm.error).toBe('Geolocation is not supported by this browser');

      wrapper.unmount();
    });
  });

  describe('watchPosition', () => {
    it('should start watching position', async () => {
      const mockPosition: GeolocationPosition = {
        coords: {
          latitude: 13.7563,
          longitude: 100.5018,
          accuracy: 10,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
        },
        timestamp: Date.now(),
      };

      mockGeolocation.getCurrentPosition.mockImplementation(
        (successCallback: PositionCallback) => {
          successCallback(mockPosition);
        }
      );

      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      await vm.startWatchingPosition();

      expect(mockGeolocation.watchPosition).toHaveBeenCalled();

      wrapper.unmount();
    });

    it('should skip watching if permission denied', async () => {
      // Mock getCurrentPosition to set permissionDenied
      mockGeolocation.getCurrentPosition.mockImplementation(
        (_success: PositionCallback, errorCallback: PositionErrorCallback) => {
          errorCallback({
            code: 1,
            message: 'User denied geolocation permission',
            PERMISSION_DENIED: 1,
            POSITION_UNAVAILABLE: 2,
            TIMEOUT: 3,
          });
        }
      );

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Network error')
      );

      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      // First call sets permissionDenied
      await vm.getCurrentPosition();
      expect(vm.permissionDenied).toBe(true);

      // Now try to watch - should be skipped
      mockGeolocation.watchPosition.mockClear();
      await vm.startWatchingPosition();

      expect(mockGeolocation.watchPosition).not.toHaveBeenCalled();

      wrapper.unmount();
    });

    it('should stop watching position', async () => {
      const mockPosition: GeolocationPosition = {
        coords: {
          latitude: 13.7563,
          longitude: 100.5018,
          accuracy: 10,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
        },
        timestamp: Date.now(),
      };

      mockGeolocation.getCurrentPosition.mockImplementation(
        (successCallback: PositionCallback) => {
          successCallback(mockPosition);
        }
      );

      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      await vm.startWatchingPosition();
      vm.stopWatchingPosition();

      expect(mockGeolocation.clearWatch).toHaveBeenCalledWith(123);

      wrapper.unmount();
    });
  });

  describe('cleanup', () => {
    it('should clean up on unmount', async () => {
      const mockPosition: GeolocationPosition = {
        coords: {
          latitude: 13.7563,
          longitude: 100.5018,
          accuracy: 10,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
        },
        timestamp: Date.now(),
      };

      mockGeolocation.getCurrentPosition.mockImplementation(
        (successCallback: PositionCallback) => {
          successCallback(mockPosition);
        }
      );

      const wrapper = mount(createTestComponent());
      const vm = wrapper.vm as ReturnType<typeof useGeolocation>;

      await vm.startWatchingPosition();
      await flushPromises();

      wrapper.unmount();

      expect(mockGeolocation.clearWatch).toHaveBeenCalledWith(123);
    });
  });
});
