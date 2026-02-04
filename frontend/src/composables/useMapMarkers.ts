/// <reference types="google.maps" />
import { shallowRef, watch, type Ref, onUnmounted } from 'vue';
import type { CatLocation } from '../types/api';
import { MarkerClusterer } from '@googlemaps/markerclusterer';

// Type for google maps objects (since we load them dynamically)
type GoogleMap = google.maps.Map;
// Use any for marker to support both legacy Marker and AdvancedMarkerElement in clusterer
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GoogleMarker = any;

export function useMapMarkers(map: Ref<GoogleMap | null>) {
  // Use shallowRef for markers array to avoid deep reactivity overhead with Google Maps objects
  const markers = shallowRef<Map<string, GoogleMarker>>(new Map());
  const userMarker = shallowRef<GoogleMarker | null>(null);
  const clusterer = shallowRef<MarkerClusterer | null>(null);

  // Keep track of event listeners to clean them up
  const markerListeners = new Map<string, google.maps.MapsEventListener>();

  // Watch for map changes to initialize/destroy clusterer
  watch(map, (newMap) => {
    if (newMap) {
      clusterer.value ??= new MarkerClusterer({ map: newMap });
    } else if (clusterer.value) {
      clusterer.value.clearMarkers();
      (clusterer.value as any).setMap(null); // eslint-disable-line @typescript-eslint/no-explicit-any
      clusterer.value = null;
    }
  });

  /**
   * Update markers based on current locations list (Diffing logic)
   */
  const updateMarkers = (locations: CatLocation[], onMarkerClick?: (cat: CatLocation) => void) => {
    if (!map.value) {
      return;
    }

    // Ensure clusterer exists if map exists
    // Custom renderer for Ghibli theme
    clusterer.value ??= new MarkerClusterer({ 
      map: map.value,
      renderer: {
        render: ({ count, position }) => {
          return new google.maps.Marker({
            position,
            label: {
              text: String(count),
              color: "white",
              fontSize: "14px",
              fontWeight: "bold",
            },
            icon: {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 18,
              fillColor: '#A65D37', // Ghibli Theme Primary (Brown)
              fillOpacity: 0.9,
              strokeColor: "white",
              strokeWeight: 2,
            },
            // Adjust zIndex to be above other markers
            zIndex: Number(google.maps.Marker.MAX_ZINDEX) + count,
          });
        }
      }
    });

    const currentIds = new Set(locations.map((l) => l.id));
    const markersMap = markers.value;
    const markersToRemove: GoogleMarker[] = [];
    const markersToAdd: GoogleMarker[] = [];

    // 1. Remove markers that are no longer in the list
    for (const [id, marker] of markersMap.entries()) {
      if (!currentIds.has(id)) {
        markersToRemove.push(marker);

        // Remove listener
        if (markerListeners.has(id)) {
          google.maps.event.removeListener(markerListeners.get(id)!);
          markerListeners.delete(id);
        }

        markersMap.delete(id);
      }
    }

    // 2. Add or Update markers
    locations.forEach((location) => {
      const existingMarker = markersMap.get(location.id);

      if (existingMarker) {
        // OPTIMIZATION: Skip position check if no significant change
        // Only update if position changed significantly (more than 0.001 degrees)
        // AdvancedMarkerElement uses 'position' property, not getPosition() method
        const currentPos = existingMarker.position;
        if (currentPos) {
          const lat = typeof currentPos.lat === 'function' ? currentPos.lat() : currentPos.lat;
          const lng = typeof currentPos.lng === 'function' ? currentPos.lng() : currentPos.lng;
          if (
            Math.abs(lat - location.latitude) > 0.001 ||
            Math.abs(lng - location.longitude) > 0.001
          ) {
            // AdvancedMarkerElement uses position property assignment
            existingMarker.position = { lat: location.latitude, lng: location.longitude };
          }
        }
      } else {
        // Create new marker
        // Important: Do not set 'map' property, let clusterer handle it
        
        // Defensive check for AdvancedMarkerElement
        if (!google.maps.marker || !google.maps.marker.AdvancedMarkerElement) {
          console.warn('AdvancedMarkerElement NOT available, falling back to legacy Marker');
          const marker = new google.maps.Marker({
            position: { lat: location.latitude, lng: location.longitude },
            title: location.location_name || 'Cat Location',
          });
          
          if (onMarkerClick) {
            const listener = marker.addListener('click', () => {
              onMarkerClick(location);
            });
            markerListeners.set(location.id, listener);
          }
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          markersToAdd.push(marker as any);
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          markersMap.set(location.id, marker as any);
          return;
        }

        // Force Legacy Marker for stability
        // AdvancedMarkerElement seems to have issues with current configuration/browser
        const marker = new google.maps.Marker({
          position: { lat: location.latitude, lng: location.longitude },
          title: location.location_name || 'Cat Location',
          // map: map.value, // REMOVED: Let Clusterer manage the map
          icon: {
            url: '/location_10753796.png',
            scaledSize: new google.maps.Size(40, 40),
            anchor: new google.maps.Point(20, 20), // Center anchor
          },
        });
        // Add Click Listener - Use 'click' for Legacy Marker
        if (onMarkerClick) {
          const listener = marker.addListener('click', () => {
            onMarkerClick(location);
          });
          markerListeners.set(location.id, listener);
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        markersToAdd.push(marker as any);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        markersMap.set(location.id, marker as any);
      }
    });

    // Apply batch updates to clusterer
    if (markersToRemove.length > 0) {
      clusterer.value.removeMarkers(markersToRemove, true); // true = noDraw (defer redraw)
    }

    if (markersToAdd.length > 0) {
      clusterer.value.addMarkers(markersToAdd, true); // true = noDraw
    }

    // Perform redraw once if changes occured
    if (markersToRemove.length > 0 || markersToAdd.length > 0) {
      clusterer.value.render();
    }

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
        // AdvancedMarkerElement uses 'map' property assignment, not setMap()
        userMarker.value.map = null;
        userMarker.value = null;
      }
      return;
    }

    if (userMarker.value) {
      // AdvancedMarkerElement uses 'position' property assignment, not setPosition()
      userMarker.value.position = position;
    } else {
      // Use AdvancedMarkerElement for user marker as well for consistency
      if (google.maps.marker && google.maps.marker.AdvancedMarkerElement) {
        // Create a custom element for the user blue dot
        const pinElement = document.createElement('div');
        pinElement.className = 'user-location-marker';
        pinElement.style.width = '20px';
        pinElement.style.height = '20px';
        pinElement.style.backgroundColor = '#4285F4';
        pinElement.style.border = '3px solid white';
        pinElement.style.borderRadius = '50%';
        pinElement.style.boxShadow = '0 0 10px rgba(0,0,0,0.3)';

        userMarker.value = new google.maps.marker.AdvancedMarkerElement({
          position: position,
          map: map.value,
          title: 'Your Location',
          content: pinElement,
          zIndex: 999,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
        }) as any;
      } else {
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
      }

      const infoWindow = new google.maps.InfoWindow({
        content:
          '<div style="padding: 8px; font-family: sans-serif;"><strong>You are here</strong></div>',
      });

      if (userMarker.value) {
        // Use 'gmp-click' for AdvancedMarkerElement, 'click' for legacy Marker
        const eventName = google.maps.marker?.AdvancedMarkerElement ? 'gmp-click' : 'click';
        userMarker.value.addListener(eventName, () => {
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
  const clearMarkers = () => {
    if (clusterer.value) {
      clusterer.value.clearMarkers();
    }

    markers.value.clear();

    // Clear listeners
    markerListeners.forEach((listener) => google.maps.event.removeListener(listener));
    markerListeners.clear();

    if (userMarker.value) {
      // AdvancedMarkerElement uses 'map' property assignment, not setMap()
      userMarker.value.map = null;
      userMarker.value = null;
    }
  };

  onUnmounted(() => {
    clearMarkers();
    if (clusterer.value) {
      (clusterer.value as any).setMap(null); // eslint-disable-line @typescript-eslint/no-explicit-any
      clusterer.value = null;
    }
  });

  return {
    markers,
    userMarker,
    updateMarkers,
    updateUserMarker,
    clearMarkers,
  };
}
