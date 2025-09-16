import { test, expect } from '@playwright/test'

const TOOL_NAMES = [
  'critic.color_contrast',
  'critic.assess_blur',
  'critic.measure_noise',
  'critic.check_color_contrast_ratio',
  'design.saliency_spectral',
  'design.find_empty_regions',
  'design.extract_palette',
  'design.suggest_placement',
  'design.generate_procedural_texture',
  'research.ocr_extract',
  'brand.detect_logo',
  'brand.validate_brand_colors',
  'research.extract_data_from_bar_chart',
  'research.extract_data_from_line_graph',
]

const SAMPLE_IMAGE_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAuwB9VEZCBcAAAAASUVORK5CYII='

test.describe('VisionCV developer tooling page', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/dev/visioncv/proxy?path=/v1/visioncv/tools', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ tools: TOOL_NAMES.map(name => ({ name })) }),
      })
    })

    await page.route('**/api/dev/visioncv/proxy', async route => {
      if (route.request().method() === 'POST') {
        try {
          const payload = await route.request().postDataJSON() as { path?: string }
          if (payload?.path === '/v1/visioncv/procedural_texture') {
            return await route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({ image_b64: SAMPLE_IMAGE_B64 }),
            })
          }
        } catch (err) {
          // Ignore JSON parsing errors and fall through to default response
        }
        return await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ok: true }),
        })
      }
      return route.continue()
    })

    await page.goto('/dev/visioncv')
  })

  test('lists new tools and renders image responses', async ({ page }) => {
    const selector = page.locator('select')
    await expect(selector).toBeVisible()

    // Ensure the new tools are surfaced in the dropdown
    await selector.focus()
    for (const name of ['design.generate_procedural_texture', 'design.extract_palette', 'critic.measure_noise', 'critic.check_color_contrast_ratio']) {
      await expect(page.getByRole('option', { name })).toBeVisible()
    }

    // Contrast ratio tool should not require an upload
    await selector.selectOption('critic.check_color_contrast_ratio')
    const requestArea = page.locator('textarea').first()
    await expect(requestArea).toContainText('"fg"')
    await expect(page.locator('text=No image upload needed')).toBeVisible()

    // Switch to procedural texture generator and trigger a call
    await selector.selectOption('design.generate_procedural_texture')
    await expect(requestArea).toContainText('"texture_type"')
    await page.getByRole('button', { name: 'Call' }).click()

    const responseArea = page.locator('textarea').last()
    await expect(responseArea).toContainText('image_b64')
    await expect(page.locator('img[alt="Generated output"]')).toBeVisible()
  })
})
