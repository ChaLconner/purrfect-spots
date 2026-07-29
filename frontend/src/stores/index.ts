/**
 * Pinia Store Configuration
 *
 * Central export for all Pinia stores.
 * Import stores from this file for clean imports.
 */
import { createPinia } from 'pinia';

// Create Pinia instance
export const pinia = createPinia();

// Export public stores that are safe on the unauthenticated critical path.
export { useCatsStore, extractTags, getCleanDescription, hasTag } from './catsStore';
export { useToastStore } from './toastStore';

// Export types
export type { CatLocation, PaginationMeta, TagInfo } from './catsStore';
