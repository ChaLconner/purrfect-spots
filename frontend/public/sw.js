/**
 * Service Worker for Purrfect Spots
 * 
 * Features:
 * - Cache static assets (CSS, JS, images)
 * - Cache API responses for offline support
 * - Network-first strategy for API calls
 * - Cache-first strategy for static assets
 */

const CACHE_NAME = 'purrfect-spots-v1';
const STATIC_CACHE_NAME = 'purrfect-spots-static-v1';
const API_CACHE_NAME = 'purrfect-spots-api-v1';

// Cache URLs
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/cat-icon.png',
  '/cat-illustration.png',
  '/default-avatar.svg',
  '/location_10753796.png',
];

// API endpoints to cache
const API_ENDPOINTS = [
  '/api/v1/gallery',
  '/api/v1/gallery/locations',
  '/api/v1/gallery/popular-tags',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log(`[SW] Installing service worker for scope: ${self.registration.scope}`);
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets...');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  
  // Force the waiting service worker to become the active service worker
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log(`[SW] Activating service worker for scope: ${self.registration.scope}`);
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== STATIC_CACHE_NAME && 
              cacheName !== API_CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
          return null;
        })
      );
    })
  );
  
  // Take control of all pages immediately
  self.clients.claim();
});

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static assets with cache-first strategy
  if (STATIC_ASSETS.some(asset => url.pathname === asset || url.pathname.endsWith(asset))) {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Handle image requests with cache-first strategy
  if (request.destination === 'image') {
    event.respondWith(handleImageRequest(request));
    return;
  }

  // Default: network-first with cache fallback
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache successful responses
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // If network fails, try cache
        return caches.match(request);
      })
  );
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  // Check if this is a gallery endpoint that should be cached
  const isGalleryEndpoint = API_ENDPOINTS.some(endpoint => 
    url.pathname.startsWith(endpoint)
  );

  if (!isGalleryEndpoint) {
    // For non-cacheable API endpoints, use network-only
    return fetch(request);
  }

  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse && networkResponse.status === 200) {
      // Cache successful API responses for 1 minute
      const responseClone = networkResponse.clone();
      const cache = await caches.open(API_CACHE_NAME);
      await cache.put(request, responseClone);
      console.log('[SW] Cached API response:', url.pathname);
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache for:', url.pathname);
    
    // If network fails, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Returning cached API response:', url.pathname);
      return cachedResponse;
    }
    
    // If no cache, return error
    throw error;
  }
}

// Handle static assets with cache-first strategy
async function handleStaticRequest(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    console.log('[SW] Returning cached static asset:', request.url);
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      await cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] Failed to fetch static asset:', request.url, error);
    throw error;
  }
}

// Handle image requests with cache-first strategy
async function handleImageRequest(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    console.log('[SW] Returning cached image:', request.url);
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] Failed to fetch image:', request.url, error);
    throw error;
  }
}

// Handle messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => caches.delete(cacheName))
      );
    }).then(() => {
      event.ports[0].postMessage({ success: true });
    });
  }
});
