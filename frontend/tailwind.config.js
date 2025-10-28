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
      keyframes: {
        fadeIn: {
          '0%': {
            opacity: '0',
            transform: 'scale(0.9)',
          },
          '100%': {
            opacity: '1',
            transform: 'scale(1)',
          },
        },
        slideDown: {
          '0%': {
            opacity: '0',
            transform: 'translateY(-10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        bounceIn: {
          '0%': {
            opacity: '0',
            transform: 'scale(0.3)',
          },
          '50%': {
            opacity: '1',
            transform: 'scale(1.05)',
          },
          '70%': {
            transform: 'scale(0.9)',
          },
          '100%': {
            transform: 'scale(1)',
          },
        },
        logoFloat: {
          '0%': {
            transform: 'translateY(0px) rotate(0deg)',
          },
          '25%': {
            transform: 'translateY(-5px) rotate(-5deg)',
          },
          '50%': {
            transform: 'translateY(0px) rotate(0deg)',
          },
          '75%': {
            transform: 'translateY(-5px) rotate(5deg)',
          },
          '100%': {
            transform: 'translateY(0px) rotate(0deg)',
          },
        },
        logoGlow: {
          '0%, 100%': {
            filter: 'drop-shadow(0 0 5px rgba(168, 218, 220, 0.5))',
          },
          '50%': {
            filter: 'drop-shadow(0 0 15px rgba(168, 218, 220, 0.8))',
          },
        },
      },
      animation: {
        'bounce-in': 'bounceIn 1s',
        'logo-float': 'logoFloat 3s ease-in-out infinite',
        'logo-glow': 'logoGlow 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
