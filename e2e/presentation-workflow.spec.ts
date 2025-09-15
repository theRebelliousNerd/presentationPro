import { test, expect } from '@playwright/test';

test.describe('Presentation Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the application to load
    await page.waitForSelector('[data-testid="app-loaded"]', { timeout: 10000 });
  });

  test('complete presentation creation workflow', async ({ page }) => {
    // Step 1: Initial Input
    await test.step('Fill initial input form', async () => {
      // Wait for initial input form
      await page.waitForSelector('[data-testid="initial-input-form"]');
      
      // Fill presentation details
      await page.fill('[data-testid="presentation-text-input"]', 
        'Create a presentation about the future of artificial intelligence in healthcare, focusing on diagnostic applications and patient outcomes.');
      
      // Set presentation length
      await page.selectOption('[data-testid="presentation-length"]', '10-15 slides');
      
      // Set audience
      await page.fill('[data-testid="audience-input"]', 'Medical professionals and healthcare executives');
      
      // Set industry
      await page.selectOption('[data-testid="industry-select"]', 'Healthcare');
      
      // Set tone
      await page.getByRole('slider', { name: 'Formality' }).fill('75');
      await page.getByRole('slider', { name: 'Energy' }).fill('60');
      
      // Start clarification
      await page.click('[data-testid="start-clarification-btn"]');
    });

    // Step 2: Clarification Process
    await test.step('Navigate clarification chat', async () => {
      // Wait for clarification interface
      await page.waitForSelector('[data-testid="clarification-chat"]');
      
      // Verify context meter is visible
      await expect(page.locator('[data-testid="context-meter"]')).toBeVisible();
      
      // Look for AI questions
      await page.waitForSelector('[data-testid="ai-message"]', { timeout: 15000 });
      
      // Simulate answering clarification questions
      const chatInput = page.locator('[data-testid="chat-input"]');
      
      // Answer first question
      await chatInput.fill('Focus on machine learning algorithms for medical imaging, particularly MRI and CT scan analysis. Include real-world case studies from major hospitals.');
      await page.click('[data-testid="send-message-btn"]');
      
      // Wait for response and context meter update
      await page.waitForSelector('[data-testid="ai-message"]', { timeout: 15000 });
      
      // Continue until context meter reaches sufficient level (>25%)
      let contextMeter = await page.locator('[data-testid="context-meter-value"]').textContent();
      let contextValue = parseInt(contextMeter?.replace('%', '') || '0');
      
      while (contextValue < 30) {
        await chatInput.fill('Include specific examples of AI reducing diagnostic errors and improving treatment timelines. Show before/after statistics.');
        await page.click('[data-testid="send-message-btn"]');
        await page.waitForTimeout(2000);
        
        contextMeter = await page.locator('[data-testid="context-meter-value"]').textContent();
        contextValue = parseInt(contextMeter?.replace('%', '') || '0');
        
        if (contextValue >= 30) break;
      }
      
      // Complete clarification
      await page.click('[data-testid="complete-clarification-btn"]');
    });

    // Step 3: Outline Approval
    await test.step('Review and approve outline', async () => {
      // Wait for outline approval screen
      await page.waitForSelector('[data-testid="outline-approval"]', { timeout: 20000 });
      
      // Verify outline is generated
      const outlineItems = page.locator('[data-testid="outline-item"]');
      await expect(outlineItems).toHaveCountGreaterThan(5);
      
      // Check that outline items contain relevant content
      const firstSlide = outlineItems.first();
      await expect(firstSlide).toContainText(/AI|artificial intelligence|healthcare/i);
      
      // Approve the outline
      await page.click('[data-testid="approve-outline-btn"]');
    });

    // Step 4: Slide Generation
    await test.step('Monitor slide generation progress', async () => {
      // Wait for generation spinner
      await page.waitForSelector('[data-testid="generating-spinner"]');
      
      // Verify progress indicator
      await expect(page.locator('[data-testid="generation-progress"]')).toBeVisible();
      
      // Wait for generation to complete (this may take several minutes)
      await page.waitForSelector('[data-testid="editor-interface"]', { timeout: 300000 }); // 5 minutes
    });

    // Step 5: Slide Editor
    await test.step('Verify editor interface', async () => {
      // Check that slides are generated
      const slideCards = page.locator('[data-testid="slide-card"]');
      await expect(slideCards).toHaveCountGreaterThan(5);
      
      // Select first slide
      await slideCards.first().click();
      
      // Verify slide content is loaded
      await expect(page.locator('[data-testid="slide-content"]')).toBeVisible();
      await expect(page.locator('[data-testid="speaker-notes"]')).toBeVisible();
      
      // Test slide editing
      await page.click('[data-testid="edit-slide-content-btn"]');
      await page.fill('[data-testid="slide-title-input"]', 'AI in Healthcare: Revolutionary Diagnostics');
      await page.click('[data-testid="save-slide-btn"]');
      
      // Verify changes are saved
      await expect(page.locator('[data-testid="slide-title"]')).toContainText('Revolutionary Diagnostics');
    });

    // Step 6: Test Export Functionality
    await test.step('Test presentation export', async () => {
      // Open export menu
      await page.click('[data-testid="export-menu-btn"]');
      
      // Verify export options
      await expect(page.locator('[data-testid="export-powerpoint"]')).toBeVisible();
      await expect(page.locator('[data-testid="export-pdf"]')).toBeVisible();
      
      // Test PowerPoint export
      const downloadPromise = page.waitForEvent('download');
      await page.click('[data-testid="export-powerpoint"]');
      const download = await downloadPromise;
      
      // Verify download
      expect(download.suggestedFilename()).toContain('.pptx');
    });
  });

  test('file upload functionality', async ({ page }) => {
    await test.step('Upload research documents', async () => {
      // Navigate to initial input
      await page.waitForSelector('[data-testid="initial-input-form"]');
      
      // Test file upload
      const fileInput = page.locator('[data-testid="file-upload-input"]');
      
      // Create a test file
      const testFile = {
        name: 'research-doc.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('This is a test research document about AI in healthcare. It contains information about machine learning algorithms and diagnostic improvements.')
      };
      
      await fileInput.setInputFiles(testFile);
      
      // Verify file upload
      await expect(page.locator('[data-testid="uploaded-file"]')).toContainText('research-doc.txt');
      
      // Remove file
      await page.click('[data-testid="remove-file-btn"]');
      await expect(page.locator('[data-testid="uploaded-file"]')).not.toBeVisible();
    });
  });

  test('settings and configuration', async ({ page }) => {
    await test.step('Access and modify settings', async () => {
      // Open settings dialog
      await page.click('[data-testid="settings-btn"]');
      await page.waitForSelector('[data-testid="settings-dialog"]');
      
      // Test model configuration
      await page.selectOption('[data-testid="clarifier-model-select"]', 'gemini-2.5-flash');
      await page.selectOption('[data-testid="slide-writer-model-select"]', 'gemini-1.5-pro');
      
      // Test telemetry settings
      await page.check('[data-testid="enable-telemetry-checkbox"]');
      
      // Save settings
      await page.click('[data-testid="save-settings-btn"]');
      
      // Verify settings are saved
      await page.click('[data-testid="settings-btn"]');
      await expect(page.locator('[data-testid="clarifier-model-select"]')).toHaveValue('gemini-2.5-flash');
    });
  });

  test('error handling and recovery', async ({ page }) => {
    await test.step('Handle API errors gracefully', async () => {
      // Mock API failure
      await page.route('**/v1/clarify', route => {
        route.abort('failed');
      });
      
      // Try to start clarification
      await page.fill('[data-testid="presentation-text-input"]', 'Test presentation');
      await page.click('[data-testid="start-clarification-btn"]');
      
      // Verify error state
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="retry-btn"]')).toBeVisible();
      
      // Test retry functionality
      await page.unroute('**/v1/clarify');
      await page.click('[data-testid="retry-btn"]');
      
      // Verify recovery
      await page.waitForSelector('[data-testid="clarification-chat"]', { timeout: 15000 });
    });
  });

  test('responsive design', async ({ page }) => {
    await test.step('Test mobile responsiveness', async () => {
      // Test tablet view
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.reload();
      await page.waitForSelector('[data-testid="app-loaded"]');
      
      // Verify mobile navigation
      if (await page.locator('[data-testid="mobile-menu-btn"]').isVisible()) {
        await page.click('[data-testid="mobile-menu-btn"]');
        await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
      }
      
      // Test mobile view
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();
      await page.waitForSelector('[data-testid="app-loaded"]');
      
      // Verify layout adapts to mobile
      await expect(page.locator('[data-testid="initial-input-form"]')).toBeVisible();
    });
  });
});