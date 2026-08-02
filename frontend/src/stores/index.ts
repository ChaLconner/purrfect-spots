/**
 * Pinia Store Configuration
 *
 * Central export for all Pinia stores.
 * Import stores from this file for clean imports.
 */
import { createPinia } from 'pinia';

// Create Pinia instance
export const pinia = createPinia();

// Export all stores
export { useCatsStore } from './catsStore';
export { useToastStore } from './toastStore';

// Export types
export type { CatLocation } from './catsStore';
