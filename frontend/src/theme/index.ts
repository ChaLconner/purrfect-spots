/**
 * Ghibli Theme - Main Export
 * Central export point for all theme configurations
 */

export { colors, tailwindColors, type GhibliColor, type SemanticColor } from './colors';
export {
  typography,
  tailwindFontFamily,
  googleFontsUrl,
  type FontFamily,
  type FontWeight,
} from './typography';

// Theme configuration object for programmatic use
export const ghibliTheme = {
  name: 'ghibli',

  // Design tokens
  spacing: {
    unit: 8,
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    '2xl': 48,
  },

  borderRadius: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '20px',
    xl: '28px',
    '2xl': '36px',
    full: '9999px',
  },

  shadows: {
    sm: '0 2px 4px rgba(66, 33, 16, 0.05)',
    md: '0 4px 12px rgba(66, 33, 16, 0.08)',
    lg: '0 12px 24px rgba(66, 33, 16, 0.12)',
    xl: '0 20px 48px rgba(66, 33, 16, 0.15)',
    glow: '0 0 20px rgba(214, 122, 79, 0.3)',
    glass: '0 8px 32px 0 rgba(139, 77, 45, 0.1)',
  },

  transitions: {
    instant: '0ms',
    fast: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
    normal: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '500ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
} as const;

export type GhibliTheme = typeof ghibliTheme;
