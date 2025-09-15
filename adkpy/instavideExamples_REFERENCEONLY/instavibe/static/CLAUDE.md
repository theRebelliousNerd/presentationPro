# 🚨 INSTAVIBE STATIC FILES - DO NOT USE 🚨

## ⛔ THESE ARE FLASK STATIC ASSETS ⛔

### WRONG FRAMEWORK - WRONG APPLICATION

This directory contains **InstaVibe's Flask static files**:
- Flask-specific CSS (NOT Next.js styles)
- InstaVibe JavaScript (NOT React components)
- Event planning images (NOT presentation assets)

### ⚠️ CRITICAL DIFFERENCES ⚠️

| InstaVibe Static (Here) | PresentationPro Assets |
|------------------------|------------------------|
| Flask static serving | Next.js public folder |
| Plain CSS files | Tailwind CSS + CSS Modules |
| Vanilla JavaScript | React/TypeScript |
| Event images | Presentation backgrounds |

### Files/Folders:

- `css/style.css` - InstaVibe styles (NOT for PresentationPro)
- `js/main.js` - InstaVibe vanilla JS (NOT React)
- `*.png`, `*.gif` - InstaVibe images (wrong branding)

### ❌ DO NOT:

- Copy any CSS - PresentationPro uses Tailwind
- Use the JavaScript - PresentationPro uses React/TypeScript
- Take any images - Wrong branding/purpose
- Reference these paths - Different asset structure

### ✅ REAL PRESENTATIONPRO ASSETS:

```
/public/               ← Real static assets
/src/app/globals.css  ← Real global styles
/src/components/      ← Real React components with styles
```

---

**THESE ARE INSTAVIBE'S ASSETS - NOT PRESENTATIONPRO'S!**