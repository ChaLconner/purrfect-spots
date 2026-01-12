/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,vue}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#EAF6F3',       // mint sky background
        surface: 'rgba(255,255,255,0.7)',
        primary: '#7FB7A4',          // sage green
        secondary: '#F6C1B1',        // soft peach
        accent: '#FFD6A5',

        text: {
          primary: '#5A4632',        // brown title
          secondary: '#7D7D7D'
        },

        border: 'rgba(255,255,255,0.5)',

        // Ghibli Theme Colors
        brown: {
          DEFAULT: '#A65D37',
          light: '#C4855C',
          dark: '#8B4D2D',
        },
        sage: {
          DEFAULT: '#95A792',
          light: '#B3C4B0',
          dark: '#6D8B6A',
        },
        terracotta: {
          DEFAULT: '#C97B49',
          light: '#E09A6B',
          dark: '#A85D2E',
        },
        cream: {
          DEFAULT: '#F4EBD0',
          light: '#FAF6EC',
          dark: '#E8DFC4',
        },
      },

      borderRadius: {
        xl: '1.25rem',
        '2xl': '1.75rem',
        card: '1.5rem'
      },

      boxShadow: {
        soft: '0 8px 24px rgba(0,0,0,0.06)',
        card: '0 12px 30px rgba(0,0,0,0.08)'
      },

      backdropBlur: {
        glass: '12px'
      },

      fontFamily: {
        heading: ['"Nunito"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif']
      },

      animation: {
        float: 'float 6s ease-in-out infinite'
      },
      
      keyframes: {
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' }
        }
      }
    }
  },
  plugins: [],
}
