/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#1e3a5f', light: '#2d5282' },
        risk: { low: '#22c55e', medium: '#eab308', high: '#f97316', critical: '#ef4444' },
      },
    },
  },
  plugins: [],
}
