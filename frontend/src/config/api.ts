/**
 * API Configuration
 */

// Helper function to get API base URL
export function getApiBaseUrl(): string {
  // ดึงจาก environment variable
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  
  // Production fallback - your actual Vercel backend deployment URL
  const fallbackUrl = 'https://purrfect-spots-backend.vercel.app';
  
  const apiUrl = envUrl || fallbackUrl;
  
  return apiUrl;
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
  const token = localStorage.getItem('access_token');
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
    console.error('API request failed:', error);
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
