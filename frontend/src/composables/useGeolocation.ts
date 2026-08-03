import { ref, onUnmounted, getCurrentInstance, type Ref } from 'vue';

export interface Coordinates {
  lat: number;
  lng: number;
  accuracy: number | null;
  timestamp: number;
}

export type GeolocationStatus =
  | 'idle'
  | 'loading'
  | 'available'
  | 'stale'
  | 'denied'
  | 'unavailable';

export type GeolocationSource = 'gps' | 'manual' | 'approximate' | null;

export type GeolocationRequestOptions = PositionOptions & {
  /** IP location is approximate and must be opted into by the caller. */
  allowIpFallback?: boolean;
};

export interface UseGeolocationReturn {
  userLocation: Ref<Coordinates | null>;
  error: Ref<string | null>;
  isLoading: Ref<boolean>;
  permissionDenied: Ref<boolean>;
  isSupported: Ref<boolean>;
  locationStatus: Ref<GeolocationStatus>;
  locationSource: Ref<GeolocationSource>;
  lastUpdatedAt: Ref<number | null>;
  getCurrentPosition: (options?: GeolocationRequestOptions) => Promise<Coordinates | null>;
  startWatchingPosition: (options?: GeolocationRequestOptions) => Promise<void>;
  stopWatchingPosition: () => void;
  setManualLocation: (position: { lat: number; lng: number }) => Coordinates;
}

const STALE_AFTER_MS = 2 * 60 * 1000;

export function useGeolocation(): UseGeolocationReturn {
  const userLocation = ref<Coordinates | null>(null);
  const error = ref<string | null>(null);
  const isLoading = ref(false);
  const watchId = ref<number | null>(null);
  const permissionDenied = ref(false);
  const isSupported = ref(
    typeof navigator !== 'undefined' && 'geolocation' in navigator && !!navigator.geolocation
  );
  const locationStatus = ref<GeolocationStatus>('idle');
  const locationSource = ref<GeolocationSource>(null);
  const lastUpdatedAt = ref<number | null>(null);
  let staleTimer: ReturnType<typeof setTimeout> | null = null;

  const clearStaleTimer = (): void => {
    if (staleTimer !== null) {
      clearTimeout(staleTimer);
      staleTimer = null;
    }
  };

  const scheduleStaleTimer = (): void => {
    clearStaleTimer();
    staleTimer = setTimeout(() => {
      if (userLocation.value && locationStatus.value === 'available') {
        locationStatus.value = 'stale';
      }
    }, STALE_AFTER_MS);
  };

  const setLivePosition = (position: GeolocationPosition): Coordinates => {
    const timestamp = Number.isFinite(position.timestamp) ? position.timestamp : Date.now();
    const accuracy = Number.isFinite(position.coords.accuracy) && position.coords.accuracy >= 0
      ? position.coords.accuracy
      : null;
    const coords: Coordinates = {
      lat: position.coords.latitude,
      lng: position.coords.longitude,
      accuracy,
      timestamp,
    };

    userLocation.value = coords;
    locationSource.value = 'gps';
    lastUpdatedAt.value = timestamp;
    error.value = null;
    permissionDenied.value = false;
    locationStatus.value = 'available';
    scheduleStaleTimer();
    return coords;
  };

  /**
   * Get approximate location via IP. Callers must opt in because this is not
   * accurate enough to present as the user's current GPS position.
   */
  const getIpLocation = async (): Promise<Coordinates | null> => {
    try {
      const response = await fetch('/api/v1/geo/ip-location');
      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      const latitude = Number(data.latitude);
      const longitude = Number(data.longitude);
      if (
        data.latitude != null &&
        data.longitude != null &&
        Number.isFinite(latitude) &&
        Number.isFinite(longitude)
      ) {
        const approximateLocation: Coordinates = {
          lat: latitude,
          lng: longitude,
          accuracy: null,
          timestamp: Date.now(),
        };
        userLocation.value = approximateLocation;
        locationSource.value = 'approximate';
        lastUpdatedAt.value = approximateLocation.timestamp;
        locationStatus.value = 'stale';
        return approximateLocation;
      }
    } catch (fallbackError) {
      console.warn('IP Geolocation failed:', fallbackError);
    }
    return null;
  };

  const setManualLocation = (position: { lat: number; lng: number }): Coordinates => {
    clearStaleTimer();
    const manualLocation: Coordinates = {
      lat: position.lat,
      lng: position.lng,
      accuracy: null,
      timestamp: Date.now(),
    };
    userLocation.value = manualLocation;
    locationSource.value = 'manual';
    lastUpdatedAt.value = manualLocation.timestamp;
    locationStatus.value = 'available';
    error.value = null;
    return manualLocation;
  };

  const getCurrentPosition = (
    options: GeolocationRequestOptions = {}
  ): Promise<Coordinates | null> => {
    const { allowIpFallback = false, ...positionOptions } = options;
    isLoading.value = true;
    error.value = null;
    locationStatus.value = 'loading';

    return new Promise((resolve) => {
      const handleFailure = async (positionError: GeolocationPositionError | Error): Promise<void> => {
        const message = positionError.message || 'Unable to determine your location';
        const isDenied =
          ('code' in positionError && positionError.code === 1) ||
          message.toLowerCase().includes('denied') ||
          message.toLowerCase().includes('permission');

        permissionDenied.value = isDenied;
        error.value = message;
        locationStatus.value = isDenied
          ? 'denied'
          : userLocation.value
            ? 'stale'
            : 'unavailable';

        if (allowIpFallback) {
          const fallbackCoords = await getIpLocation();
          if (fallbackCoords) {
            error.value = null;
            isLoading.value = false;
            resolve(fallbackCoords);
            return;
          }
        }

        isLoading.value = false;
        resolve(null);
      };

      if (typeof navigator === 'undefined' || !navigator.geolocation) {
        isSupported.value = false;
        void handleFailure(new Error('Geolocation is not supported by this browser'));
        return;
      }

      isSupported.value = true;
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords = setLivePosition(position);
          isLoading.value = false;
          resolve(coords);
        },
        (positionError) => {
          void handleFailure(positionError);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
          ...positionOptions,
        }
      );
    });
  };

  const startWatchingPosition = async (
    options: GeolocationRequestOptions = {}
  ): Promise<void> => {
    const { allowIpFallback = false, ...positionOptions } = options;

    if (typeof navigator === 'undefined' || !navigator.geolocation || watchId.value !== null) {
      isSupported.value = false;
      return;
    }

    if (permissionDenied.value) {
      return;
    }

    if (!userLocation.value || locationStatus.value !== 'available') {
      const initialPosition = await getCurrentPosition({ allowIpFallback, ...positionOptions });
      if (!initialPosition || permissionDenied.value || locationStatus.value !== 'available') {
        return;
      }
    }

    watchId.value = navigator.geolocation.watchPosition(
      (position) => {
        setLivePosition(position);
      },
      (positionError) => {
        const isDenied = positionError.code === 1 || positionError.message.toLowerCase().includes('denied');
        permissionDenied.value = isDenied;
        error.value = positionError.message;
        locationStatus.value = isDenied
          ? 'denied'
          : userLocation.value
            ? 'stale'
            : 'unavailable';
        if (isDenied) {
          stopWatchingPosition();
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 5000,
        ...positionOptions,
      }
    );
  };

  const stopWatchingPosition = (): void => {
    if (typeof navigator !== 'undefined' && watchId.value !== null) {
      navigator.geolocation?.clearWatch(watchId.value);
      watchId.value = null;
    }
  };

  if (getCurrentInstance()) {
    onUnmounted(() => {
      stopWatchingPosition();
      clearStaleTimer();
    });
  }

  return {
    userLocation,
    error,
    isLoading,
    permissionDenied,
    isSupported,
    locationStatus,
    locationSource,
    lastUpdatedAt,
    getCurrentPosition,
    startWatchingPosition,
    stopWatchingPosition,
    setManualLocation,
  };
}
