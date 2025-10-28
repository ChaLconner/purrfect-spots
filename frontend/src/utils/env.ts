/**
 * Utility functions for environment variables
 */

/**
 * Check if the application is running in development mode
 * @returns true if in development mode, false otherwise
 */
export const isDev = (): boolean => {
  return (import.meta as any).env?.DEV === true || (import.meta as any).env?.MODE === 'development';
};

/**
 * Check if the application is running in production mode
 * @returns true if in production mode, false otherwise
 */
export const isProd = (): boolean => {
  return (import.meta as any).env?.PROD === true || (import.meta as any).env?.MODE === 'production';
};

/**
 * Get an environment variable with type assertion
 * @param key - The environment variable key
 * @param defaultValue - Default value if the environment variable is not defined
 * @returns The environment variable value or the default value
 */
export const getEnvVar = (key: string, defaultValue: string = ''): string => {
  return (import.meta as any).env?.[key] || defaultValue;
};