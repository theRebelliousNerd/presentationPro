import { test, expect } from '@playwright/test';

test.describe('Workflow Insights Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="app-loaded"]', { timeout: 15000 });
  });

  test('opens and closes workflow panel with placeholder trace', async ({ page }) => {
    await test.step('Open workflow panel', async () => {
      await page.getByLabel('Workflow').click();
      await expect(page.getByText('No trace entries returned.')).toBeVisible();
    });

    await test.step('Close workflow panel', async () => {
      await page.getByLabel('Workflow').click();
      await expect(page.getByText('No trace entries returned.')).toHaveCount(0);
    });
  });
});
