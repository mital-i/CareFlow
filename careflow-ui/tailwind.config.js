/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a5f',
        },
        danger: '#ef4444',
        warning: '#f59e0b',
        success: '#22c55e',
      },
      animation: {
        'flash-red': 'flashRed 0.5s ease-in-out 3',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        flashRed: {
          '0%, 100%': { backgroundColor: 'transparent' },
          '50%': { backgroundColor: 'rgba(239, 68, 68, 0.25)' },
        },
      },
    },
  },
  plugins: [],
}
