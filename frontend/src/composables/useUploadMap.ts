import { ref, type Ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { showError } from '@/stores/toast';
import { useGeolocation } from '@/composables/useGeolocation';
export interface UseUploadMapOptions {
  onLocationUpdate: (lat: number, lng: number) => void;
  mapElementId?: string;
  defaultCenter?: { lat: number; lng: number };
}

export function useUploadMap(options: UseUploadMapOptions): {
  gettingLocation: Ref<boolean>;
  map: Ref<google.maps.Map | null>;
  marker: Ref<google.maps.Marker | null>;
  initMap: () => Promise<void>;
  updateLocation: (lat: number, lng: number) => void;
  getCurrentLocation: () => void;
} {
  const { t } = useI18n();
  const gettingLocation = ref(false);
  const map: Ref<google.maps.Map | null> = ref(null);
  const marker: Ref<google.maps.Marker | null> = ref(null);

  const initMap = async (): Promise<void> => {
    try {
      const [{ loadGoogleMaps }, { getEnvVar }] = await Promise.all([
        import('@/utils/googleMapsLoader'),
        import('@/utils/env'),
      ]);

      await loadGoogleMaps({ apiKey: getEnvVar('VITE_GOOGLE_MAPS_API_KEY') });

      const elementId = options.mapElementId || 'uploadMap';
      const mapEl = document.getElementById(elementId);
      if (!mapEl) return;

      const center = options.defaultCenter || { lat: 13.7563, lng: 100.5018 }; // Bangkok default

      map.value = new google.maps.Map(mapEl, {
        center,
        zoom: 12,
        disableDefaultUI: true,
        clickableIcons: false,
      });

      map.value.addListener('click', (e: google.maps.MapMouseEvent) => {
        if (e.latLng) {
          updateLocation(e.latLng.lat(), e.latLng.lng());
        }
      });
    } catch {
      showError(t('upload.errorMapLoad'), t('common.error'));
    }
  };

  const updateLocation = (lat: number, lng: number): void => {
    options.onLocationUpdate(lat, lng);

    if (marker.value) {
      marker.value.setPosition({ lat, lng });
    } else if (map.value) {
      marker.value = new google.maps.Marker({
        position: { lat, lng },
        map: map.value,
        animation: google.maps.Animation.DROP,
      });
    }
  };


  const { getCurrentPosition } = useGeolocation();

  const getCurrentLocation = async (): Promise<void> => {
    gettingLocation.value = true;
    try {
      const coords = await getCurrentPosition();
      if (coords) {
        updateLocation(coords.lat, coords.lng);
        if (map.value) {
          map.value.panTo({ lat: coords.lat, lng: coords.lng });
          map.value.setZoom(15);
        }
      } else {
        showError(t('upload.errorGeolocation'), 'Location Error');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Location Error';
      showError(message, 'Location Error');
    } finally {
      gettingLocation.value = false;
    }
  };

  return {
    gettingLocation,
    map,
    marker,
    initMap,
    updateLocation,
    getCurrentLocation,
  };
}
