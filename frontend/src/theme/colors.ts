/**
 * Ghibli Theme - Color Palette
 * Studio Ghibli-inspired colors with warm, earthy tones
 */

export const colors = {
  // Primary palette
  cream: {
    DEFAULT: '#F4EBD0',
    light: '#FAF6EC',
    dark: '#E8DFC4',
  },
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

  // Semantic aliases (for easy theming)
  semantic: {
    primary: '#A65D37', // brown
    secondary: '#95A792', // sage
    accent: '#C97B49', // terracotta
    background: '#F4EBD0', // cream
    surface: '#FAF6EC', // cream-light
    text: {
      primary: '#A65D37',
      secondary: '#C4855C',
      muted: '#8B7355',
    },
    success: '#6D8B6A', // sage-dark
    warning: '#C97B49', // terracotta
    error: '#C75B5B',
  },
} as const;

// Tailwind-compatible color object
export const tailwindColors = {
  cream: colors.cream,
  brown: colors.brown,
  sage: colors.sage,
  terracotta: colors.terracotta,
} as const;

export type GhibliColor = keyof typeof colors;
export type SemanticColor = keyof typeof colors.semantic;
