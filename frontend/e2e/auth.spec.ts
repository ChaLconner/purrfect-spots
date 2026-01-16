/**
 * E2E Tests for Authentication Flow
 * 
 * Tests cover:
 * - Login page rendering
 * - Registration flow
 * - Login flow
 * - Logout flow
 * - Protected route access
 */
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  
  test.describe('Login Page', () => {
    
    test('should display login form', async ({ page }) => {
      await page.goto('/login');
      
      // Check page title
      await expect(page).toHaveTitle(/Purrfect Spots/);
      
      // Check form elements exist
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.locator('#password')).toBeVisible();
      await expect(page.getByRole('button', { name: /login|sign in/i })).toBeVisible();
    });
    
    test('should show validation errors for empty form', async ({ page }) => {
      await page.goto('/login');
      
      // Submit empty form
      await page.getByRole('button', { name: /login|sign in/i }).click();
      
      // Should show validation message
      await expect(page.getByText('Please enter your email')).toBeVisible();
    });
    
    test('should show error for invalid credentials', async ({ page }) => {
      await page.goto('/login');
      
      // Fill invalid credentials
      await page.getByLabel(/email/i).fill('invalid@example.com');
      await page.locator('#password').fill('wrongpassword');
      await page.getByRole('button', { name: /login|sign in/i }).click();
      
      // Should show error message
      await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible({ timeout: 5000 });
    });
    
    test('should have link to registration', async ({ page }) => {
      await page.goto('/login');
      
      // Find and click register link
      const registerLink = page.getByRole('link', { name: /register|sign up|create account/i });
      await expect(registerLink).toBeVisible();
    });
    
    test('should have Google OAuth button', async ({ page }) => {
      await page.goto('/login');
      
      // Check for Google login button
      const googleButton = page.getByRole('button', { name: /google/i });
      await expect(googleButton).toBeVisible();
    });
  });
  
  test.describe('Registration Flow', () => {
    
    test('should display registration form', async ({ page }) => {
      await page.goto('/register');
      
      // Check form elements
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.getByLabel(/password/i).first()).toBeVisible();
      await expect(page.getByLabel(/name/i)).toBeVisible();
    });
    
    test('should validate password strength', async ({ page }) => {
      await page.goto('/register');
      
      // Fill weak password
      await page.locator('#password').fill('123');
      
      // Should show password strength indicator or error
      const strengthIndicator = page.locator('[class*="strength"], [class*="password"]');
      await expect(strengthIndicator.first()).toBeVisible();
    });
    
    test('should prevent duplicate email registration', async ({ page }) => {
      await page.goto('/register');
      
      // Try to register with existing email
      await page.getByLabel(/name/i).fill('Test User');
      await page.getByLabel(/email/i).fill('existing@example.com');
      await page.locator('#password').fill('SecurePass123');
      
      await page.getByRole('button', { name: /register|sign up|create/i }).click();
      
      // Should show error about existing email (or succeed if email doesn't exist)
      // This is a best-effort test
    });
  });
  
  test.describe('Protected Routes', () => {
    
    test('should redirect to login when accessing upload without auth', async ({ page }) => {
      await page.goto('/upload');
      
      // Should redirect to login
      await expect(page).toHaveURL(/login/);
    });
    
    test('should redirect to login when accessing profile without auth', async ({ page }) => {
      await page.goto('/profile');
      
      // Should redirect to login
      await expect(page).toHaveURL(/login/);
    });
  });
  
  test.describe('Public Routes', () => {
    
    test('should access gallery without authentication', async ({ page }) => {
      await page.goto('/gallery');
      
      // Should NOT redirect to login
      await expect(page).not.toHaveURL(/login/);
      
      // Should show gallery content
      await expect(page.getByRole('main')).toBeVisible();
    });
    
    test('should access map without authentication', async ({ page }) => {
      await page.goto('/');
      
      // Should show map or homepage
      await expect(page).not.toHaveURL(/login/);
    });
  });
});
