/**
 * Image utilities for optimization and CDN handling
 */

import { isProd, getEnvVar } from './env';

// Image optimization settings
export interface ImageOptimizationOptions {
  maxWidth?: number;
  maxHeight?: number;
  quality?: number; // 0-100
  format?: 'jpeg' | 'png' | 'webp';
  enableProgressive?: boolean;
}

// Default optimization settings
const DEFAULT_OPTIONS: ImageOptimizationOptions = {
  maxWidth: 1920,
  maxHeight: 1080,
  quality: 85,
  format: 'jpeg',
  enableProgressive: true,
};

// CDN configuration
export interface CDNConfig {
  enabled: boolean;
  baseUrl?: string;
  defaultParams?: Record<string, string>;
}

// Default CDN configuration
const DEFAULT_CDN_CONFIG: CDNConfig = {
  enabled: isProd(), // Enable CDN in production
  baseUrl: getEnvVar('VITE_CDN_BASE_URL') || '',
  defaultParams: {
    auto: 'format,compress',
    q: '85', // quality
  },
};

/**
 * Check if CDN is available and configured
 */
export const isCDNAvailable = (): boolean => {
  return DEFAULT_CDN_CONFIG.enabled && !!DEFAULT_CDN_CONFIG.baseUrl;
};

/**
 * Get CDN URL for an image
 */
export const getCDNUrl = (imageUrl: string, options?: ImageOptimizationOptions): string => {
  if (!isCDNAvailable()) {
    return imageUrl;
  }

  const { baseUrl, defaultParams } = DEFAULT_CDN_CONFIG;
  const url = new URL(imageUrl, baseUrl);
  
  // Add default parameters
  if (defaultParams) {
    Object.entries(defaultParams).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }
  
  // Add custom parameters based on options
  if (options) {
    if (options.maxWidth) url.searchParams.set('w', options.maxWidth.toString());
    if (options.maxHeight) url.searchParams.set('h', options.maxHeight.toString());
    if (options.quality) url.searchParams.set('q', options.quality.toString());
    if (options.format) url.searchParams.set('f', options.format);
  }
  
  return url.toString();
};

/**
 * Optimize an image file before upload
 */
export const optimizeImage = async (
  file: File,
  options: ImageOptimizationOptions = {}
): Promise<File> => {
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options };
  
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      // Calculate new dimensions
      let { width, height } = img;
      const { maxWidth, maxHeight } = mergedOptions;
      
      if (maxWidth && width > maxWidth) {
        height = (height * maxWidth) / width;
        width = maxWidth;
      }
      
      if (maxHeight && height > maxHeight) {
        width = (width * maxHeight) / height;
        height = maxHeight;
      }
      
      // Set canvas dimensions
      canvas.width = width;
      canvas.height = height;
      
      // Draw and compress image
      ctx?.drawImage(img, 0, 0, width, height);
      
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Failed to optimize image'));
            return;
          }
          
          // Create new file with optimized data
          const optimizedFile = new File([blob], file.name, {
            type: `image/${mergedOptions.format}`,
            lastModified: Date.now(),
          });
          
          resolve(optimizedFile);
        },
        `image/${mergedOptions.format}`,
        mergedOptions.quality! / 100
      );
    };
    
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = URL.createObjectURL(file);
  });
};

/**
 * Generate responsive image sources for different screen sizes
 */
export const generateResponsiveSources = (
  imageUrl: string,
  baseOptions: ImageOptimizationOptions = {}
): Array<{ srcSet: string; media?: string; type?: string }> => {
  const sources = [];
  
  // Generate sources for different widths
  const widths = [320, 640, 768, 1024, 1280, 1536];
  
  for (const width of widths) {
    const options = { ...baseOptions, maxWidth: width };
    const src = isCDNAvailable() 
      ? getCDNUrl(imageUrl, options)
      : imageUrl;
    
    sources.push({
      srcSet: `${src} ${width}w`,
    });
  }
  
  return sources;
};

/**
 * Create a responsive image element with proper srcset and sizes
 */
export const createResponsiveImage = (
  container: HTMLElement,
  imageUrl: string,
  alt: string,
  options: ImageOptimizationOptions = {},
  sizes: string = '100vw'
): HTMLImageElement => {
  const img = document.createElement('img');
  img.alt = alt;
  
  // Generate responsive sources
  const sources = generateResponsiveSources(imageUrl, options);
  
  // Create srcset string
  const srcset = sources.map(source => source.srcSet).join(', ');
  img.srcset = srcset;
  img.sizes = sizes;
  
  // Set fallback src
  img.src = isCDNAvailable() 
    ? getCDNUrl(imageUrl, options)
    : imageUrl;
  
  // Add loading optimization
  img.loading = 'lazy';
  img.decoding = 'async';
  
  // Append to container
  container.appendChild(img);
  
  return img;
};

/**
 * Preload critical images
 */
export const preloadImage = (url: string, options?: ImageOptimizationOptions): Promise<void> => {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = isCDNAvailable() 
      ? getCDNUrl(url, options)
      : url;
    
    link.onload = () => resolve();
    link.onerror = () => reject(new Error(`Failed to preload image: ${url}`));
    
    document.head.appendChild(link);
  });
};

/**
 * Get image dimensions without loading the full image
 */
export const getImageDimensions = (file: File): Promise<{ width: number; height: number }> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    
    img.onload = () => {
      resolve({ width: img.width, height: img.height });
      URL.revokeObjectURL(img.src);
    };
    
    img.onerror = () => {
      reject(new Error('Failed to load image'));
      URL.revokeObjectURL(img.src);
    };
    
    img.src = URL.createObjectURL(file);
  });
};

/**
 * Validate image file
 */
export const validateImageFile = (
  file: File,
  maxSizeMB: number = 10,
  allowedTypes: string[] = ['image/jpeg', 'image/png', 'image/webp']
): { valid: boolean; error?: string } => {
  // Check file type
  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: `Invalid file type. Allowed types: ${allowedTypes.join(', ')}`,
    };
  }
  
  // Check file size
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  if (file.size > maxSizeBytes) {
    return {
      valid: false,
      error: `File too large. Maximum size: ${maxSizeMB}MB`,
    };
  }
  
  return { valid: true };
};

/**
 * Generate a thumbnail for an image
 */
export const generateThumbnail = async (
  file: File,
  maxSize: number = 200,
  quality: number = 80
): Promise<File> => {
  return optimizeImage(file, {
    maxWidth: maxSize,
    maxHeight: maxSize,
    quality,
    format: 'jpeg',
  });
};

/**
 * Convert image to base64
 */
export const imageToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result);
      } else {
        reject(new Error('Failed to convert image to base64'));
      }
    };
    
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsDataURL(file);
  });
};