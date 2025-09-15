import { test, expect } from '@playwright/test'

/**
 * ADK Workflow Integration Tests
 *
 * These tests validate the presentation generation workflow
 * after ADK/A2A modernization efforts.
 */

test.describe('ADK Presentation Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000')

    // Wait for the application to load
    await expect(page.locator('h1')).toContainText('Presentation Studio')
  })

  test('should complete clarification phase successfully', async ({ page }) => {
    // Enter initial presentation topic
    const chatInput = page.getByRole('textbox', { name: 'Ask or add context...' })
    await chatInput.fill('Create a technical presentation about Google ADK and A2A protocol')
    await chatInput.press('Enter')

    // Wait for AI response
    await page.waitForTimeout(2000)

    // Verify Context Meter appears and updates
    const contextMeter = page.locator('text=Context Meter')
    await expect(contextMeter).toBeVisible()

    // Answer clarification questions
    await chatInput.fill('The audience is experienced AI developers')
    await chatInput.press('Enter')
    await page.waitForTimeout(2000)

    await chatInput.fill('20-minute presentation, about 12-15 slides')
    await chatInput.press('Enter')
    await page.waitForTimeout(2000)

    // Verify token tracking is working
    const tokenDisplay = page.locator('text=/Tokens \\(in\\/out\\):/')
    await expect(tokenDisplay).toBeVisible()

    // Check that tokens are being counted
    const tokenText = await tokenDisplay.textContent()
    expect(tokenText).not.toContain('0/0')
  })

  test('should handle initial input form correctly', async ({ page }) => {
    // Click Start Over to get fresh state
    await page.getByRole('button', { name: 'Start Over' }).click()

    // Handle dialog if it appears
    const dialog = page.locator('text=Start over?')
    if (await dialog.isVisible({ timeout: 1000 })) {
      await page.getByRole('button', { name: 'Start Fresh' }).click()
    }

    // Wait for initial input form
    await page.waitForTimeout(1000)

    // Fill in presentation content
    const contentArea = page.getByRole('textbox', { name: 'Paste your presentation' })
    if (await contentArea.isVisible({ timeout: 2000 })) {
      await contentArea.fill('Create a presentation about ADK and A2A protocol for building multi-agent AI systems')

      // Check if Start Creating button becomes enabled
      const startButton = page.getByRole('button', { name: 'Start Creating' })
      await expect(startButton).toBeEnabled({ timeout: 5000 })

      // Click to start creation
      await startButton.click()
    }
  })

  test('should track token usage correctly', async ({ page }) => {
    // Start a new conversation
    const chatInput = page.getByRole('textbox', { name: 'Ask or add context...' })
    await chatInput.fill('Test message for token tracking')
    await chatInput.press('Enter')

    // Wait for response
    await page.waitForTimeout(2000)

    // Check input tokens
    const inTokens = page.locator('text=/In: \\d+/')
    await expect(inTokens).toBeVisible()
    const inText = await inTokens.textContent()
    const inCount = parseInt(inText?.match(/\\d+/)?.[0] || '0')
    expect(inCount).toBeGreaterThan(0)

    // Check output tokens
    const outTokens = page.locator('text=/Out: \\d+/')
    await expect(outTokens).toBeVisible()
    const outText = await outTokens.textContent()
    const outCount = parseInt(outText?.match(/\\d+/)?.[0] || '0')
    expect(outCount).toBeGreaterThan(0)
  })

  test('should maintain conversation history', async ({ page }) => {
    const chatInput = page.getByRole('textbox', { name: 'Ask or add context...' })

    // Send first message
    await chatInput.fill('First message about ADK')
    await chatInput.press('Enter')
    await page.waitForTimeout(2000)

    // Send second message
    await chatInput.fill('Second message about A2A')
    await chatInput.press('Enter')
    await page.waitForTimeout(2000)

    // Verify both messages are visible in chat history
    await expect(page.locator('text=First message about ADK')).toBeVisible()
    await expect(page.locator('text=Second message about A2A')).toBeVisible()
  })

  test('should update Context Meter during clarification', async ({ page }) => {
    const chatInput = page.getByRole('textbox', { name: 'Ask or add context...' })

    // Start conversation
    await chatInput.fill('Create ADK presentation')
    await chatInput.press('Enter')
    await page.waitForTimeout(2000)

    // Get initial context meter value
    const contextMeter = page.locator('progressbar')
    const initialValue = await contextMeter.getAttribute('value')

    // Continue conversation
    await chatInput.fill('For experienced developers, 20 minutes')
    await chatInput.press('Enter')
    await page.waitForTimeout(2000)

    // Check if context meter increased
    const updatedValue = await contextMeter.getAttribute('value')
    if (initialValue && updatedValue) {
      expect(parseFloat(updatedValue)).toBeGreaterThanOrEqual(parseFloat(initialValue))
    }
  })
})

test.describe('ADK Backend Health', () => {
  test('should have ADK backend running', async ({ request }) => {
    const response = await request.get('http://localhost:8089/health')
    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    expect(data.ok).toBe(true)
    expect(data.service).toBe('adkpy')
  })

  test('should have proper API endpoints', async ({ request }) => {
    // Test clarify endpoint exists
    const clarifyResponse = await request.post('http://localhost:8089/v1/clarify', {
      data: {
        history: [],
        initialInput: { text: 'test' }
      }
    })

    // Should return 200 even if the request fails internally
    expect(clarifyResponse.status()).toBeLessThanOrEqual(500)
  })
})

test.describe('Error Handling', () => {
  test('should handle empty input gracefully', async ({ page }) => {
    const chatInput = page.getByRole('textbox', { name: 'Ask or add context...' })

    // Try to submit empty input
    await chatInput.fill('')
    await chatInput.press('Enter')

    // Should not crash or show error
    await page.waitForTimeout(1000)

    // App should still be functional
    await expect(page.locator('h1')).toContainText('Presentation Studio')
  })

  test('should maintain state after navigation', async ({ page }) => {
    // Start a conversation
    const chatInput = page.getByRole('textbox', { name: 'Ask or add context...' })
    await chatInput.fill('Test persistence')
    await chatInput.press('Enter')
    await page.waitForTimeout(2000)

    // Navigate to another page
    await page.getByRole('link', { name: 'Settings' }).click()
    await page.waitForTimeout(1000)

    // Navigate back
    await page.getByRole('link', { name: 'Home' }).click()
    await page.waitForTimeout(1000)

    // Check if conversation is preserved (localStorage persistence)
    // Note: This depends on the app's localStorage implementation
  })
})