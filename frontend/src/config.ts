/**
 * Application-wide configuration.
 * Centralizes environment variables and constants.
 */

export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  },
  app: {
    name: 'Purrfect Spots',
    currency: 'THB', // Default currency
  },
};
