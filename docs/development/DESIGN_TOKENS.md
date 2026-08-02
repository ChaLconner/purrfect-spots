# Design Tokens (Premium Ghibli)

## 🎨 Color Tokens

| Token | Name | Description | Hex / Value |
| :--- | :--- | :--- | :--- |
| `background` | Clean Cream | Background หลัก | `#FAF6EC` |
| `surface` | Pure White | Card / Secondary Surface | `#FFFFFF` |
| `primary` | Deep Brown | Primary Action | `#8B4D2D` |
| `secondary` | Spring Sage | Natural Accent | `#7A9B76` |
| `accent` | Sunset Terracotta| Highlights | `#D67A4F` |
| `text-primary` | Dark Walnut | Main Heading | `#422110` |
| `text-secondary` | Deep Brown | Subheading | `#8B4D2D` |
| `text-muted` | Soft Sepia | Body Content | `#A68B75` |
| `glass-cream`| Glass Cream | Glassmorphism | `rgba(250, 246, 236, 0.8)` |

## 🏗 Layout & Depth Tokens

*   **Corner Radius**:
    *   `md`: `12px`
    *   `lg`: `20px` (Standard Card)
    *   `xl`: `28px` (Large Modal/Overlay)
*   **Shadows**:
    *   `sm`: `0 2px 4px rgba(66, 33, 16, 0.05)`
    *   `md`: `0 4px 12px rgba(66, 33, 16, 0.08)`
    *   `lg`: `0 12px 24px rgba(66, 33, 16, 0.12)`
    *   `xl`: `0 20px 48px rgba(66, 33, 16, 0.15)`
    *   `glass`: `0 8px 32px 0 rgba(139, 77, 45, 0.1)`

## 🧩 Component Tokens

### Premium Card
```html
<div class="
  bg-surface
  rounded-[20px]
  shadow-lg
  p-6
  transition-all
  duration-300
  hover:-translate-y-1
  hover:shadow-xl
">
```

### Glass Container
```html
<div class="
  bg-white/80
  backdrop-blur-md
  rounded-[28px]
  border border-white/20
  shadow-glass
  p-8
">
```

## ✒️ Typography

*   **Heading**: `Quicksand` (Weights: 400, 500, 600, 700)
    *   Style: Friendly, rounded terminals
    *   Usage: `font-heading text-3xl font-bold`
*   **Body**: `Montserrat` (Weights: 400, 500, 600)
    *   Style: Geometric, high readability
    *   Usage: `font-body text-base`
*   **Accent (JP Style)**: `Zen Maru Gothic`
    *   Style: Soft, organic feel
    *   Usage: `font-accent text-sm tracking-wide`

## ✨ Transitions & Animations

*   **Instant**: `0ms`
*   **Fast**: `200ms cubic-bezier(0.4, 0, 0.2, 1)`
*   **Normal**: `300ms cubic-bezier(0.4, 0, 0.2, 1)`
*   **Slow**: `500ms cubic-bezier(0.4, 0, 0.2, 1)`

## Tailwind v4 Theme Bridge

```css
@theme {
  /* Colors - Ghibli Palette (Premium) */
  --color-cream: #faf6ec;
  --color-cream-light: #ffffff;
  --color-cream-dark: #f0e6d2;

  --color-brown: #8b4d2d;
  --color-brown-light: #a65d37;
  --color-brown-dark: #5d321d;

  --color-sage: #7a9b76;
  --color-sage-light: #95b390;
  --color-sage-dark: #5b7858;

  --color-terracotta: #d67a4f;
  --color-terracotta-light: #e59976;
  --color-terracotta-dark: #a65d37;

  /* Semantic Aliases */
  --color-primary: #8b4d2d;
  --color-secondary: #7a9b76;
  --color-accent: #d67a4f;
  --color-background: #faf6ec;
  --color-surface: #ffffff;

  /* Glassmorphism */
  --color-glass-cream: rgba(250, 246, 236, 0.8);
  --color-glass-brown: rgba(139, 77, 45, 0.8);
  --color-glass-sage: rgba(122, 155, 118, 0.8);
  --color-glass-terracotta: rgba(214, 122, 79, 0.8);

  /* Fonts */
  --font-heading: 'Quicksand', sans-serif;
  --font-body: 'Montserrat', sans-serif;
  --font-accent: 'Zen Maru Gothic', sans-serif;

  /* Shadow & Spacing */
  --shadow-premium: 0 12px 24px rgba(66, 33, 16, 0.12);
  --radius-premium: 20px;

  /* 3D Button Color Palette - Sage (Primary) */
  --color-btn-bg: #faf6ec;
  --color-btn-shade-a: #5b7858;
  --color-btn-shade-b: #7a9b76;
  --color-btn-shade-c: #95b390;
  --color-btn-shade-d: #c8dbc5;
  --color-btn-shade-e: #e8f0e6;

  /* 3D Button Accent Palette - Terracotta (CTA) */
  --color-btn-accent-a: #a65d37;
  --color-btn-accent-b: #d67a4f;
  --color-btn-accent-c: #e59976;
  --color-btn-accent-d: #f0c4ae;
  --color-btn-accent-e: #fae8df;

  /* 3D Button Brown Palette (Special) */
  --color-btn-brown-a: #5d321d;
  --color-btn-brown-b: #8b4d2d;
  --color-btn-brown-c: #a65d37;
  --color-btn-brown-d: #d4a88a;
  --color-btn-brown-e: #f5e6db;
}
```

---

## 🎮 3D Push Button System

### Color Palettes

ระบบปุ่ม 3D ใช้ 5 ระดับสี (a-e) สำหรับแต่ละ palette:

| Level | ชื่อ | การใช้งาน |
| :--- | :--- | :--- |
| `shade-a` | Darkest | ขอบ, ข้อความ, เงาหลัก |
| `shade-b` | Dark | เส้นขอบเงา |
| `shade-c` | Medium | พื้นหลัง 3D base |
| `shade-d` | Light | Hover state |
| `shade-e` | Lightest | พื้นหลังปุ่มหลัก |

### 🌿 Sage Palette (Primary - Navigation)

| Token | Hex | Preview |
| :--- | :--- | :--- |
| `--color-btn-shade-a` | `#5b7858` | 🟢 เขียวเข้ม |
| `--color-btn-shade-b` | `#7a9b76` | 🌿 เขียวกลาง |
| `--color-btn-shade-c` | `#95b390` | 🍃 เขียวอ่อน |
| `--color-btn-shade-d` | `#c8dbc5` | 🌱 เขียวอ่อนมาก |
| `--color-btn-shade-e` | `#e8f0e6` | ⬜ เขียวอ่อนสุด |

**ใช้กับ:** Nav links, Brand button, Search, User menu, Hamburger

### 🔶 Terracotta Palette (Accent - CTA)

| Token | Hex | Preview |
| :--- | :--- | :--- |
| `--color-btn-accent-a` | `#a65d37` | 🟠 ส้มเข้ม |
| `--color-btn-accent-b` | `#d67a4f` | 🧡 ส้มกลาง |
| `--color-btn-accent-c` | `#e59976` | 🍑 ส้มอ่อน |
| `--color-btn-accent-d` | `#f0c4ae` | 🍊 ส้มอ่อนมาก |
| `--color-btn-accent-e` | `#fae8df` | ⬜ ส้มอ่อนสุด |

**ใช้กับ:** Login button, Call-to-Action buttons

### 🤎 Brown Palette (Special Elements)

| Token | Hex | Preview |
| :--- | :--- | :--- |
| `--color-btn-brown-a` | `#5d321d` | 🟤 น้ำตาลเข้ม |
| `--color-btn-brown-b` | `#8b4d2d` | 🏠 น้ำตาลกลาง |
| `--color-btn-brown-c` | `#a65d37` | ☕ น้ำตาลอ่อน |
| `--color-btn-brown-d` | `#d4a88a` | 🍞 น้ำตาลอ่อนมาก |
| `--color-btn-brown-e` | `#f5e6db` | ⬜ น้ำตาลอ่อนสุด |

**ใช้กับ:** Special buttons, Premium features

---

### 3D Button CSS Structure

```css
/* Base 3D Button */
.btn-3d {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  outline: none;
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 1em;
  background: var(--color-btn-shade-e);
  color: var(--color-btn-shade-a);
  font-weight: 600;
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

/* 3D Depth Effect (Pseudo-element) */
.btn-3d::before {
  position: absolute;
  content: "";
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-shade-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.5em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.5em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

/* Hover - Button lifts slightly */
.btn-3d:hover {
  background: var(--color-btn-shade-d);
  transform: translate(0, 0.25em);
}

/* Active - Button pressed down */
.btn-3d:active {
  transform: translate(0, 0.5em);
}

.btn-3d:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.1em 0 0 var(--color-btn-shade-b);
}
```

### Usage Examples

```html
<!-- Sage Nav Link -->
<a class="nav-link-3d">Map</a>

<!-- Terracotta Login Button -->
<a class="login-btn-3d">Login</a>

<!-- Mobile Nav Link -->
<a class="mobile-nav-link-3d">Gallery</a>
```

---

## 🔄 Switching Themes

หากต้องการเปลี่ยนธีมปุ่ม 3D ให้แก้ไขค่าใน `theme.css`:

```css
/* เปลี่ยนเป็น Blue Theme */
--color-btn-shade-a: #2563eb;  /* blue-600 */
--color-btn-shade-b: #3b82f6;  /* blue-500 */
--color-btn-shade-c: #60a5fa;  /* blue-400 */
--color-btn-shade-d: #93c5fd;  /* blue-300 */
--color-btn-shade-e: #dbeafe;  /* blue-100 */
```

### Theme Switching Checklist

- [ ] Update `--color-btn-shade-*` variables in `theme.css`
- [ ] Update `--color-btn-accent-*` for CTA buttons
- [ ] Update `--color-btn-brown-*` for special elements (optional)
- [ ] Verify contrast ratios for accessibility
- [ ] Test hover and active states
