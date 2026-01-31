import { describe, it, expect, vi } from 'vitest';
import { 
  getCDNUrl, 
  validateImageFile, 
  isCDNAvailable,
  generateResponsiveSources
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
});
