/// <reference types="google.maps" />
import { shallowRef, watch, type Ref, onUnmounted, getCurrentInstance, type ShallowRef } from 'vue';
import type { CatLocation } from '../types/api';
import { MarkerClusterer, SuperClusterAlgorithm } from '@googlemaps/markerclusterer';

// Type for google maps objects (since we load them dynamically)
type GoogleMap = google.maps.Map;

type GoogleMarker = google.maps.Marker | google.maps.marker.AdvancedMarkerElement;
const markerIconCache = new Map<string, string>();
const MARKER_ICON_CACHE_MAX_SIZE = 200;

export function useMapMarkers(map: Ref<GoogleMap | null>): {
  markers: ShallowRef<Map<string, GoogleMarker>>;
  userMarker: ShallowRef<GoogleMarker | null>;
  updateMarkers: (locations: CatLocation[], onMarkerClick?: (cat: CatLocation) => void) => void;
  updateUserMarker: (position: { lat: number; lng: number } | null) => void;
  clearMarkers: () => void;
} {
  // Use shallowRef for markers array to avoid deep reactivity overhead with Google Maps objects
  const markers = shallowRef<Map<string, GoogleMarker>>(new Map());
  const userMarker = shallowRef<GoogleMarker | null>(null);

  const removeUserMarker = (): void => {
    if (!userMarker.value) return;
    if (userMarker.value instanceof google.maps.Marker) {
      userMarker.value.setMap(null);
    } else if (
      google.maps.marker?.AdvancedMarkerElement &&
      userMarker.value instanceof google.maps.marker.AdvancedMarkerElement
    ) {
      userMarker.value.map = null;
    }
    userMarker.value = null;
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
      icon: {
        url: '/location_10753796.png',
        scaledSize: new google.maps.Size(40, 40),
        anchor: new google.maps.Point(20, 20),
      },
    });

    if (location.image_url) {
      const cachedIcon = markerIconCache.get(location.image_url);
      if (cachedIcon) {
        marker.setIcon({
          url: cachedIcon,
          scaledSize: new google.maps.Size(52, 68),
          anchor: new google.maps.Point(26, 64),
        });
      } else {
        const img = new Image();
        img.crossOrigin = 'Anonymous';
        img.decoding = 'async';
        img.width = 52;
        img.height = 52;
        img.src = location.image_url;
        img.onload = (): void => {
          const canvas = document.createElement('canvas');
          const size = 52;
          canvas.width = size;
          canvas.height = size + 16;
          const ctx = canvas.getContext('2d');
          if (!ctx) return;

          const cx = size / 2;
          const cy = size / 2;
          const r = size / 2 - 2;

          ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
          ctx.shadowBlur = 4;
          ctx.shadowOffsetY = 2;

          ctx.fillStyle = '#d97757'; // location-badge color
          ctx.beginPath();
          ctx.arc(cx, cy, r, Math.PI * 0.2, Math.PI * 0.8, true);
          ctx.lineTo(cx, canvas.height - 4);
          ctx.closePath();
          ctx.fill();

          ctx.shadowColor = 'transparent';

          ctx.save();
          ctx.beginPath();
          ctx.arc(cx, cy, r - 3, 0, Math.PI * 2);
          ctx.clip();

          const d = (r - 3) * 2;
          const imgAspect = img.width / img.height;
          let drawWidth = d;
          let drawHeight = d;

          if (imgAspect > 1) {
            drawWidth = d * imgAspect;
          } else {
            drawHeight = d / imgAspect;
          }

          const drawX = cx - drawWidth / 2;
          const drawY = cy - drawHeight / 2;

          ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
          ctx.restore();

          const iconUrl = canvas.toDataURL();
          if (markerIconCache.size >= MARKER_ICON_CACHE_MAX_SIZE) {
            const oldest = markerIconCache.keys().next().value;
            if (oldest) markerIconCache.delete(oldest);
          }
          markerIconCache.set(location.image_url, iconUrl);
          marker.setIcon({
            url: iconUrl,
            scaledSize: new google.maps.Size(size, size + 16),
            anchor: new google.maps.Point(size / 2, size + 12),
          });
        };

        img.onerror = (): void => {
          marker.setIcon({
            url: location.image_url,
            scaledSize: new google.maps.Size(40, 40),
            anchor: new google.maps.Point(20, 20),
          });
        };
      }
    }

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
  const updateUserMarker = (position: { lat: number; lng: number } | null): void => {
    if (!map.value) return;

    if (!position) {
      removeUserMarker();
      return;
    }

    if (userMarker.value) {
      // Update existing marker
      if (userMarker.value instanceof google.maps.Marker) {
        userMarker.value.setPosition(position);
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
        title: 'Your Location',
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: '#4285F4',
          fillOpacity: 1,
          strokeColor: '#FFFFFF',
          strokeWeight: 3,
        },
        zIndex: 999,
      });

      const infoWindow = new google.maps.InfoWindow({
        content:
          '<div class="p-2 font-sans"><strong>You are here</strong></div>',
      });

      if (userMarker.value) {
        // Use 'click' for legacy Marker
        userMarker.value.addListener('click', () => {
          if (map.value && userMarker.value) {
            infoWindow.open(map.value, userMarker.value);
          }
        });
      }
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
    clearMarkers,
  };
}
