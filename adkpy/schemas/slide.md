# Slide Schema (No Code)

Fields
- title: string (3–6 words, concrete)
- content: string[] (2–4 bullets, <= 12 words each)
- speakerNotes: string (short paragraph + 3–5 bullets)
- imagePrompt: string (descriptive, no text/logos)
- citations?: string[] (e.g., ["report.pdf"]) 
- designCode?: { css?: string; svg?: string }

Constraints
- Bullet words and counts enforced by CriticAgent.
- Citations must correspond to uploaded assets.

