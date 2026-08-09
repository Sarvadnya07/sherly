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
        background: '#09090d',
        panel: '#0e0e15',
        card: '#13131e',
        sidebar: '#0b0b11',
        input: '#161624',
        purple: {
          main: '#8b5cf6',
          dark: '#6d28d9',
          glow: 'rgba(139, 92, 246, 0.25)',
        },
        cyan: {
          accent: '#00f0ff',
        },
        emerald: {
          success: '#10b981',
        },
      },
    },
  },
  plugins: [],
};
