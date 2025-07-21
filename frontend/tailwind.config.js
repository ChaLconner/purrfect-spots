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
    },
  },
  plugins: [],
}
