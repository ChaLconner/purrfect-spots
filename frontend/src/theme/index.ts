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
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    full: '9999px',
  },

  shadows: {
    sm: '0 2px 8px rgba(166, 93, 55, 0.08)',
    md: '0 4px 16px rgba(166, 93, 55, 0.12)',
    lg: '0 8px 32px rgba(166, 93, 55, 0.16)',
    glow: '0 0 20px rgba(201, 123, 73, 0.3)',
  },

  transitions: {
    fast: '150ms ease',
    normal: '300ms ease',
    slow: '500ms ease',
  },
} as const;

export type GhibliTheme = typeof ghibliTheme;
