import { test, expect } from '@playwright/test';

const API_BASE_URL = process.env.WORKFLOW_API_BASE_URL || 'http://localhost:18088';

function ok(response) {
  expect(response.ok(), `Unexpected status ${response.status()} - ${response.statusText()}`).toBeTruthy();
}

test.describe('Workflow API smoke tests', () => {
  test('design refresh workflow responds', async ({ request }) => {
    const payload = {
      presentationId: 'playwright-design-refresh',
      initialInput: {
        text: 'Refresh visuals for our quarterly AI roadmap deck',
        audience: 'executive',
        tone: 'confident',
        length: 'medium',
        theme: 'modern'
      },
      slides: [
        {
          id: 'slide-1',
          title: 'Roadmap Overview',
          content: ['AI upgrades', 'Customer impact'],
          speakerNotes: 'Explain roadmap at high level'
        }
      ],
      newFiles: []
    };

    const response = await request.post(`${API_BASE_URL}/v1/workflow/design-refresh`, { data: payload });
    ok(response);
    const body = await response.json();
    expect(body).toHaveProperty('state');
    expect(body).toHaveProperty('trace');
  });

  test('evidence sweep workflow responds', async ({ request }) => {
    const payload = {
      presentationId: 'playwright-evidence',
      slides: [
        {
          id: 'slide-1',
          title: 'AI Impact',
          content: ['Usage stats', 'ROI improvements'],
          speakerNotes: 'Highlight metrics',
          citations: []
        }
      ],
      newFiles: []
    };

    const response = await request.post(`${API_BASE_URL}/v1/workflow/evidence-sweep`, { data: payload });
    ok(response);
  });

  test('research prep workflow responds', async ({ request }) => {
    const payload = {
      presentationId: 'playwright-research',
      history: [],
      initialInput: {
        text: 'Summarize AI trends for healthcare',
        audience: 'product',
        tone: 'insightful'
      },
      newFiles: []
    };

    const response = await request.post(`${API_BASE_URL}/v1/workflow/research-prep`, { data: payload });
    ok(response);
  });
});
