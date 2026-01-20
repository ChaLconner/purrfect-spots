import { ref, onUnmounted } from 'vue';

export interface Coordinates {
  lat: number;
  lng: number;
}

export function useGeolocation() {
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
          lat: parseFloat(data.latitude), 
          lng: parseFloat(data.longitude) 
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

    return new Promise(async (resolve) => {
      // Helper to handle success from native API
      const handleSuccess = (position: GeolocationPosition) => {
        const coords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        userLocation.value = coords;
        permissionDenied.value = false;
        isLoading.value = false;
        resolve(coords);
      };

      // Helper to handle failure/fallback
      const handleFailure = async (msg: string) => {
        // If user denied, mark it so we don't try to watch
        if (msg.includes("denied") || msg.includes("permission")) {
            permissionDenied.value = true;
        }
        
        // eslint-disable-next-line no-console
        console.debug('Geolocation error/denied:', msg);
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

      if (!navigator.geolocation) {
        await handleFailure('Geolocation is not supported by this browser');
        return;
      }

      navigator.geolocation.getCurrentPosition(
        handleSuccess,
        (err) => handleFailure(err.message),
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0,
          ...options
        }
      );
    });
  };

  /**
   * Start watching position for continuous updates
   */
  const startWatchingPosition = async (options?: PositionOptions) => {
    if (!navigator.geolocation || watchId.value !== null) return;
    
    // Don't start watching if we already know permission is denied
    if (permissionDenied.value) {
        // eslint-disable-next-line no-console
        console.debug('Skipping watchPosition: Permission previously denied');
        return;
    }

    // Initial check to set start location (handling fallback if needed)
    if (!userLocation.value) {
      await getCurrentPosition(options);
      // Re-check permission after get attempt
      if (permissionDenied.value) return; 
    }

    watchId.value = navigator.geolocation.watchPosition(
      (position) => {
        const newCoords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        userLocation.value = newCoords;
        error.value = null; // Clear error on success
      },
      (err) => {
        // eslint-disable-next-line no-console
        console.debug('Watch position error:', err.message);
        if (err.message.includes("denied")) {
             permissionDenied.value = true;
             stopWatchingPosition();
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 5000,
        ...options
      }
    );
  };

  /**
   * Stop watching position
   */
  const stopWatchingPosition = () => {
    if (watchId.value !== null) {
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
    stopWatchingPosition
  };
}
