/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#08080c',
        sidebar: '#0c0c12',
        surface: '#101018',
        card: {
          DEFAULT: '#151520',
          hover: '#1a1a28',
        },
        input: '#12121c',
        brand: {
          DEFAULT: '#7c3aed',
          hover: '#8b5cf6',
          surface: 'rgba(124, 58, 237, 0.12)',
          glow: 'rgba(124, 58, 237, 0.20)',
          border: 'rgba(124, 58, 237, 0.35)',
        },
        status: {
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#f43f5e',
          info: '#38bdf8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'Cascadia Code', 'Consolas', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
};

