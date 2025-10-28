/**
 * API Configuration
 */

import { isDev, getEnvVar } from '../utils/env';

// Helper function to get API base URL
export function getApiBaseUrl(): string {
  // Get from environment variable
  const envUrl = getEnvVar('VITE_API_BASE_URL');
  
  if (envUrl) {
    return envUrl;
  }
  
  // Auto-detect environment
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const isVercel = window.location.hostname.includes('vercel.app');
  
  if (isLocalhost) {
    // Local development - use localhost backend
    return 'http://localhost:8000';
  } else if (isVercel) {
    // Vercel deployment - use relative path for same-origin requests
    // This will automatically route to the backend through vercel.json routes
    return '/api';
  } else {
    // Fallback for other environments
    return 'https://purrfect-spots-backend.vercel.app';
  }
}

// Create full API URL
export function createApiUrl(endpoint: string): string {
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  const fullUrl = `${baseUrl}/${cleanEndpoint}`;
  
  return fullUrl;
}

// Default headers for API requests
export function getDefaultHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}

// Headers with authentication
export function getAuthHeaders(): Record<string, string> {
  // Try both token keys for compatibility
  const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');
  const headers = getDefaultHeaders();
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
}

// Centralized API request function
export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = createApiUrl(endpoint);
  const headers = {
    ...getDefaultHeaders(),
    ...options.headers,
  };

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    
    return response;
  } catch (error) {
    if (isDev()) {
      console.error('API request failed:', error);
    }
    throw error;
  }
}

// Authenticated API request
export async function authenticatedApiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  };

  return apiRequest(endpoint, {
    ...options,
    headers,
  });
}
