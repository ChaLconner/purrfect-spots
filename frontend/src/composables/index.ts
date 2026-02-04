/**
 * Composables Index
 *
 * Central export for all composables.
 * Import from '@/composables' for cleaner imports.
 *
 * @module Composables
 */

// Accessibility utilities
export {
  announce,
  useFocusTrap,
  useModalFocus,
  useArrowKeyNavigation,
  useSkipLink,
} from './useAccessibility';

// Performance monitoring
export {
  logMetric,
  measureAsync,
  measureSync,
  useWebVitals,
  useRenderTime,
  useApiTiming,
  getMetrics,
  clearMetrics,
  getPerformanceSummary,
} from './usePerformance';

// Geolocation
export { useGeolocation } from './useGeolocation';

// Map utilities
export { useMapMarkers } from './useMapMarkers';
export { useLocationPicker } from './useLocationPicker';

// SEO
export { useSeo } from './useSeo';

// Upload
export { useUploadCat } from './useUploadCat';
