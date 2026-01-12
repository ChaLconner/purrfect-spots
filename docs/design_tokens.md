# Design Tokens

## 🎨 Color Tokens

| Token | Name | Description | Hex / Value |
| :--- | :--- | :--- | :--- |
| `background` | Mint / Sky pastel | Background หลัก | `#EAF6F3` |
| `surface` | White glass | Card / Search | `rgba(255,255,255,0.7)` |
| `primary` | Sage green | Accent | `#7FB7A4` |
| `secondary` | Peach / Blush | Highlight | `#F6C1B1` |
| `accent` | - | - | `#FFD6A5` |
| `text-primary` | Soft brown | Heading | `#5A4632` |
| `text-secondary` | Muted gray | Body text | `#7D7D7D` |
| `border` | Transparent white | Card border | `rgba(255,255,255,0.5)` |

## 🏗 Layout Tokens

*   **Card Spacing**: `gap-6`
*   **Page Padding**: `px-10 py-8`
*   **Card Inner Padding**: `p-4`

## 🧩 Component Tokens

### Card (Image Tile)
```html
<div class="
  bg-surface
  backdrop-blur-glass
  rounded-card
  border border-border
  shadow-card
  p-3
  hover:scale-[1.03]
  transition
  duration-300
">
```

### Search Bar
```html
<div class="
  flex items-center gap-2
  bg-surface
  backdrop-blur-glass
  rounded-full
  px-5 py-3
  shadow-soft
">
```

## ✒️ Typography

*   **Heading**: `Nunito` (weight: 600, 700)
    *   Usage: `font-heading text-4xl font-bold`
*   **Body**: `Inter` (weight: 400, 500)
    *   Usage: `font-body text-base`

## ✨ Animations

*   **Float**: `float 6s ease-in-out infinite`
    *   Keyframes: 0%, 100% (0), 50% (-6px)

## Tailwind Config Reference

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        background: '#EAF6F3',
        surface: 'rgba(255,255,255,0.7)',
        primary: '#7FB7A4',
        secondary: '#F6C1B1',
        accent: '#FFD6A5',
        text: {
          primary: '#5A4632',
          secondary: '#7D7D7D'
        },
        border: 'rgba(255,255,255,0.5)',
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
      }
    }
  }
}
```
