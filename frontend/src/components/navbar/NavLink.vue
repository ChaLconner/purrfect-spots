<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';

// Define props
const props = withDefaults(
  defineProps<{
    to: string;
    variant?: 'sage' | 'sky' | 'lavender' | 'sakura' | 'accent';
    label?: string; // Optional label if not using slot
  }>(),
  {
    variant: 'sage',
  }
);

// Map variants to CSS classes that define the color variables
const variantClass = computed(() => `variant-${props.variant}`);
</script>

<template>
  <RouterLink :to="to" class="nav-link-3d" :class="variantClass" active-class="active">
    <slot name="icon"></slot>
    <span v-if="label" class="hidden xl:block">{{ label }}</span>
    <slot></slot>
  </RouterLink>
</template>

<style scoped>
/* Base Variables & Overrides by Variant */
.nav-link-3d {
  --btn-a: var(--color-btn-shade-a);
  --btn-b: var(--color-btn-shade-b);
  --btn-c: var(--color-btn-shade-c);
  --btn-d: var(--color-btn-shade-d);
  --btn-e: var(--color-btn-shade-e);
}

.variant-sky {
  --btn-a: var(--color-btn-sky-a);
  --btn-b: var(--color-btn-sky-b);
  --btn-c: var(--color-btn-sky-c);
  --btn-d: var(--color-btn-sky-d);
  --btn-e: var(--color-btn-sky-e);
}

.variant-lavender {
  --btn-a: var(--color-btn-lavender-a);
  --btn-b: var(--color-btn-lavender-b);
  --btn-c: var(--color-btn-lavender-c);
  --btn-d: var(--color-btn-lavender-d);
  --btn-e: var(--color-btn-lavender-e);
}

.variant-sakura {
  --btn-a: var(--color-btn-sakura-a);
  --btn-b: var(--color-btn-sakura-b);
  --btn-c: var(--color-btn-sakura-c);
  --btn-d: var(--color-btn-sakura-d);
  --btn-e: var(--color-btn-sakura-e);
}

.variant-accent {
  --btn-a: var(--color-btn-accent-a);
  --btn-b: var(--color-btn-accent-b);
  --btn-c: var(--color-btn-accent-c);
  --btn-d: var(--color-btn-accent-d);
  --btn-e: var(--color-btn-accent-e);
  text-transform: uppercase; /* Accent usually for Login */
}

/* 3D Link Styles */
.nav-link-3d {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  outline: none;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  font-family: 'Zen Maru Gothic', sans-serif;
  padding: 0.5rem 0.75rem;
  border-radius: 0.75em;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
  transform-style: preserve-3d;

  /* Usage of mapped variables */
  color: var(--btn-a);
  border: 2px solid var(--btn-a);
  background: var(--btn-e);
}

.nav-link-3d::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--btn-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--btn-b),
    0 0.4em 0 0 var(--btn-a);
  transform: translate3d(0, 0.4em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
  z-index: -1;
}

/* Hover State */
.nav-link-3d:hover {
  background: var(--btn-d);
  transform: translate(0, 0.2em);
}

.nav-link-3d:hover::before {
  transform: translate3d(0, 0.4em, -1em);
}

/* Active/Pressed State */
.nav-link-3d:active {
  transform: translate(0em, 0.4em);
}

.nav-link-3d:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--btn-b),
    0 0.1em 0 0 var(--btn-b);
}

/* Router Active State */
.nav-link-3d.active {
  background: var(--btn-d);
  font-weight: 700;
}

/* Icon Animation on Hover */
.nav-link-3d:hover :deep(svg),
.nav-link-3d:hover :deep(.nav-icon) {
  transform: rotate(-8deg) scale(1.1);
  transition: transform 0.2s ease;
}
</style>
