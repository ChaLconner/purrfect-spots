/**
 * Ghibli Theme - Color Palette
 * Studio Ghibli-inspired colors with warm, earthy tones
 */

export const colors = {
  // Primary palette (Premium Ghibli)
  cream: {
    DEFAULT: '#FAF6EC',
    light: '#FFFFFF',
    dark: '#F0E6D2',
    glass: 'rgba(250, 246, 236, 0.8)',
  },
  brown: {
    DEFAULT: '#8B4D2D',
    light: '#A65D37',
    dark: '#5D321D',
    glass: 'rgba(139, 77, 45, 0.8)',
  },
  sage: {
    DEFAULT: '#7A9B76',
    light: '#95B390',
    dark: '#5B7858',
    glass: 'rgba(122, 155, 118, 0.8)',
  },
  terracotta: {
    DEFAULT: '#D67A4F',
    light: '#E59976',
    dark: '#A65D37',
    glass: 'rgba(214, 122, 79, 0.8)',
  },

  // Semantic aliases
  semantic: {
    primary: '#8B4D2D', // Deep Brown
    secondary: '#7A9B76', // Spring Sage
    accent: '#D67A4F', // Sunset Terracotta
    background: '#FAF6EC', // Clean Cream
    surface: '#FFFFFF',
    text: {
      primary: '#422110', // Very dark brown for accessibility
      secondary: '#8B4D2D',
      muted: '#A68B75',
    },
    success: '#5B7858',
    warning: '#D67A4F',
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
