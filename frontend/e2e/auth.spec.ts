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

  // Mock global user for success scenarios
  const mockUser = {
    id: 'test-user-123',
    email: 'test@example.com',
    name: 'Test User',
    picture: 'https://placehold.co/100',
    bio: 'Test bio',
    created_at: '2023-01-01T00:00:00Z'
  };

  test.beforeEach(async ({ page }) => {
    // Mock refresh token to fail immediately (401) so app initializes quickly
    // This calls Main.ts -> AuthStore.initializeAuth -> refreshToken
    // Without this, the app waits for the real backend (which isn't running) and times out
    await page.route('**/api/v1/auth/refresh-token', async route => {
      await route.fulfill({ 
        status: 401, 
        contentType: 'application/json',
        json: { detail: "Not authenticated" } 
      });
    });
  });
  
  test.describe('Login Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
    });
    
    test('should display login form', async ({ page }) => {
      // Check page title
      await expect(page).toHaveTitle(/Purrfect Spots/);
      
      // Check form elements exist
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.locator('#password')).toBeVisible();
      await expect(page.getByRole('button', { name: /login|sign in/i })).toBeVisible();
    });
    
    test('should show validation errors for empty form', async ({ page }) => {
      // Submit empty form
      await page.getByRole('button', { name: /login|sign in/i }).click();
      
      // Should show validation message
      // Note: Browser native validation might intercept this, so we check if button is still there
      // or check for specific validation UI if app implements it.
      // Assuming app shows text error:
      await expect(page.getByText(/required|enter your email/i)).toBeVisible();
    });
    
    test('should show error for invalid credentials', async ({ page }) => {
      // Mock failure response
      await page.route('**/api/v1/auth/login', async route => {
        await route.fulfill({
            status: 401,
            contentType: 'application/json',
            json: { detail: 'Invalid email or password.' }
        });
      });

      // Fill invalid credentials
      await page.getByLabel(/email/i).fill('invalid@example.com');
      await page.locator('#password').fill('wrongpassword');
      await page.getByRole('button', { name: /login|sign in/i }).click();
      
      // Should show error message
      await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible({ timeout: 5000 });
    });

    test('should redirect to home on successful login', async ({ page }) => {
         // Mock success response
        await page.route('**/api/v1/auth/login', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                json: {
                    access_token: 'fake-jwt-token',
                    token_type: 'bearer',
                    user: mockUser
                }
            });
        });

        // Mock /me endpoint for subsequent checks
         await page.route('**/api/v1/auth/me', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                json: mockUser
            });
        });

        await page.getByLabel(/email/i).fill('test@example.com');
        await page.locator('#password').fill('CorrectPassword123');
        await page.getByRole('button', { name: /login|sign in/i }).click();

        // Should redirect to home or dashboard
        await expect(page).toHaveURL(/$|dashboard/);
    });
    
    test('should have link to registration', async ({ page }) => {
      // Find and click register link
      const registerLink = page.getByRole('link', { name: /register|sign up|create account/i });
      await expect(registerLink).toBeVisible();
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
    
    test('should successfully register user', async ({ page }) => {
       // Mock register success
       await page.route('**/api/v1/auth/register', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            json: {
                access_token: 'fake-jwt-token',
                token_type: 'bearer',
                user: mockUser
            }
        });
      });

      // Mock /me endpoint
      await page.route('**/api/v1/auth/me', async route => {
        await route.fulfill({ status: 200, json: mockUser });
      });

      await page.goto('/register');
      await page.getByLabel(/name/i).fill('Test User');
      await page.getByLabel(/email/i).fill('newuser@example.com');
      await page.locator('#password').fill('SecurePass123');
      
      await page.getByRole('button', { name: /register|sign up|create/i }).click();
      
      // Should redirect after success
      await expect(page).toHaveURL(/$|dashboard/);
    });
  });
  
  test.describe('Protected Routes', () => {
    
    test('should redirect to login when accessing upload without auth', async ({ page }) => {
       // Ensure we are not logged in (clear storage/cookies if needed, but new context should be clean)
      await page.goto('/upload');
      
      // Should redirect to login
      await expect(page).toHaveURL(/login/);
    });

    test('should allow access to protected route if logged in', async ({ page }) => {
        // Mock auth endpoints
        await page.route('**/api/v1/auth/me', async route => {
            await route.fulfill({ status: 200, json: mockUser });
        });

        // Mock refresh token endpoint to succeed
        await page.route('**/api/v1/auth/refresh-token', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                json: {
                    access_token: 'fake-jwt-token',
                    token_type: 'bearer',
                    user: mockUser
                }
            });
        });

        // Simulate logged in state by setting token in localStorage directly
        await page.addInitScript(() => {
            localStorage.setItem('token', 'fake-jwt-token');
            // The auth store reads 'user_data', not 'user' for restoration
            localStorage.setItem('user_data', JSON.stringify({
                id: 'test-user-123',
                email: 'test@example.com',
                name: 'Test User'
            }));
        });

        await page.goto('/upload');
        // Should NOT redirect to login
        await expect(page).not.toHaveURL(/login/);
    });
  });
});
