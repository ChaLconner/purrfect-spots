/**
 * Browser Extension Error Handler
 * 
 * This utility provides centralized handling for browser extension conflicts
 * that cause "message channel closed" errors and similar issues.
 */
/* eslint-disable @typescript-eslint/no-explicit-any */

import { isDev } from './env';

// Error patterns to identify browser extension conflicts
const BROWSER_EXTENSION_ERROR_PATTERNS = [
  'message channel closed',
  'asynchronous response by returning true, but the message channel closed',
  'A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received',
  'listener indicated an asynchronous response',
  'Non-Error promise rejection captured',
  'ChunkLoadError'
];

// Error names that indicate browser extension conflicts
const BROWSER_EXTENSION_ERROR_NAMES = [
  'ChunkLoadError',
  'TypeError'
];

// Error codes that indicate browser extension conflicts
const BROWSER_EXTENSION_ERROR_CODES = [
  'NETWORK_ERROR',
  'ERR_NETWORK'
];

/**
 * Check if an error is related to browser extension conflicts
 * @param error The error to check
 * @returns True if the error is related to browser extension conflicts
 */
export const isBrowserExtensionError = (error: any): boolean => {
  if (!error) return false;
  
  // Check error message
  if (error.message && typeof error.message === 'string') {
    for (const pattern of BROWSER_EXTENSION_ERROR_PATTERNS) {
      if (error.message.includes(pattern)) {
        return true;
      }
    }
  }
  
  // Check error name
  if (error.name && BROWSER_EXTENSION_ERROR_NAMES.includes(error.name)) {
    return true;
  }
  
  // Check error code
  if (error.code && BROWSER_EXTENSION_ERROR_CODES.includes(error.code)) {
    return true;
  }
  
  // Check error toString() method
  if (error.toString && typeof error.toString === 'function') {
    const errorString = error.toString();
    for (const pattern of BROWSER_EXTENSION_ERROR_PATTERNS) {
      if (errorString.includes(pattern)) {
        return true;
      }
    }
  }
  
  return false;
};

/**
 * Log a browser extension error (only in development)
 * @param error The error to log
 * @param context Additional context about where the error occurred
 */
export const logBrowserExtensionError = (error: any, context: string = ''): void => {
  if (isDev()) {
    const message = error?.message || error || 'Unknown browser extension error';
    console.warn('⚠️ Browser extension error', context ? `(${context})` : '', ':', message);
  }
};

/**
 * Handle browser extension errors with retry logic
 * @param error The error that occurred
 * @param retryCallback Function to call for retry
 * @param maxRetries Maximum number of retry attempts (default: 1)
 * @param retryDelay Delay between retries in milliseconds (default: 100)
 * @returns Promise that resolves with the retry result or rejects with the original error
 */
export const handleBrowserExtensionError = async <T>(
  error: any,
  retryCallback: () => Promise<T>,
  maxRetries: number = 1,
  retryDelay: number = 100
): Promise<T> => {
  if (!isBrowserExtensionError(error)) {
    throw error;
  }
  
  logBrowserExtensionError(error, 'retry handler');
  
  let lastError: any = error;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // Add delay before retry
      if (retryDelay > 0) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
      
      return await retryCallback();
    } catch (retryError: any) {
      lastError = retryError;
      
      // If it's not a browser extension error, don't retry further
      if (!isBrowserExtensionError(retryError)) {
        throw retryError;
      }
      
      logBrowserExtensionError(retryError, `retry attempt ${attempt}`);
    }
  }
  
  // All retries failed, throw the last error
  throw lastError;
};

/**
 * Create a wrapped version of an async function that handles browser extension errors
 * @param fn The async function to wrap
 * @param options Options for error handling
 * @returns A wrapped function that handles browser extension errors
 */
export const withBrowserExtensionHandling = <T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  options: {
    maxRetries?: number;
    retryDelay?: number;
    context?: string;
  } = {}
) => {
  return async (...args: T): Promise<R> => {
    try {
      return await fn(...args);
    } catch (error: any) {
      if (isBrowserExtensionError(error)) {
        return handleBrowserExtensionError(
          error,
          () => fn(...args),
          options.maxRetries,
          options.retryDelay
        );
      }
      throw error;
    }
  };
};

/**
 * Global error handler for unhandled promise rejections
 * @param event The unhandledrejection event
 */
export const handleUnhandledRejection = (event: PromiseRejectionEvent): boolean => {
  if (isBrowserExtensionError(event.reason)) {
    logBrowserExtensionError(event.reason, 'unhandled rejection');
    event.preventDefault();
    return false;
  }
  return true;
};

/**
 * Global error handler for window errors
 * @param event The error event
 */
export const handleError = (event: ErrorEvent): boolean => {
  if (isBrowserExtensionError(event.error || event.message)) {
    logBrowserExtensionError(event.error || event.message, 'window error');
    event.preventDefault();
    return false;
  }
  return true;
};

/**
 * Vue error handler for browser extension errors
 * @param err The error that occurred
 * @param info Vue-specific error information
 */
export const handleVueError = (err: any, info: string): boolean | undefined => {
  if (isBrowserExtensionError(err)) {
    logBrowserExtensionError(err, `Vue error in ${info}`);
    return false;
  }
  // Return undefined to let other errors be handled normally
  return undefined;
};