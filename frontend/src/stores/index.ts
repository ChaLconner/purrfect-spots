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
export { useAdminStore } from './adminStore';
export { useAuthStore } from './authStore';
export { useCatsStore, extractTags, getCleanDescription, hasTag } from './catsStore';
export { useNotificationStore } from './notificationStore';
export { useSubscriptionStore } from './subscriptionStore';
export { useToastStore, toastState, addToast, removeToast, showError, showSuccess } from './toastStore';

// Export types
export type { CatLocation, PaginationMeta, TagInfo } from './catsStore';
