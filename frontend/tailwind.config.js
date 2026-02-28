/** @type {import('tailwindcss').Config} */

// ─────────────────────────────────────────────────────────────────────────────
// VORTEX Golden Ratio Typography Scale  (φ = 1.618)
// Base: 10px  →  each step × φ
//
//  Step │ Class  │  Size   │  Usage
// ──────┼────────┼─────────┼──────────────────────────────────────────────────
//   -1  │ 2xs    │  6.18px │  micro labels, legal text
//    0  │ xs     │ 10.00px │  captions, badges, timestamps
//   +1  │ sm     │ 16.18px │  body text, table cells, descriptions
//   +2  │ base   │ 26.18px │  card values, subheadings
//   +3  │ lg     │ 42.34px │  section headings
//   +4  │ xl     │ 68.51px │  page titles
//   +5  │ 2xl    │110.81px │  hero / display numbers
// ─────────────────────────────────────────────────────────────────────────────

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'vortex-dark': '#0d1117',
        'vortex-darker': '#010409',
        'vortex-accent': '#1f6feb',
        'vortex-accent-hover': '#388bfd',
        'risk-critical': '#fb2c36',
        'risk-high': '#ff6900',
        'risk-medium': '#f0b100',
        'risk-low': '#00c950',
        'github-border': '#30363d',
        'github-text': '#c9d1d9',
      },
      fontSize: {
        // ── Standard Normalized Scale (Fixes 'Blown Up' UI) ──────────────────
        '2xs': ['0.625rem', { lineHeight: '0.75rem' }], // 10px
        'xs': ['0.75rem', { lineHeight: '1rem' }],      // 12px
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],   // 14px
        'base': ['1rem', { lineHeight: '1.5rem' }],      // 16px
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],   // 18px
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],    // 20px
        '2xl': ['1.5rem', { lineHeight: '2rem' }],       // 24px
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],  // 30px
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],    // 36px

        // ── VORTEX Golden Ratio Scale (φ=1.618, base=10px) ──────────────────
        'vortex-xs': ['10px', { lineHeight: '16px', letterSpacing: '0.02em' }],
        'vortex-sm': ['16.18px', { lineHeight: '24px', letterSpacing: '0.01em' }],
        'vortex-base': ['26.18px', { lineHeight: '36px', letterSpacing: '0em' }],
        'vortex-lg': ['42.34px', { lineHeight: '52px', letterSpacing: '-0.01em' }],
        'vortex-xl': ['68.51px', { lineHeight: '78px', letterSpacing: '-0.02em' }],
        'vortex-2xl': ['110.81px', { lineHeight: '120px', letterSpacing: '-0.03em' }],
      },
    },
  },
  plugins: [],
}
