import { defineConfig, devices } from '@playwright/test';

/**
 * Purrfect Spots E2E Test Configuration
 * 
 * Run all tests:
 *   npx playwright test
 * 
 * Run in headed mode:
 *   npx playwright test --headed
 * 
 * Run specific test file:
 *   npx playwright test e2e/auth.spec.ts
 */
export default defineConfig({
  // Test directory
  testDir: './e2e',
  
  // Test files pattern
  testMatch: '**/*.spec.ts',
  
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Limit parallel workers on CI
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }]
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: process.env.CI ? 'http://localhost:4173' : (process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173'),
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Capture screenshot on failure
    screenshot: 'only-on-failure',
    
    // Record video on failure
    video: 'on-first-retry',
    
    // Maximum time for each action
    actionTimeout: 10000,
    
    // Navigation timeout
    navigationTimeout: 30000,
  },
  
  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    
    // Mobile testing
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  
  // Run dev server before tests
  webServer: {
    command: process.env.CI ? 'npm run preview -- --port 4173' : 'npm run dev -- --host',
    url: process.env.CI ? 'http://localhost:4173' : 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
  
  // Output folder for test artifacts
  outputDir: 'test-results',
  
  // Global timeout for each test
  timeout: 60000,
  
  // Expect timeout
  expect: {
    timeout: 10000,
  },
});
