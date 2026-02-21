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

// Map variants to CSS custom properties using Tailwind arbitrary values
const variantStyle = computed(() => {
  switch (props.variant) {
    case 'sky':
      return {
        '--btn-a': 'var(--color-btn-sky-a)',
        '--btn-b': 'var(--color-btn-sky-b)',
        '--btn-c': 'var(--color-btn-sky-c)',
        '--btn-d': 'var(--color-btn-sky-d)',
        '--btn-e': 'var(--color-btn-sky-e)',
      };
    case 'lavender':
      return {
        '--btn-a': 'var(--color-btn-lavender-a)',
        '--btn-b': 'var(--color-btn-lavender-b)',
        '--btn-c': 'var(--color-btn-lavender-c)',
        '--btn-d': 'var(--color-btn-lavender-d)',
        '--btn-e': 'var(--color-btn-lavender-e)',
      };
    case 'sakura':
      return {
        '--btn-a': 'var(--color-btn-sakura-a)',
        '--btn-b': 'var(--color-btn-sakura-b)',
        '--btn-c': 'var(--color-btn-sakura-c)',
        '--btn-d': 'var(--color-btn-sakura-d)',
        '--btn-e': 'var(--color-btn-sakura-e)',
      };
    case 'accent':
      return {
        '--btn-a': 'var(--color-btn-accent-a)',
        '--btn-b': 'var(--color-btn-accent-b)',
        '--btn-c': 'var(--color-btn-accent-c)',
        '--btn-d': 'var(--color-btn-accent-d)',
        '--btn-e': 'var(--color-btn-accent-e)',
        'text-transform': 'uppercase',
      };
    case 'sage':
    default:
      return {
        '--btn-a': 'var(--color-btn-shade-a)',
        '--btn-b': 'var(--color-btn-shade-b)',
        '--btn-c': 'var(--color-btn-shade-c)',
        '--btn-d': 'var(--color-btn-shade-d)',
        '--btn-e': 'var(--color-btn-shade-e)',
      };
  }
});
</script>

<template>
  <RouterLink
    :to="to"
    class="group relative inline-flex items-center gap-2 cursor-pointer outline-none no-underline text-[0.85rem] font-semibold font-accent px-3 py-2 rounded-xl transition-all duration-[150ms] ease-out bg-[var(--btn-e)] text-[var(--btn-a)] border-2 border-[var(--btn-a)] hover:bg-[var(--btn-d)] hover:translate-y-[0.1em] active:translate-y-[0.25rem] [&.active]:bg-[var(--btn-d)] [&.active]:font-bold [&:hover_svg]:-rotate-8 [&:hover_svg]:scale-110 [&:hover_svg]:transition-transform [&:hover_svg]:duration-200"
    :style="[variantStyle, { 'transform-style': 'preserve-3d', 'will-change': 'transform' }]"
    active-class="active"
  >
    <span
      class="absolute inset-0 bg-[var(--btn-c)] rounded-[inherit] shadow-[0_0_0_2px_var(--btn-b),_0_0.25rem_0_0_var(--btn-a)] transition-all duration-[150ms] ease-out -z-10 group-hover:translate-y-[0.15rem] group-active:translate-y-0 group-active:translate-z-[-1em] group-active:shadow-[0_0_0_2px_var(--btn-b),_0_0.1em_0_0_var(--btn-b)]"
      style="transform: translate3d(0, 0.25rem, -1em); will-change: transform"
    ></span>
    <slot name="icon"></slot>
    <span v-if="label" class="hidden xl:block">{{ label }}</span>
    <slot></slot>
  </RouterLink>
</template>
