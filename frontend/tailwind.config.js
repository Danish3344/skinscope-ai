/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#16302b',
        sage: '#2f7d6d',
        mint: '#e9f6f2',
        coral: '#f27668',
      },
      fontFamily: { sans: ['Inter', 'Segoe UI', 'sans-serif'] },
    },
  },
  plugins: [],
}

