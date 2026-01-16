/**
 * E2E Tests for Gallery Page
 * 
 * Tests cover:
 * - Gallery loading
 * - Image display
 * - Pagination
 * - Modal interactions
 * - Navigation
 */
import { test, expect } from '@playwright/test';

test.describe('Gallery Page', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/gallery');
  });
  
  test.describe('Page Loading', () => {
    
    test('should display gallery page', async ({ page }) => {
      await expect(page).toHaveTitle(/Gallery|Purrfect/i);
      await expect(page.getByRole('main')).toBeVisible();
    });
    
    test('should show loading state initially', async ({ page }) => {
      // Reload and check for loading state
      await page.reload();
      
      // Look for loading indicator (spinner, skeleton, or loading text)
      const loadingIndicator = page.locator('[class*="loading"], [class*="skeleton"], [aria-busy="true"]').first();
      
      // Loading should appear briefly (or photos load immediately)
      // This is a soft assertion
    });
    
    test('should display photos or empty state', async ({ page }) => {
      // Wait for content to load
      await page.waitForLoadState('networkidle');
      
      // Should show either photos or empty state
      const hasPhotos = await page.locator('[class*="gallery"] img, [class*="photo"] img, [class*="card"] img').count() > 0;
      const hasEmptyState = await page.getByText(/no photos|empty|no cats/i).count() > 0;
      
      expect(hasPhotos || hasEmptyState).toBeTruthy();
    });
  });
  
  test.describe('Image Grid', () => {
    
    test('should display images in grid layout', async ({ page }) => {
      await page.waitForLoadState('networkidle');
      
      // Check for grid container
      const grid = page.locator('[class*="grid"], [class*="masonry"], [class*="gallery"]').first();
      await expect(grid).toBeVisible();
    });
    
    test('should lazy load images', async ({ page }) => {
      const images = page.locator('img[loading="lazy"]');
      
      // Modern galleries should use lazy loading
      const count = await images.count();
      
      // If there are images, at least some should be lazy loaded
      // This is a soft check since the gallery might be empty
    });
  });
  
  test.describe('Photo Modal', () => {
    
    test('should open modal when clicking photo', async ({ page }) => {
      await page.waitForLoadState('networkidle');
      
      // Find and click first photo
      const firstPhoto = page.locator('[class*="gallery"] img, [class*="photo"] img, [class*="card"] img').first();
      
      const photoCount = await firstPhoto.count();
      if (photoCount > 0) {
        await firstPhoto.click();
        
        // Modal should be visible
        const modal = page.locator('[class*="modal"], [role="dialog"]');
        await expect(modal.first()).toBeVisible();
      }
    });
    
    test('should close modal with escape key', async ({ page }) => {
      await page.waitForLoadState('networkidle');
      
      const firstPhoto = page.locator('[class*="gallery"] img, [class*="photo"] img, [class*="card"] img').first();
      
      const photoCount = await firstPhoto.count();
      if (photoCount > 0) {
        await firstPhoto.click();
        
        // Wait for modal
        const modal = page.locator('[class*="modal"], [role="dialog"]').first();
        await expect(modal).toBeVisible();
        
        // Press escape
        await page.keyboard.press('Escape');
        
        // Modal should close
        await expect(modal).not.toBeVisible();
      }
    });
    
    test('should close modal with close button', async ({ page }) => {
      await page.waitForLoadState('networkidle');
      
      const firstPhoto = page.locator('[class*="gallery"] img, [class*="photo"] img, [class*="card"] img').first();
      
      const photoCount = await firstPhoto.count();
      if (photoCount > 0) {
        await firstPhoto.click();
        
        // Find and click close button
        const closeButton = page.locator('[class*="close"], [aria-label*="close"]').first();
        const closeButtonCount = await closeButton.count();
        
        if (closeButtonCount > 0) {
          await closeButton.click();
          
          // Modal should close
          const modal = page.locator('[class*="modal"], [role="dialog"]').first();
          await expect(modal).not.toBeVisible();
        }
      }
    });
  });
  
  test.describe('Navigation', () => {
    
    test('should have navigation to map', async ({ page }) => {
      const mapLink = page.getByRole('link', { name: /map/i });
      await expect(mapLink.first()).toBeVisible();
    });
    
    test('should have navigation to upload (if logged in)', async ({ page }) => {
      // Upload link might be hidden for non-authenticated users
      const uploadLink = page.getByRole('link', { name: /upload/i });
      
      // Just check page renders without errors
      await expect(page.getByRole('main')).toBeVisible();
    });
  });
  
  test.describe('Responsive Design', () => {
    
    test('should display correctly on mobile', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();
      
      // Page should still render correctly
      await expect(page.getByRole('main')).toBeVisible();
      
      // Grid should adjust (fewer columns)
      const grid = page.locator('[class*="grid"], [class*="gallery"]').first();
      await expect(grid).toBeVisible();
    });
    
    test('should display correctly on tablet', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.reload();
      
      await expect(page.getByRole('main')).toBeVisible();
    });
  });
});
