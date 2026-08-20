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
        canvas: '#09090b',
        sidebar: '#0d0d11',
        surface: '#09090b',
        card: {
          DEFAULT: '#141418',
          hover: '#1a1a22',
        },
        input: '#121216',
        brand: {
          DEFAULT: '#6366f1',
          hover: '#4f46e5',
          surface: 'rgba(99, 102, 241, 0.08)',
          border: 'rgba(99, 102, 241, 0.25)',
        },
        status: {
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          info: '#38bdf8',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Inter', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.4)',
        'elevated': '0 8px 24px -4px rgba(0, 0, 0, 0.6), 0 2px 6px -2px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
};
