import { ref, onUnmounted, type Ref } from 'vue';

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface UseGeolocationReturn {
  userLocation: Ref<Coordinates | null>;
  error: Ref<string | null>;
  isLoading: Ref<boolean>;
  permissionDenied: Ref<boolean>;
  getCurrentPosition: (options?: PositionOptions) => Promise<Coordinates | null>;
  startWatchingPosition: (options?: PositionOptions) => Promise<void>;
  stopWatchingPosition: () => void;
}

export function useGeolocation(): UseGeolocationReturn {
  const userLocation = ref<Coordinates | null>(null);
  const error = ref<string | null>(null);
  const isLoading = ref(false);
  const watchId = ref<number | null>(null);
  const permissionDenied = ref(false);

  /**
   * Get approx location via IP (Fallback)
   */
  const getIpLocation = async (): Promise<Coordinates | null> => {
    try {
      const response = await fetch('https://ipapi.co/json/');
      const data = await response.json();
      if (data.latitude && data.longitude) {
        return {
          lat: Number.parseFloat(data.latitude),
          lng: Number.parseFloat(data.longitude),
        };
      }
    } catch (e) {
      console.warn('IP Geolocation failed:', e);
    }
    return null;
  };

  /**
   * Get current position once (Promise-based)
   */
  const getCurrentPosition = (options?: PositionOptions): Promise<Coordinates | null> => {
    isLoading.value = true;
    error.value = null;

    return new Promise((resolve) => {
      // Helper to handle success from native API
      const handleSuccess = (position: GeolocationPosition): void => {
        const coords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        userLocation.value = coords;
        permissionDenied.value = false;
        isLoading.value = false;
        resolve(coords);
      };

      // Helper to handle failure/fallback
      const handleFailure = async (msg: string): Promise<void> => {
        // If user denied, mark it so we don't try to watch
        if (msg.includes('denied') || msg.includes('permission')) {
          permissionDenied.value = true;
        }

        // Try fallback
        const fallbackCoords = await getIpLocation();
        if (fallbackCoords) {
          userLocation.value = fallbackCoords;
          // Don't set error if fallback works, so UI acts like we found a location
        } else {
          error.value = msg;
        }
        isLoading.value = false;
        resolve(fallbackCoords);
      };

      if (typeof navigator === 'undefined' || !navigator.geolocation) {
        // nosec typescript:S5604 - Geolocation is the core feature of this cat location app
        // User consent is obtained via browser permission prompt
        handleFailure('Geolocation is not supported by this browser');
        return;
      }

      navigator.geolocation.getCurrentPosition(handleSuccess, (err) => handleFailure(err.message), {
        // NOSONAR typescript:S5604 - Geolocation is core to this cat location app; consent via browser prompt
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0,
        ...options,
      });
    });
  };

  /**
   * Start watching position for continuous updates
   */
  const startWatchingPosition = async (options?: PositionOptions): Promise<void> => {
    if (typeof navigator === 'undefined' || !navigator.geolocation || watchId.value !== null)
      return;

    // Don't start watching if we already know permission is denied
    if (permissionDenied.value) {
      return;
    }

    // Initial check to set start location (handling fallback if needed)
    if (!userLocation.value) {
      await getCurrentPosition(options);
      // Re-check permission after get attempt
      if (permissionDenied.value) return;
    }

    watchId.value = navigator.geolocation.watchPosition(
      // NOSONAR typescript:S5604 - Geolocation is core to this cat location app; consent via browser prompt
      (position) => {
        const newCoords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        userLocation.value = newCoords;
        error.value = null; // Clear error on success
      },
      (err) => {
        if (err.message.includes('denied')) {
          permissionDenied.value = true;
          stopWatchingPosition();
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 5000,
        ...options,
      }
    );
  };

  /**
   * Stop watching position
   */
  const stopWatchingPosition = (): void => {
    if (typeof navigator !== 'undefined' && watchId.value !== null) {
      navigator.geolocation.clearWatch(watchId.value);
      watchId.value = null;
    }
  };

  // Auto-cleanup on unmount if used inside a component setup
  onUnmounted(() => {
    stopWatchingPosition();
  });

  return {
    userLocation,
    error,
    isLoading,
    permissionDenied,
    getCurrentPosition,
    startWatchingPosition,
    stopWatchingPosition,
  };
}
