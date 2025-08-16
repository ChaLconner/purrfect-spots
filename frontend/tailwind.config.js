/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,vue}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'zen-maru': ['Zen Maru Gothic', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-pastel': 'linear-gradient(160deg, rgba(168, 218, 220, 0.7) 0%, rgba(183, 228, 199, 0.7) 30%, rgba(253, 229, 200, 0.7) 65%, rgba(246, 166, 161, 0.7) 100%)',
      },
      backdropFilter: {
        'blur-glass': 'blur(20px)',
      },
    },
  },
  plugins: [],
}
