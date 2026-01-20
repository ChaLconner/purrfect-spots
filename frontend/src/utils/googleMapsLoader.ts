// Google Maps API Loader - Centralized loader to prevent multiple script loads
/* eslint-disable @typescript-eslint/no-explicit-any */
import { isDev } from './env';

interface GoogleMapsLoaderOptions {
  apiKey: string;
  libraries?: string;
  version?: string;
  callback?: string;
}

// Global state to track loading status
let isLoading = false;
let isLoaded = false;
let loadPromise: Promise<void> | null = null;
let pendingCallbacks: Array<() => void> = [];

/**
 * Load Google Maps API script only once
 * @param options Configuration options for loading Google Maps
 * @returns Promise that resolves when Google Maps API is loaded
 */
export const loadGoogleMaps = async (options: GoogleMapsLoaderOptions): Promise<void> => {
  // If already loaded, resolve immediately
  if (isLoaded && window.google && window.google.maps) {
    return Promise.resolve();
  }

  // If currently loading, add to pending callbacks and return existing promise
  if (isLoading && loadPromise) {
    return loadPromise;
  }

  // Start loading process
  isLoading = true;

  // Create a unique callback name to avoid conflicts
  const callbackName = `initMap_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  
  // Create a script element manually to load the Google Maps API
  const script = document.createElement('script');
  script.async = true;
  script.defer = true;
  script.src = `https://maps.googleapis.com/maps/api/js?key=${options.apiKey}&v=${options.version || 'weekly'}&libraries=${options.libraries || 'places'}&callback=${callbackName}`;
  
  // Create the load promise
  loadPromise = new Promise<void>((resolve, reject) => {
    // Set up the callback function
    (window as any)[callbackName] = () => {
      clearTimeout(timeoutId);
      isLoaded = true;
      isLoading = false;
      
      // Clean up the callback function
      delete (window as any)[callbackName];
      
      // Execute all pending callbacks
      pendingCallbacks.forEach(callback => callback());
      pendingCallbacks = [];
      
      resolve();
    };
    
    script.onerror = (error) => {
      if (isDev()) {
        console.error('❌ Failed to load Google Maps API:', error);
      }
      isLoading = false;
      
      // Clean up the callback function on error
      delete (window as any)[callbackName];
      
      // Reject all pending promises
      pendingCallbacks = []; // Clear pending callbacks on error
      
      // More specific error message
      reject(new Error(`Failed to load Google Maps API. Please check your API key: ${options.apiKey ? 'Key is set' : 'Key is missing'}`));
    };
    
    // Add timeout handling
    const timeoutId = setTimeout(() => {
      if (!isLoaded) {
        if (isDev()) {
          console.error('❌ Google Maps API loading timed out');
        }
        isLoading = false;
        
        // Clean up
        delete (window as any)[callbackName];
        document.head.removeChild(script);
        
        pendingCallbacks = [];
        reject(new Error('Google Maps API loading timed out. Please check your internet connection and API key.'));
      }
    }, 15000); // 15 second timeout
    
    // Add the script to the document
    document.head.appendChild(script);
  });

  return loadPromise;
};

/**
 * Check if Google Maps API is loaded
 * @returns Boolean indicating if Google Maps API is available
 */
export const isGoogleMapsLoaded = (): boolean => {
  return isLoaded && !!(window.google?.maps);
};

/**
 * Get the Google Maps object
 * @returns The global Google Maps object or null if not loaded
 */
export const getGoogleMaps = () => {
  return window.google?.maps || null;
};

/**
 * Add a callback to be executed when Google Maps is loaded
 * @param callback Function to execute when Google Maps is loaded
 */
export const onGoogleMapsLoaded = (callback: () => void): void => {
  if (isGoogleMapsLoaded()) {
    // If already loaded, execute immediately
    callback();
  } else {
    // Otherwise, add to pending callbacks
    pendingCallbacks.push(callback);
  }
};

// Note: The Window interface with google property is defined in frontend/src/types/global.d.ts