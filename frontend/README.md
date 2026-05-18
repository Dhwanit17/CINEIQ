# CINEIQ — React Port

A Vite + React port of the original single-file `index.html` for CINEIQ.

## Run it

```bash
npm install
npm run dev
```

Then open the URL Vite prints (typically http://localhost:5173).

To build for production:

```bash
npm run build
npm run preview
```

## Project structure

```
cineiq-react/
├── index.html               # Vite entry HTML, loads /src/main.jsx + Google Fonts
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx             # React mount + CSS imports
    ├── App.jsx              # Top-level component composition
    │
    ├── components/          # One file per section
    │   ├── Nav.jsx
    │   ├── Hero.jsx
    │   ├── Ticker.jsx       # Used inside Hero
    │   ├── Problem.jsx
    │   ├── Features.jsx
    │   ├── Demo.jsx
    │   ├── Stack.jsx
    │   ├── Datasets.jsx
    │   ├── Architecture.jsx
    │   └── Footer.jsx
    │
    ├── hooks/
    │   ├── useScrollNav.js     # Tracks scroll for nav background + active link
    │   └── useScrollReveal.js  # IntersectionObserver-based fade-in
    │
    ├── data/                # Content extracted from the original page
    │   ├── demoData.js      # Movies + recommendations for the live demo
    │   ├── tickerData.js    # Marquee items in the hero
    │   ├── features.js
    │   ├── stack.js
    │   └── datasets.js
    │
    └── styles/              # One file per visual concern
        ├── index.css        # Design tokens, reset, body overlays, shared helpers
        ├── nav.css
        ├── hero.css
        ├── problem.css
        ├── features.css
        ├── demo.css
        ├── stack.css
        ├── datasets.css
        ├── architecture.css
        └── footer.css
```

## Notes on the conversion

- **CSS variables / tokens** are unchanged. All visual design lives in `src/styles/`.
- **Fonts** are loaded from `index.html` (same Google Fonts URL as the original).
- **DOM manipulation → React state**:
  - The nav scroll listener that toggled `.scrolled` and the active link became `useScrollNav`.
  - The IntersectionObserver-based reveal animation became `useScrollReveal`.
  - The ticker, dust particles, demo data, and clock are all driven by component state.
- **The demo terminal** is now fully controlled: typing + Enter, or clicking a chip,
  updates React state and re-renders. Recommendation `reason` text contains inline
  `<span class="hl">…</span>` markup, so it's rendered via `dangerouslySetInnerHTML`.
  That's safe here because the strings are static and authored, not user input.
- **SVG diagrams** were translated to JSX (attribute names like `stroke-width` →
  `strokeWidth`, `text-anchor` → `textAnchor`, etc.). The architecture pipeline nodes
  are defined as a data array and mapped, which makes future tweaks much easier.
