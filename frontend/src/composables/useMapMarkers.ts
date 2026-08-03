/// <reference types="google.maps" />
import { shallowRef, watch, type Ref, onUnmounted, getCurrentInstance, type ShallowRef } from 'vue';
import type { CatLocation } from '../types/api';
import { EXTERNAL_URLS } from '../utils/constants';
import { MarkerClusterer, SuperClusterAlgorithm } from '@googlemaps/markerclusterer';

// Type for google maps objects (since we load them dynamically)
type GoogleMap = google.maps.Map;

type GoogleMarker = google.maps.Marker | google.maps.marker.AdvancedMarkerElement;
const markerIconCache = new Map<string, string>();
const MARKER_ICON_CACHE_MAX_SIZE = 200;
const CAT_MARKER_SIZE = 52;
const CAT_MARKER_HEIGHT = 72;
const CAT_MARKER_ICON = EXTERNAL_URLS.CAT_MARKER_ICON;
const CAT_MARKER_THEME_FALLBACKS = {
  fill: '#d67a4f',
  outline: '#a65d37',
  inner: '#faf6ec',
} as const;

const readThemeColor = (variable: string, fallback: string): string => {
  if (typeof window === 'undefined') return fallback;

  return window.getComputedStyle(document.documentElement).getPropertyValue(variable).trim() || fallback;
};

const getCatMarkerTheme = (): typeof CAT_MARKER_THEME_FALLBACKS => ({
  fill: readThemeColor('--color-terracotta', CAT_MARKER_THEME_FALLBACKS.fill),
  outline: readThemeColor('--color-terracotta-dark', CAT_MARKER_THEME_FALLBACKS.outline),
  inner: readThemeColor('--color-cream', CAT_MARKER_THEME_FALLBACKS.inner),
});

const createThemedCatMarkerIcon = (image: HTMLImageElement): string | null => {
  const canvas = document.createElement('canvas');
  canvas.width = CAT_MARKER_SIZE;
  canvas.height = CAT_MARKER_HEIGHT;

  const context = canvas.getContext('2d');
  if (!context) return null;

  const theme = getCatMarkerTheme();
  const centerX = CAT_MARKER_SIZE / 2;
  const centerY = 25;
  const outerRadius = 23;
  const tipY = CAT_MARKER_HEIGHT - 2;
  const imageRadius = outerRadius - 4;

  context.save();
  context.shadowColor = 'rgba(66, 33, 16, 0.28)';
  context.shadowBlur = 4;
  context.shadowOffsetY = 2;
  context.beginPath();
  context.moveTo(centerX, tipY);
  context.bezierCurveTo(
    centerX - 3,
    tipY - 7,
    centerX - outerRadius,
    centerY + 8,
    centerX - outerRadius,
    centerY
  );
  context.arc(centerX, centerY, outerRadius, Math.PI, 0, false);
  context.bezierCurveTo(
    centerX + outerRadius,
    centerY + 8,
    centerX + 3,
    tipY - 7,
    centerX,
    tipY
  );
  context.closePath();
  context.fillStyle = theme.fill;
  context.fill();
  context.shadowColor = 'transparent';
  context.strokeStyle = theme.outline;
  context.lineWidth = 2;
  context.stroke();
  context.restore();

  context.save();
  context.beginPath();
  context.arc(centerX, centerY, imageRadius, 0, Math.PI * 2);
  context.fillStyle = theme.inner;
  context.fill();
  context.clip();

  const sourceWidth = image.naturalWidth || image.width || CAT_MARKER_SIZE;
  const sourceHeight = image.naturalHeight || image.height || CAT_MARKER_SIZE;
  const diameter = imageRadius * 2;
  const scale = Math.max(diameter / sourceWidth, diameter / sourceHeight);
  const drawWidth = sourceWidth * scale;
  const drawHeight = sourceHeight * scale;
  context.drawImage(
    image,
    centerX - drawWidth / 2,
    centerY - drawHeight / 2,
    drawWidth,
    drawHeight
  );
  context.restore();

  return canvas.toDataURL('image/png');
};

type UserLocationPosition = { lat: number; lng: number };
type UserLocationMarkerOptions = {
  accuracy?: number | null;
  stale?: boolean;
  title?: string;
};
export function useMapMarkers(map: Ref<GoogleMap | null>): {
  markers: ShallowRef<Map<string, GoogleMarker>>;
  userMarker: ShallowRef<GoogleMarker | null>;
  updateMarkers: (locations: CatLocation[], onMarkerClick?: (cat: CatLocation) => void) => void;
  updateUserMarker: (position: UserLocationPosition | null, options?: UserLocationMarkerOptions) => void;
  updateUserRadiusCircle: (radiusKm: number | null, center?: UserLocationPosition | null) => void;
  clearMarkers: () => void;
} {
  // Use shallowRef for markers array to avoid deep reactivity overhead with Google Maps objects
  const markers = shallowRef<Map<string, GoogleMarker>>(new Map());
  const userMarker = shallowRef<GoogleMarker | null>(null);
  const userAccuracyCircle = shallowRef<google.maps.Circle | null>(null);
  const userRadiusCircle = shallowRef<google.maps.Circle | null>(null);
  const markerImageUrls = new Map<string, string>();
  const markerImageTokens = new Map<string, symbol>();

  const removeUserAccuracyCircle = (): void => {
    userAccuracyCircle.value?.setMap(null);
    userAccuracyCircle.value = null;
  };

  const removeUserRadiusCircle = (): void => {
    userRadiusCircle.value?.setMap(null);
    userRadiusCircle.value = null;
  };

  const removeUserMarker = (): void => {
    if (userMarker.value) {
      if (userMarker.value instanceof google.maps.Marker) {
        userMarker.value.setMap(null);
      } else if (
        google.maps.marker?.AdvancedMarkerElement &&
        userMarker.value instanceof google.maps.marker.AdvancedMarkerElement
      ) {
        userMarker.value.map = null;
      }
      userMarker.value = null;
    }
    removeUserAccuracyCircle();
    removeUserRadiusCircle();
  };
  const clusterer = shallowRef<MarkerClusterer | null>(null);

  // Keep track of event listeners to clean them up
  const markerListeners = new Map<string, google.maps.MapsEventListener>();

  // Clusterer Options
  const clustererOptions = {
    algorithm: new SuperClusterAlgorithm({ radius: 60, maxZoom: 16 }),
    renderer: {
      render: ({
        count,
        position,
      }: {
        count: number;
        position: google.maps.LatLng;
      }): google.maps.Marker => {
        return new google.maps.Marker({
          position,
          label: {
            text: String(count),
            color: 'white',
            fontSize: '14px',
            fontWeight: 'bold',
          },
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 18,
            fillColor: '#A65D37',
            fillOpacity: 0.9,
            strokeColor: 'white',
            strokeWeight: 2,
          },
          // Safety check for MAX_ZINDEX which might be missing in some type defs or versions
          zIndex: (google.maps.Marker.MAX_ZINDEX || 1000000) + count,
        });
      },
    },
  };

  const getFallbackCatMarkerIcon = (): google.maps.Icon => ({
    url: CAT_MARKER_ICON,
    scaledSize: new google.maps.Size(40, 40),
    anchor: new google.maps.Point(20, 20),
  });

  const setCachedCatMarkerIcon = (imageUrl: string, iconUrl: string): void => {
    if (markerIconCache.size >= MARKER_ICON_CACHE_MAX_SIZE) {
      const oldest = markerIconCache.keys().next().value;
      if (oldest) markerIconCache.delete(oldest);
    }
    markerIconCache.set(imageUrl, iconUrl);
  };

  const setImageCatMarker = (
    id: string,
    marker: google.maps.Marker,
    imageUrl: string
  ): void => {
    markerImageUrls.set(id, imageUrl);

    const cachedIcon = markerIconCache.get(imageUrl);
    if (cachedIcon) {
      marker.setIcon({
        url: cachedIcon,
        scaledSize: new google.maps.Size(CAT_MARKER_SIZE, CAT_MARKER_HEIGHT),
        anchor: new google.maps.Point(CAT_MARKER_SIZE / 2, CAT_MARKER_HEIGHT - 4),
      });
      return;
    }

    const token = Symbol(id);
    markerImageTokens.set(id, token);
    const image = new Image();
    image.crossOrigin = 'anonymous';
    image.decoding = 'async';
    image.width = CAT_MARKER_SIZE;
    image.height = CAT_MARKER_SIZE;

    image.onload = (): void => {
      if (markerImageTokens.get(id) !== token) return;

      const iconUrl = createThemedCatMarkerIcon(image);
      if (!iconUrl) {
        marker.setIcon({
          url: imageUrl,
          scaledSize: new google.maps.Size(40, 40),
          anchor: new google.maps.Point(20, 20),
        });
        markerImageTokens.delete(id);
        return;
      }

      setCachedCatMarkerIcon(imageUrl, iconUrl);
      marker.setIcon({
        url: iconUrl,
        scaledSize: new google.maps.Size(CAT_MARKER_SIZE, CAT_MARKER_HEIGHT),
        anchor: new google.maps.Point(CAT_MARKER_SIZE / 2, CAT_MARKER_HEIGHT - 4),
      });
      markerImageTokens.delete(id);
    };

    image.onerror = (): void => {
      if (markerImageTokens.get(id) !== token) return;

      marker.setIcon({
        url: imageUrl,
        scaledSize: new google.maps.Size(40, 40),
        anchor: new google.maps.Point(20, 20),
      });
      markerImageTokens.delete(id);
    };

    image.src = imageUrl;
  };

  const updateCatMarkerImage = (
    id: string,
    marker: google.maps.Marker,
    imageUrl?: string
  ): void => {
    markerImageTokens.delete(id);

    if (!imageUrl) {
      markerImageUrls.set(id, '');
      marker.setIcon(getFallbackCatMarkerIcon());
      return;
    }

    setImageCatMarker(id, marker, imageUrl);
  };

  // Watch for map changes to initialize/destroy clusterer
  watch(map, (newMap) => {
    if (newMap) {
      clusterer.value ??= new MarkerClusterer({ map: newMap, ...clustererOptions });
    } else if (clusterer.value) {
      clusterer.value.clearMarkers();
      clusterer.value = null;
    }
  });

  /**
   * Update markers based on current locations list (Diffing logic)
   */
  const getMarkerPosition = (marker: GoogleMarker): { lat: number; lng: number } | null => {
    // Check if it's an AdvancedMarkerElement (has 'position' property directly accessible)
    // Legacy Marker uses getPosition()
    if (marker instanceof google.maps.Marker) {
      const pos = marker.getPosition();
      if (!pos) return null;
      return { lat: pos.lat(), lng: pos.lng() };
    } else if (
      google.maps.marker?.AdvancedMarkerElement &&
      marker instanceof google.maps.marker.AdvancedMarkerElement
    ) {
      // AdvancedMarkerElement
      const pos = marker.position;
      if (!pos) return null;
      // AdvancedMarkerElement position can be LatLng or LatLngLiteral
      const lat = typeof pos.lat === 'function' ? pos.lat() : pos.lat;
      const lng = typeof pos.lng === 'function' ? pos.lng() : pos.lng;
      return { lat, lng };
    }
    return null;
  };

  const createMarker = (
    location: CatLocation,
    onMarkerClick?: (cat: CatLocation) => void
  ): google.maps.Marker => {
    // Use Legacy Marker for consistent display of custom icons
    // AdvancedMarkerElement requires a valid Map ID and Vector Map, which can be flaky in some envs

    // Fallback to Legacy Marker
    const marker = new google.maps.Marker({
      position: { lat: location.latitude, lng: location.longitude },
      title: location.location_name || 'Cat Location',
      icon: getFallbackCatMarkerIcon(),
    });

    updateCatMarkerImage(location.id, marker, location.image_url);

    if (onMarkerClick) {
      const listener = marker.addListener('click', () => onMarkerClick(location));
      markerListeners.set(location.id, listener);
    }

    return marker;
  };

  const updateExistingMarker = (marker: GoogleMarker, location: CatLocation): void => {
    const currentPos = getMarkerPosition(marker);
    if (currentPos) {
      if (
        Math.abs(currentPos.lat - location.latitude) > 0.0001 ||
        Math.abs(currentPos.lng - location.longitude) > 0.0001
      ) {
        if (
          google.maps.marker?.AdvancedMarkerElement &&
          marker instanceof google.maps.marker.AdvancedMarkerElement
        ) {
          marker.position = { lat: location.latitude, lng: location.longitude };
        } else {
          (marker as google.maps.Marker).setPosition({
            lat: location.latitude,
            lng: location.longitude,
          });
        }
      }
    }

    if (marker instanceof google.maps.Marker) {
      const imageUrl = location.image_url || '';
      if (markerImageUrls.get(location.id) !== imageUrl) {
        updateCatMarkerImage(location.id, marker, location.image_url);
      }
    }
  };

  const updateMarkers = (
    locations: CatLocation[],
    onMarkerClick?: (cat: CatLocation) => void
  ): void => {
    if (!map.value) return;

    // Markers update successfully triggered
    // Logger removed to reduce console noise during high-frequency reactivity

    // Ensure clusterer is initialized with options if not already
    clusterer.value ??= new MarkerClusterer({
      map: map.value,
      ...clustererOptions,
    });

    const currentIds = new Set(locations.map((l) => l.id));
    const markersMap = markers.value;
    const markersToRemove: GoogleMarker[] = [];
    const markersToAdd: GoogleMarker[] = [];

    // 1. Remove markers
    for (const [id, marker] of markersMap.entries()) {
      if (!currentIds.has(id)) {
        markersToRemove.push(marker);
        if (markerListeners.has(id)) {
          const listener = markerListeners.get(id);
          if (listener) {
            google.maps.event.removeListener(listener);
          }
          markerListeners.delete(id);
        }
        markerImageTokens.delete(id);
        markerImageUrls.delete(id);
        markersMap.delete(id);
      }
    }

    // 2. Add or Update markers
    locations.forEach((location) => {
      const existingMarker = markersMap.get(location.id);
      if (existingMarker) {
        updateExistingMarker(existingMarker, location);
      } else {
        const marker = createMarker(location, onMarkerClick);
        markersToAdd.push(marker);
        markersMap.set(location.id, marker);
      }
    });

    if (markersToRemove.length > 0) clusterer.value.removeMarkers(markersToRemove, true);
    if (markersToAdd.length > 0) clusterer.value.addMarkers(markersToAdd, true);

    if (markersToRemove.length > 0 || markersToAdd.length > 0) {
      clusterer.value.render();
    }

    markers.value = markersMap;
  };

  /**
   * Update user location marker (Blue Dot)
   */
  const updateUserMarker = (
    position: UserLocationPosition | null,
    options: UserLocationMarkerOptions = {}
  ): void => {
    if (!map.value) return;

    if (!position) {
      removeUserMarker();
      return;
    }

    const stale = options.stale ?? false;
    const markerColor = stale ? '#7b8794' : '#4285F4';
    const strokeColor = stale ? '#f3f4f6' : '#FFFFFF';
    const markerIcon = {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 10,
      fillColor: markerColor,
      fillOpacity: stale ? 0.72 : 1,
      strokeColor,
      strokeWeight: 3,
    };

    if (userMarker.value) {
      // Update existing marker
      if (userMarker.value instanceof google.maps.Marker) {
        userMarker.value.setPosition(position);
        userMarker.value.setIcon(markerIcon);
        userMarker.value.setTitle(options.title || 'Your location');
      } else if (
        google.maps.marker?.AdvancedMarkerElement &&
        userMarker.value instanceof google.maps.marker.AdvancedMarkerElement
      ) {
        // AdvancedMarkerElement
        userMarker.value.position = position;
      }
    } else {
      // Use Legacy Marker for user location as well (consistent with cat markers)
      userMarker.value = new google.maps.Marker({
        position: position,
        map: map.value, // User marker is NOT clustered, add to map directly
        title: options.title || 'Your location',
        icon: markerIcon,
        zIndex: 999,
      });
    }

    const accuracy = options.accuracy;
    if (accuracy !== undefined && accuracy !== null && Number.isFinite(accuracy) && accuracy > 0) {
      const circleOptions: google.maps.CircleOptions = {
        center: position,
        radius: accuracy,
        map: map.value,
        strokeColor: markerColor,
        strokeOpacity: stale ? 0.25 : 0.45,
        strokeWeight: 1,
        fillColor: markerColor,
        fillOpacity: stale ? 0.06 : 0.12,
        clickable: false,
        zIndex: 998,
      };

      if (userAccuracyCircle.value) {
        userAccuracyCircle.value.setOptions(circleOptions);
      } else {
        userAccuracyCircle.value = new google.maps.Circle(circleOptions);
      }
    } else {
      removeUserAccuracyCircle();
    }
  };

  const updateUserRadiusCircle = (
    radiusKm: number | null,
    center: UserLocationPosition | null = null
  ): void => {
    if (!map.value || !center || radiusKm === null || !Number.isFinite(radiusKm) || radiusKm <= 0) {
      removeUserRadiusCircle();
      return;
    }

    const circleOptions: google.maps.CircleOptions = {
      center,
      radius: radiusKm * 1000,
      map: map.value,
      strokeColor: '#A65D37',
      strokeOpacity: 0.55,
      strokeWeight: 1.5,
      fillColor: '#D67A4F',
      fillOpacity: 0.04,
      clickable: false,
      zIndex: 997,
    };

    if (userRadiusCircle.value) {
      userRadiusCircle.value.setOptions(circleOptions);
    } else {
      userRadiusCircle.value = new google.maps.Circle(circleOptions);
    }
  };

  /**
   * Clear all markers
   */
  const clearMarkers = (): void => {
    if (clusterer.value) {
      clusterer.value.clearMarkers();
    }

    markers.value.clear();

    // Clear listeners
    markerListeners.forEach((listener) => google.maps.event.removeListener(listener));
    markerListeners.clear();
    markerImageTokens.clear();
    markerImageUrls.clear();

    removeUserMarker();
  };

  if (getCurrentInstance()) {
    onUnmounted(() => {
      clearMarkers();
      if (clusterer.value) {
        clusterer.value.clearMarkers();
        clusterer.value = null;
      }
    });
  }

  return {
    markers,
    userMarker,
    updateMarkers,
    updateUserMarker,
    updateUserRadiusCircle,
    clearMarkers,
  };
}
