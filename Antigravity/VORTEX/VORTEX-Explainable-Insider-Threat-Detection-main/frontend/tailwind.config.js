/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'vortex-dark': '#0a0e27',
        'vortex-darker': '#060914',
        'vortex-accent': '#4f46e5',
        'vortex-accent-hover': '#4338ca',
        'risk-critical': '#ef4444',
        'risk-high': '#f59e0b',
        'risk-medium': '#fbbf24',
        'risk-low': '#10b981',
      },
    },
  },
  plugins: [],
}
