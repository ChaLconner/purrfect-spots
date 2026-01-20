import { ref, shallowRef, watch } from 'vue';
import { getGoogleMaps, loadGoogleMaps } from '../utils/googleMapsLoader';
import { getEnvVar } from '../utils/env';
import { showError, addToast } from '../store/toast';

interface Coordinates {
  lat: number;
  lng: number;
}

interface LocationPickerOptions {
  initialLat?: number;
  initialLng?: number;
  mapElementId?: string;
}

export function useLocationPicker(options: LocationPickerOptions = {}) {
  // Default center for initial map view (Thailand center)
  const DEFAULT_MAP_CENTER = { lat: 13.7563, lng: 100.5018 };
  const DEFAULT_ZOOM_NO_SELECTION = 6; // Zoomed out to show more area
  const DEFAULT_ZOOM_WITH_SELECTION = 15; // Zoomed in when location selected
  
  const latitude = ref("");
  const longitude = ref("");
  const hasSelectedLocation = ref(false);
  
  const mapCenter = shallowRef<Coordinates>(DEFAULT_MAP_CENTER);
  
  const mapInstance = shallowRef<google.maps.Map | null>(null);
  const mapMarker = shallowRef<google.maps.Marker | null>(null);
  const gettingLocation = ref(false);
  const mapElementId = options.mapElementId || "uploadMap";

  const googleMapsApiKey = getEnvVar('VITE_GOOGLE_MAPS_API_KEY');

  const markerIcon = Object.freeze({
    url: "/location_10753796.png",
    scaledSize: { width: 32, height: 32 }
  });

  const hoverIcon = Object.freeze({
    url: "/location_10753796.png",
    scaledSize: { width: 38, height: 38 }
  });

  // Helper to update all coordinate refs and create marker if needed
  const setCoordinates = (lat: number, lng: number) => {
    latitude.value = lat.toFixed(6);
    longitude.value = lng.toFixed(6);
    mapCenter.value = { lat, lng };
    hasSelectedLocation.value = true;
    
    // Create marker if it doesn't exist yet
    if (!mapMarker.value && mapInstance.value) {
      createDraggableMarker({ lat, lng });
    }
    
    debouncedUpdateMap();
    
    // Zoom in when location is selected
    if (mapInstance.value) {
      mapInstance.value.setZoom(DEFAULT_ZOOM_WITH_SELECTION);
    }
  };

  const createMarkerWithHover = (position: Coordinates, title: string, map: google.maps.Map) => {
    const googleMaps = getGoogleMaps();
    if (!googleMaps) return null;
    
    const marker = new googleMaps.Marker({
      position,
      map,
      title,
      icon: markerIcon
    });
    
    marker.addListener('mouseover', () => {
      marker.setIcon(hoverIcon);
      marker.setAnimation(googleMaps.Animation.BOUNCE);
    });
    
    marker.addListener('mouseout', () => {
      marker.setIcon(markerIcon);
      marker.setAnimation(null);
    });
    
    return marker;
  };

  let mapInitializationAttempts = 0;
  
  const initializeMap = async () => {
    try {
      const mapElement = document.getElementById(mapElementId);
      if (!mapElement) return;
      
      await loadGoogleMaps({
        apiKey: googleMapsApiKey,
        libraries: "places",
        version: "weekly"
      });
      
      const googleMaps = getGoogleMaps();
      if (!googleMaps) return;
      
      const mapOptions = {
        center: mapCenter.value,
        zoom: DEFAULT_ZOOM_NO_SELECTION, // Start zoomed out
        disableDefaultUI: true,
        zoomControl: true,
        gestureHandling: 'cooperative', // Best for mobile to prevent scroll trapping
        mapTypeId: "roadmap",
        styles: [
          { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }
        ]
      };
      
      mapInstance.value = new googleMaps.Map(mapElement, mapOptions);
      
      // Don't create marker initially - wait for user to select location
      // Marker will be created when user clicks on map or uses "Get My Location"
      
      mapInstance.value.addListener('click', (event: google.maps.MapMouseEvent) => {
        if (event.latLng) {
          const lat = event.latLng.lat();
          const lng = event.latLng.lng();
          setCoordinates(lat, lng);
        }
      });
      
    } catch {
      if (mapInitializationAttempts < 3) {
        const backoffDelay = 2000 * Math.pow(2, mapInitializationAttempts);
        mapInitializationAttempts++;
        setTimeout(initializeMap, backoffDelay);
      }
    }
  };

  // Helper to create draggable marker
  const createDraggableMarker = (position: Coordinates) => {
    if (mapMarker.value) return; // Already exists
    
    mapMarker.value = createMarkerWithHover(
      position,
      'Selected Location',
      mapInstance.value
    );
    
    if (mapMarker.value) {
      mapMarker.value.setDraggable(true);
      mapMarker.value.addListener('dragend', (event: google.maps.MapMouseEvent) => {
        if (event.latLng) {
          const lat = event.latLng.lat();
          const lng = event.latLng.lng();
          setCoordinates(lat, lng);
        }
      });
    }
  };

  let mapUpdateDebounce: ReturnType<typeof setTimeout> | null = null;
  const debouncedUpdateMap = () => {
    if (!mapInstance.value) return;
    if (mapUpdateDebounce) clearTimeout(mapUpdateDebounce);
    
    mapUpdateDebounce = setTimeout(() => {
      if (!latitude.value || !longitude.value) return;
      
      const position = {
        lat: parseFloat(latitude.value),
        lng: parseFloat(longitude.value)
      };
      mapInstance.value.setCenter(position);
      if (mapMarker.value) {
        mapMarker.value.setPosition(position);
      }
    }, 16);
  };

  // Fetch approximate location from IP geolocation API
  const getApproximateLocationFromIP = async (): Promise<Coordinates | null> => {
    try {
      // Using ipapi.co (free tier, HTTPS, allowed by CSP)
      const response = await fetch('https://ipapi.co/json/');
      if (!response.ok) return null;
      
      const data = await response.json();
      if (data.latitude && data.longitude) {
        return { lat: data.latitude, lng: data.longitude };
      }
      return null;
    } catch {
      // If API fails, return null to use default
      return null;
    }
  };

  const getCurrentLocation = async (silent = false) => {
    gettingLocation.value = true;

    if (!navigator.geolocation) {
      if (!silent) showError("Geolocation is not supported by your browser.");
      // Fallback: try IP geolocation, then default
      await setApproximateLocationMarker(silent);
      gettingLocation.value = false;
      return;
    }

    const geoOptions = {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0
    };

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        setCoordinates(lat, lng);
        gettingLocation.value = false;
      },
      async (_err) => {
        if (!silent) showError("Unable to get precise location. Using approximate location.");
        // Fallback: try IP geolocation, then default
        await setApproximateLocationMarker(silent);
        gettingLocation.value = false;
      },
      geoOptions
    );
  };

  // Helper to set marker at approximate location from IP or default
  const setApproximateLocationMarker = async (silent = false) => {
    if (!mapInstance.value) return;
    
    // Try to get approximate location from IP
    const approximatePos = await getApproximateLocationFromIP();
    const position = approximatePos || DEFAULT_MAP_CENTER;
    
    // Create marker if it doesn't exist
    if (!mapMarker.value) {
      createDraggableMarker(position);
    }
    
    // Update marker position
    if (mapMarker.value) {
      mapMarker.value.setPosition(position);
    }
    
    // Center map on position
    mapInstance.value.setCenter(position);
    
    // Use different zoom levels based on whether we got IP location
    if (approximatePos) {
      mapInstance.value.setZoom(12); // Closer zoom for IP-based location
      if (!silent) {
        // Show info that this is approximate location
        addToast("Showing approximate location based on your network. Please adjust the marker to the exact location.", "info", 6000, "Approximate Location");
      }
    } else {
      mapInstance.value.setZoom(10); // Wider zoom for default location
    }
    
    // Mark as having a selected location so user can see they need to adjust
    latitude.value = position.lat.toFixed(6);
    longitude.value = position.lng.toFixed(6);
    hasSelectedLocation.value = true;
  };

  // Watch for external coordinate changes
  watch([latitude, longitude], () => {
    // This watcher handles manual input changes
    const latIdx = parseFloat(latitude.value);
    const lngIdx = parseFloat(longitude.value);
    if (!isNaN(latIdx) && !isNaN(lngIdx)) {
      if (Math.abs(latIdx - mapCenter.value.lat) > 0.0001 || 
          Math.abs(lngIdx - mapCenter.value.lng) > 0.0001) {
             mapCenter.value = { lat: latIdx, lng: lngIdx };
             debouncedUpdateMap();
      }
    }
  });

  // Cleanup function to be called in onUnmounted
  const cleanup = () => {
    // Clear debounce timer
    if (mapUpdateDebounce) {
      clearTimeout(mapUpdateDebounce);
      mapUpdateDebounce = null;
    }
    
    // Clean up marker
    if (mapMarker.value) {
      mapMarker.value.setMap(null);
      mapMarker.value = null;
    }
    
    // Clear map instance
    mapInstance.value = null;
    
    // Reset state
    hasSelectedLocation.value = false;
    latitude.value = "";
    longitude.value = "";
  };

  return {
    latitude,
    longitude,
    mapCenter,
    gettingLocation,
    hasSelectedLocation,
    mapInstance,
    initializeMap,
    getCurrentLocation,
    cleanup
  };
}
