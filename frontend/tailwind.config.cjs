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
        canvas: '#090a0f',
        sidebar: '#0e0f16',
        surface: '#12131c',
        card: {
          DEFAULT: '#171824',
          hover: '#1d1e2e',
        },
        input: '#11121b',
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
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'Cascadia Code', 'Consolas', 'Courier New', 'monospace'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.25)',
        'elevated': '0 4px 12px 0 rgba(0, 0, 0, 0.35)',
      },
    },
  },
  plugins: [],
};
