/**
 * Ghibli Theme - Typography
 * Friendly, readable fonts inspired by Studio Ghibli aesthetic
 */

export const typography = {
  fonts: {
    heading: ['Quicksand', 'sans-serif'],
    body: ['Montserrat', 'sans-serif'],
    accent: ['Zen Maru Gothic', 'sans-serif'],
  },

  weights: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },

  sizes: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
  },

  lineHeight: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },

  letterSpacing: {
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
  },
} as const;

// Google Fonts URL for import
export const googleFontsUrl = 
  'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&family=Quicksand:wght@400;500;600;700&display=swap';

// Tailwind-compatible font family object
export const tailwindFontFamily = {
  heading: typography.fonts.heading,
  body: typography.fonts.body,
  accent: typography.fonts.accent,
  'zen-maru': typography.fonts.accent, // Keep backward compatibility
} as const;

export type FontFamily = keyof typeof typography.fonts;
export type FontWeight = keyof typeof typography.weights;
