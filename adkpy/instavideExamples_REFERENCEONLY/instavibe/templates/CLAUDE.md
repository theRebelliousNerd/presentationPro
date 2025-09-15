# 🚨 INSTAVIBE HTML TEMPLATES - DO NOT USE 🚨

## ⛔ THESE ARE FLASK/JINJA2 TEMPLATES ⛔

### COMPLETELY WRONG TECHNOLOGY STACK

This directory contains **InstaVibe's Flask HTML templates**:
- Jinja2 template syntax (NOT JSX/React)
- Server-side rendering (NOT Next.js SSR/SSG)
- Event planning UI (NOT presentation creation)
- Flask macros (NOT React components)

### ⚠️ FUNDAMENTAL DIFFERENCES ⚠️

| InstaVibe Templates (Here) | PresentationPro UI |
|---------------------------|-------------------|
| HTML with Jinja2 | React JSX/TSX |
| `{{ variable }}` syntax | `{variable}` JSX |
| Flask template inheritance | React component composition |
| Server-side only | Client + Server (Next.js) |
| Event planning pages | Presentation editor |

### Template Files:

- `index.html` - InstaVibe home (NOT PresentationPro)
- `event_detail.html` - Event pages (we do presentations)
- `introvert_ally*.html` - Social features (not relevant)
- `base.html` - Flask layout (we use React layouts)
- `_macros.html` - Jinja2 macros (we use React components)

### ❌ ABSOLUTELY DO NOT:

- Copy any HTML structure - Use React components
- Use Jinja2 syntax - Use JSX
- Reference template patterns - Different rendering model
- Copy any UI layouts - Different application purpose

### ✅ REAL PRESENTATIONPRO UI:

```
/src/app/page.tsx              ← Real main page
/src/components/app/           ← Real UI components
/src/app/presentations/        ← Real presentation pages
```

### Why These Are Incompatible:

1. **Different Template Engine**: Jinja2 vs JSX
2. **Different Rendering**: Flask SSR vs Next.js hybrid
3. **Different Purpose**: Events vs Presentations
4. **Different State**: Server sessions vs React state

---

**THESE ARE HTML TEMPLATES FOR A FLASK APP!**
**PresentationPro uses React/Next.js - COMPLETELY DIFFERENT!**