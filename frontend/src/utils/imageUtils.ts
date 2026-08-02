/**
 * Image utilities for optimization and CDN handling
 */

import { getEnvVar } from './env';
import { calculateScaledDimensions } from './imageDimensions';

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
  format: 'webp',
  enableProgressive: true,
};

let imageWorker: Worker | null = null;
let msgId = 0;
const WORKER_TIMEOUT_MS = 15_000;

function getWorker(): Worker | null {
  if (typeof window !== 'undefined' && window.Worker) {
    if (!imageWorker) {
      imageWorker = new Worker(new URL('../workers/image-worker.ts', import.meta.url), {
        type: 'module',
      });
    }
    return imageWorker;
  }
  return null;
}

// CDN configuration
interface CDNConfig {
  enabled: boolean;
  baseUrl?: string;
  defaultParams?: Record<string, string>;
}

// Default CDN configuration
const envCdnUrl = getEnvVar('VITE_CDN_BASE_URL');
const DEFAULT_CDN_CONFIG: CDNConfig = {
  enabled: !!envCdnUrl, // Enable if URL is set (allows dev/testing via .env)
  baseUrl: envCdnUrl || '',
  defaultParams: {
    auto: 'format,compress',
    q: '85', // quality
  },
};

// Debug log in dev

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
  // 1. Supabase Storage (already optimized)
  if (imageUrl.includes('supabase.co')) {
    // Supabase handles params natively via query string
    const url = new URL(imageUrl);
    if (options?.maxWidth) url.searchParams.set('width', options.maxWidth.toString());
    if (options?.maxHeight) url.searchParams.set('height', options.maxHeight.toString());
    if (options?.quality) url.searchParams.set('quality', options.quality.toString());
    if (options?.format) url.searchParams.set('format', options.format);
    else url.searchParams.set('format', 'webp'); // Default to webp
    url.searchParams.set('resize', 'cover');
    return url.toString();
  }

  // 2. External / S3 (Use Proxy)
  if (options && (options.maxWidth || options.maxHeight)) {
    // If we need resizing on S3, use wsrv.nl proxy
    // This provides FREE, FAST, GLOBAL resizing for S3 buckets
    const params = new URLSearchParams();
    params.set('url', imageUrl);
    if (options.maxWidth) params.set('w', options.maxWidth.toString());
    if (options.maxHeight) params.set('h', options.maxHeight.toString());
    params.set('q', (options.quality || 80).toString());
    params.set('output', options.format || 'webp');

    return `https://wsrv.nl/?${params.toString()}`;
  }

  // 3. Fallback to simple CDN rewrite (if configured in env)
  if (!isCDNAvailable()) {
    return imageUrl;
  }

  const { baseUrl } = DEFAULT_CDN_CONFIG;
  const url = new URL(imageUrl, baseUrl);
  // ... rest of traditional CDN logic ...
  return url.toString();
};

/**
 * Optimize an image file before upload
 * Uses a Web Worker if available to prevent UI freezing on large files.
 */
export const optimizeImage = async (
  file: File,
  options: ImageOptimizationOptions = {}
): Promise<File> => {
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options };

  return new Promise((resolve, reject) => {
    const worker = getWorker();

    // Check if OffscreenCanvas is supported and we have a worker instance
    if (worker && typeof OffscreenCanvas !== 'undefined') {
      const currentId = msgId++;
      let settled = false;

      const cleanup = (): void => {
        worker.removeEventListener('message', onMessage);
        worker.removeEventListener('error', onError);
        clearTimeout(timeoutId);
      };

      const fallback = (): void => {
        if (settled) return;
        settled = true;
        cleanup();
        optimizeImageMainThread(file, mergedOptions).then(resolve).catch(reject);
      };

      const onMessage = (e: MessageEvent): void => {
        if (e.data.id === currentId) {
          if (settled) return;
          settled = true;
          cleanup();

          if (e.data.success) {
            const optimizedFile = new File(
              [e.data.blob],
              file.name.replace(/\.[^/.]+$/, '') + `.${mergedOptions.format}`,
              {
                type: `image/${mergedOptions.format}`,
                lastModified: Date.now(),
              }
            );
            resolve(optimizedFile);
          } else {
            optimizeImageMainThread(file, mergedOptions).then(resolve).catch(reject);
          }
        }
      };

      const onError = (): void => fallback();
      const timeoutId = window.setTimeout(fallback, WORKER_TIMEOUT_MS);
      worker.addEventListener('message', onMessage);
      worker.addEventListener('error', onError);
      worker.postMessage({ file, options: mergedOptions, id: currentId });
    } else {
      // Fallback for browsers that don't support workers or OffscreenCanvas
      optimizeImageMainThread(file, mergedOptions).then(resolve).catch(reject);
    }
  });
};

/**
 * Fallback image optimization on the main thread
 */
const optimizeImageMainThread = async (
  file: File,
  options: ImageOptimizationOptions
): Promise<File> => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = (): void => {
      try {
        const { width, height } = calculateScaledDimensions(img.width, img.height, options.maxWidth, options.maxHeight, 4096);

        canvas.width = width;
        canvas.height = height;

        // Drawing onto canvas strips EXIF metadata (GPS, device serial) for privacy
        if (!ctx) {
          throw new Error('Failed to get 2d canvas context');
        }
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            URL.revokeObjectURL(objectUrl);
            if (!blob) {
              reject(new Error('Failed to optimize image'));
              return;
            }

            const optimizedFile = new File(
              [blob],
              file.name.replace(/\.[^/.]+$/, '') + `.${options.format}`,
              {
                type: `image/${options.format}`,
                lastModified: Date.now(),
              }
            );

            resolve(optimizedFile);
          },
          `image/${options.format}`,
          (options.quality || 85) / 100
        );
      } catch (err) {
        URL.revokeObjectURL(objectUrl);
        reject(err instanceof Error ? err : new Error('Canvas render error'));
      }
    };

    img.onerror = (): void => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error('Failed to load image file'));
    };
    const objectUrl = URL.createObjectURL(file);
    img.src = objectUrl;
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
    const src = isCDNAvailable() ? getCDNUrl(imageUrl, options) : imageUrl;

    sources.push({
      srcSet: `${src} ${width}w`,
    });
  }

  return sources;
};

/**
 * Create a responsive image element with proper srcset and sizes
 */
/**
 * Preload critical images
 */
export const preloadImage = (url: string, options?: ImageOptimizationOptions): Promise<void> => {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = isCDNAvailable() ? getCDNUrl(url, options) : url;

    const cleanup = (): void => {
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
    };

    link.onload = (): void => {
      cleanup();
      resolve();
    };
    link.onerror = (): void => {
      cleanup();
      reject(new Error(`Failed to preload image: ${url}`));
    };

    document.head.appendChild(link);
  });
};

/**
 * Get image dimensions without loading the full image
 */
/**
 * Validate image file with edge case protections
 */
export const validateImageFile = (
  file: File,
  maxSizeMB: number = 10,
  allowedTypes: string[] = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
): { valid: boolean; error?: string } => {
  if (!file) {
    return {
      valid: false,
      error: 'Invalid file.',
    };
  }

  // Edge case: HEIC/HEIF or RAW formats from iPhone/camera
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (['heic', 'heif', 'raw', 'cr2', 'nef', 'dng'].includes(ext || '')) {
    return {
      valid: false,
      error: 'HEIC or RAW photo format is not supported directly. Please convert to JPG or PNG before uploading.',
    };
  }

  // Check file type
  if (file.type && !allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: `Invalid file type. Allowed formats: JPG, PNG, WEBP, GIF`,
    };
  }

  // Check file size limit
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  if (file.size > maxSizeBytes) {
    return {
      valid: false,
      error: `File too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Maximum allowed size is ${maxSizeMB}MB`,
    };
  }

  return { valid: true };
};

/**
 * Generate a thumbnail for an image
 */
