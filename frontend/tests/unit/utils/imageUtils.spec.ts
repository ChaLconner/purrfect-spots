import { describe, it, expect, vi, beforeAll } from 'vitest';
import { validateImageFile, imageToBase64 } from '@/utils/imageUtils';

describe('imageUtils', () => {
  beforeAll(() => {
    // Mock URL methods
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = vi.fn();
  });

  describe('validateImageFile', () => {
    it('should return valid true for correct file type and size', () => {
      const file = new File([''], 'cat.jpg', { type: 'image/jpeg' });
      // Mock size getter since File/Blob size is based on content
      Object.defineProperty(file, 'size', { value: 1024 });

      const result = validateImageFile(file);
      expect(result.valid).toBe(true);
    });

    it('should return valid false for incorrect file type', () => {
      const file = new File([''], 'document.pdf', { type: 'application/pdf' });
      const result = validateImageFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid file type');
    });

    it('should return valid false for too large file', () => {
      const file = new File([''], 'large.jpg', { type: 'image/jpeg' });
      // 11MB
      Object.defineProperty(file, 'size', { value: 11 * 1024 * 1024 });

      const result = validateImageFile(file, 10); // Max 10MB
      expect(result.valid).toBe(false);
      expect(result.error).toContain('File too large');
    });
  });

  describe('imageToBase64', () => {
    it('should convert file to base64 string', async () => {
      const file = new File(['content'], 'test.txt', { type: 'text/plain' });
      
      // Mock FileReader
      const mockFileReader = {
        readAsDataURL: vi.fn(),
        result: 'data:text/plain;base64,content',
        onload: null as any,
        onerror: null as any,
      };
      
      // Hijack the global FileReader
      const originalFileReader = global.FileReader;
      
      // Use a class because 'new FileReader()' is called
      global.FileReader = class {
        constructor() {
          // Return our mock object instead of a real instance
          return mockFileReader as any;
        }
      } as any;

      try {
        const promise = imageToBase64(file);
        
        // Simulate onload
        if (mockFileReader.onload) {
            mockFileReader.onload({} as any);
        }
        
        const result = await promise;
        expect(result).toBe('data:text/plain;base64,content');
      } finally {
        global.FileReader = originalFileReader;
      }
    });
  });
});
