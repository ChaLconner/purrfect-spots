import { shallowRef } from 'vue';
import type { CatLocation } from '../types/api';
import { EXTERNAL_URLS } from '../utils/constants';

// Type for google maps objects (since we load them dynamically)
type GoogleMap = google.maps.Map;
type GoogleMarker = google.maps.Marker;

export function useMapMarkers(map: Ref<GoogleMap | null>) {
  // Use shallowRef for markers array to avoid deep reactivity overhead with Google Maps objects
  const markers = shallowRef<Map<string, GoogleMarker>>(new Map());
  const userMarker = shallowRef<GoogleMarker | null>(null);
  
  // Keep track of event listeners to clean them up
  const markerListeners = new Map<string, google.maps.MapsEventListener>();

  /**
   * Update markers based on current locations list (Diffing logic)
   */
  const updateMarkers = (locations: CatLocation[], onMarkerClick?: (cat: CatLocation) => void) => {
    if (!map.value) return;

    const currentIds = new Set(locations.map(l => l.id));
    const markersMap = markers.value;

    // 1. Remove markers that are no longer in the list
    for (const [id, marker] of markersMap.entries()) {
      if (!currentIds.has(id)) {
        marker.setMap(null);
        
        // Remove listener
        if (markerListeners.has(id)) {
          google.maps.event.removeListener(markerListeners.get(id)!);
          markerListeners.delete(id);
        }
        
        markersMap.delete(id);
      }
    }

    // 2. Add or Update markers
    locations.forEach(location => {
      const existingMarker = markersMap.get(location.id);

      if (existingMarker) {
        // Update position if changed (rare but possible)
        const currentPos = existingMarker.getPosition();
        if (currentPos && (
             Math.abs(currentPos.lat() - location.latitude) > 0.0001 || 
             Math.abs(currentPos.lng() - location.longitude) > 0.0001
           )) {
          existingMarker.setPosition({ lat: location.latitude, lng: location.longitude });
        }
      } else {
        // Create new marker
        const marker = new google.maps.Marker({
          position: { lat: location.latitude, lng: location.longitude },
          map: map.value,
          title: location.location_name || 'Cat Location',
          animation: google.maps.Animation.DROP,
          icon: {
            url: EXTERNAL_URLS.CAT_MARKER_ICON,
            scaledSize: new google.maps.Size(40, 40)
          }
        });

        // Add Click Listener
        if (onMarkerClick) {
          const listener = marker.addListener("click", () => {
            onMarkerClick(location);
          });
          markerListeners.set(location.id, listener);
        }

        markersMap.set(location.id, marker);
      }
    });
    
    // Trigger shallow update if needed (though Map mutation is internal)
    markers.value = markersMap;
  };

  /**
   * Update user location marker (Blue Dot)
   */
  const updateUserMarker = (position: { lat: number; lng: number } | null) => {
    if (!map.value) return;

    if (!position) {
      if (userMarker.value) {
        userMarker.value.setMap(null);
        userMarker.value = null;
      }
      return;
    }

    if (userMarker.value) {
      userMarker.value.setPosition(position);
    } else {
      userMarker.value = new google.maps.Marker({
        position: position,
        map: map.value,
        title: 'Your Location',
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: '#4285F4',
          fillOpacity: 1,
          strokeColor: '#FFFFFF',
          strokeWeight: 3,
        },
        zIndex: 999
      });
      
      const infoWindow = new google.maps.InfoWindow({
        content: '<div style="padding: 8px; font-family: sans-serif;"><strong>You are here</strong></div>'
      });
      
      userMarker.value.addListener('click', () => {
        if (map.value && userMarker.value) {
           infoWindow.open(map.value, userMarker.value);
        }
      });
    }
  };

  /**
   * Clear all markers
   */
  const clearMarkers = () => {
    markers.value.forEach(marker => marker.setMap(null));
    markers.value.clear();
    
    // Clear listeners
    markerListeners.forEach(listener => google.maps.event.removeListener(listener));
    markerListeners.clear();

    if (userMarker.value) {
      userMarker.value.setMap(null);
      userMarker.value = null;
    }
  };

  return {
    markers,
    userMarker,
    updateMarkers,
    updateUserMarker,
    clearMarkers
  };
}

// Helper type for Ref
type Ref<T> = import('vue').Ref<T>;
