import { describe, it, expect, vi } from 'vitest';
import { 
  getCDNUrl, 
  validateImageFile, 
  isCDNAvailable,
  generateResponsiveSources,
  preloadImage,
} from '@/utils/imageUtils';



// Mock env module
vi.mock('@/utils/env', () => ({
  isProd: vi.fn(() => true),
  isDev: vi.fn(() => false),
  getEnvVar: vi.fn(),
}));

describe('Image Utils', () => {

  describe('isCDNAvailable', () => {
    it('is defined', () => {
        expect(isCDNAvailable).toBeDefined();
    });
  });

  describe('validateImageFile', () => {
    it('validates correct file', () => {
      const file = new File([''], 'test.jpg', { type: 'image/jpeg' });
      const result = validateImageFile(file);
      expect(result.valid).toBe(true);
    });

    it('rejects invalid type', () => {
      const file = new File([''], 'test.txt', { type: 'text/plain' });
      const result = validateImageFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid file type');
    });

    it('rejects large file', () => {
      const file = { 
        name: 'large.jpg', 
        type: 'image/jpeg', 
        size: 20 * 1024 * 1024 
      } as File;
      
      const result = validateImageFile(file, 10); // 10MB limit
      expect(result.valid).toBe(false);
      expect(result.error).toContain('File too large');
    });
  });

  describe('getCDNUrl', () => {
      it('returns original URL if CDN disabled', () => {
          const url = 'https://example.com/img.jpg';
          const result = getCDNUrl(url);
          expect(result).toBe(url);
      });

      it('builds Supabase transformations for all configured dimensions', () => {
          const result = getCDNUrl(
            'https://project.supabase.co/storage/v1/object/public/cats/cat.jpg',
            { maxWidth: 640, maxHeight: 480, quality: 70, format: 'jpeg' }
          );
          const url = new URL(result);

          expect(url.searchParams.get('width')).toBe('640');
          expect(url.searchParams.get('height')).toBe('480');
          expect(url.searchParams.get('quality')).toBe('70');
          expect(url.searchParams.get('format')).toBe('jpeg');
          expect(url.searchParams.get('resize')).toBe('cover');
      });

      it('uses the resize proxy for external images', () => {
          const result = getCDNUrl('https://images.example.com/cat.jpg', {
            maxWidth: 320,
            maxHeight: 240,
            format: 'png',
          });
          const url = new URL(result);

          expect(url.hostname).toBe('wsrv.nl');
          expect(url.searchParams.get('w')).toBe('320');
          expect(url.searchParams.get('h')).toBe('240');
          expect(url.searchParams.get('q')).toBe('80');
          expect(url.searchParams.get('output')).toBe('png');
      });
  });

  describe('generateResponsiveSources', () => {
      it('generates sources for multiple widths', () => {
          const url = 'https://example.com/img.jpg';
          const sources = generateResponsiveSources(url);
          
          expect(sources.length).toBeGreaterThan(0);
          expect(sources[0].srcSet).toContain(url);
          expect(sources[0].srcSet).toContain('w'); // checks for width descriptor
      });

      it('respects base options', () => {
         // Since isCDNAvailable returns false in default mock setup (missing env var),
         // generateResponsiveSources just returns original url + width descriptor.
         const url = '/img.jpg';
         const sources = generateResponsiveSources(url, { format: 'webp' });
         expect(sources[0].srcSet).toContain('/img.jpg');
      });
  });

  describe('preloadImage', () => {
    it('cleans up the injected preload link after loading', async () => {
      const appendSpy = vi.spyOn(document.head, 'appendChild');

      const preloadPromise = preloadImage('https://example.com/cat.jpg');
      const injectedLink = appendSpy.mock.calls.at(-1)?.[0] as HTMLLinkElement;

      expect(injectedLink?.rel).toBe('preload');
      expect(document.head.contains(injectedLink)).toBe(true);

      injectedLink.onload?.(new Event('load'));
      await preloadPromise;

      expect(document.head.contains(injectedLink)).toBe(false);

      appendSpy.mockRestore();
    });
  });
});
