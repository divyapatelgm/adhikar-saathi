/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        saathi: {
          primary: '#15803d',     // Accessible forest green
          dark: '#14532d',
          light: '#dcfce7',
          accent: '#b45309',    // High-contrast warm amber
          accentLight: '#fef3c7',
          surface: '#f8fafc',
          card: '#ffffff',
          text: '#0f172a',
          textMuted: '#475569',
        }
      },
      fontSize: {
        'touch': '1.125rem', // 18px readable baseline
      }
    },
  },
  plugins: [],
}
