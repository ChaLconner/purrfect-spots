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

  /**
   * Get current position once (Promise-based)
   */
  const getCurrentPosition = (options?: PositionOptions): Promise<Coordinates | null> => {
    isLoading.value = true;
    error.value = null;

    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        error.value = 'Geolocation is not supported by this browser';
        isLoading.value = false;
        resolve(null);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          userLocation.value = coords;
          isLoading.value = false;
          resolve(coords);
        },
        (err) => {
          error.value = err.message;
          console.warn('Geolocation error:', err.message);
          isLoading.value = false;
          resolve(null);
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 0,
          ...options
        }
      );
    });
  };

  /**
   * Start watching position for continuous updates
   */
  const startWatchingPosition = (options?: PositionOptions) => {
    if (!navigator.geolocation || watchId.value !== null) return;

    watchId.value = navigator.geolocation.watchPosition(
      (position) => {
        const newCoords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };

        // Update state
        userLocation.value = newCoords;
      },
      (err) => {
        console.warn('Watch position error:', err.message);
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
    getCurrentPosition,
    startWatchingPosition,
    stopWatchingPosition
  };
}
