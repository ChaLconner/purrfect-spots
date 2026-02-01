/**
 * Application Constants
 * 
 * Centralized configuration values used across the frontend.
 * Avoids hardcoded values scattered throughout components.
 */

// ========== Map Constants ==========
export const DEFAULT_COORDINATES = {
  CHIANG_MAI: { lat: 18.7883, lng: 98.9853 },
  BANGKOK: { lat: 13.7563, lng: 100.5018 },
  PHUKET: { lat: 7.8804, lng: 98.3923 },
};

export const FALLBACK_LOCATION = DEFAULT_COORDINATES.BANGKOK;

export const MAP_CONFIG = {
  DEFAULT_ZOOM: 13,
  MIN_ZOOM: 3,
  MAX_ZOOM: 20,
  MARKER_ANIMATION_DELAY_MS: 50,
  MIN_ZOOM_FOR_VIEWPORT_FETCH: 10,
  MAX_MARKERS_PER_VIEWPORT: 100,
  VIEWPORT_FETCH_DEBOUNCE_MS: 300, // Reduced from 500ms to 300ms for better responsiveness
  FIT_BOUNDS_PADDING: 50,
} as const;

// ========== Image Constants ==========
export const IMAGE_CONFIG = {
  MAX_FILE_SIZE_MB: 10,
  MAX_FILE_SIZE_BYTES: 10 * 1024 * 1024,
  ALLOWED_TYPES: ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.webp', '.gif'],
  MAX_DIMENSION: 1920,
  COMPRESSION_QUALITY: 0.85,
  PLACEHOLDER_URL: 'https://placehold.co/400x400?text=No+Image',
} as const;

// ========== Pagination Constants ==========
export const PAGINATION_CONFIG = {
  DEFAULT_PAGE_SIZE: 20,
  GALLERY_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  LOAD_MORE_THRESHOLD_PX: 200,
} as const;

// ========== Gallery Constants ==========
export const GALLERY_CONFIG = {
  IMAGES_PER_PAGE: 20,
  LAZY_LOAD_ROOT_MARGIN: '100px',
  LOAD_MORE_ROOT_MARGIN: '200px',
  LAZY_LOAD_THRESHOLD: 0.1,
  LOAD_MORE_DELAY_MS: 300,
  MAX_LOADED_IMAGES_CACHE: 200, // Max images to keep in memory cache
  LAZY_LOAD_DEBOUNCE_MS: 100, // Debounce delay for lazy loading setup
} as const;

// ========== Animation Constants ==========
export const ANIMATION_CONFIG = {
  TRANSITION_FAST_MS: 150,
  TRANSITION_NORMAL_MS: 300,
  TRANSITION_SLOW_MS: 500,
  DEBOUNCE_DELAY_MS: 300,
  TOAST_DURATION_MS: 5000,
  LOADING_DELAY_MS: 200,
} as const;

// ========== API Constants ==========
export const API_CONFIG = {
  TIMEOUT_MS: 30000,
  MAX_RETRIES: 3,
  RETRY_BASE_DELAY_MS: 1000,
  RETRY_MAX_DELAY_MS: 10000,
} as const;

// ========== Auth Constants ==========
export const AUTH_CONFIG = {
  TOKEN_STORAGE_KEY: 'auth_token',
  USER_STORAGE_KEY: 'user_data',
  LEGACY_TOKEN_KEY: 'access_token',
  LEGACY_USER_KEY: 'user',
  SESSION_CHECK_INTERVAL_MS: 5 * 60 * 1000, // 5 minutes
} as const;

// ========== Form Validation Constants ==========
export const VALIDATION_CONFIG = {
  MIN_PASSWORD_LENGTH: 8,
  MAX_PASSWORD_LENGTH: 128,
  MAX_NAME_LENGTH: 100,
  MAX_LOCATION_NAME_LENGTH: 200,
  MAX_DESCRIPTION_LENGTH: 1000,
  MAX_TAGS: 20,
  MAX_TAG_LENGTH: 50,
} as const;

// ========== Cat Detection Constants ==========
export const CAT_DETECTION_CONFIG = {
  HIGH_CONFIDENCE_THRESHOLD: 75,
  LOW_CONFIDENCE_THRESHOLD: 50,
  MIN_ACCEPTABLE_CONFIDENCE: 25,
} as const;

// ========== Feature Flags ==========
export const FEATURE_FLAGS = {
  ENABLE_OAUTH_LOGIN: true,
  ENABLE_PASSWORD_RESET: true,
  ENABLE_PROFILE_PICTURES: true,
  ENABLE_TAGS: true,
  ENABLE_SEARCH: true,
} as const;

// ========== External URLs ==========
export const EXTERNAL_URLS = {
  GOOGLE_MAPS_DIRECTIONS: 'https://www.google.com/maps/dir/?api=1',
  DEFAULT_AVATAR: '/default-avatar.svg',
  CAT_MARKER_ICON: '/location_10753796.png',
} as const;
