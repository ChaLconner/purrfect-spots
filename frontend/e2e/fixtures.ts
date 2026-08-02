import { test as base, expect } from '@playwright/test';

/**
 * Per-test browser isolation.
 *
 * E2E specs use mocked API data, so a database seed would add a shared state
 * dependency without improving coverage. Clear browser state before each
 * navigation and after each test instead.
 */
export const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    const testRunId = `${testInfo.project.name}:${testInfo.testId}`;

    await page.addInitScript((runId: string) => {
      window.localStorage.clear();
      window.sessionStorage.clear();
      window.localStorage.setItem('__e2e_test_run_id', runId);
    }, testRunId);

    try {
      await use(page);
    } finally {
      await page.context().clearCookies();
      try {
        await page.evaluate(() => {
          window.localStorage.clear();
          window.sessionStorage.clear();
        });
      } catch {
        // Page may already be closed after a failed test.
      }
    }
  },
});

export { expect };
