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

type NavVariant = NonNullable<typeof props.variant>;

const variantClasses: Record<NavVariant, { link: string; layer: string }> = {
  sage: {
    link: 'bg-btn-shade-e text-btn-shade-a border-btn-shade-a hover:bg-btn-shade-d',
    layer:
      'bg-btn-shade-c shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.25rem_0_0_var(--color-btn-shade-a)] group-active:shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.1em_0_0_var(--color-btn-shade-b)]',
  },
  sky: {
    link: 'bg-btn-sky-e text-btn-sky-a border-btn-sky-a hover:bg-btn-sky-d',
    layer:
      'bg-btn-sky-c shadow-[0_0_0_2px_var(--color-btn-sky-b),_0_0.25rem_0_0_var(--color-btn-sky-a)] group-active:shadow-[0_0_0_2px_var(--color-btn-sky-b),_0_0.1em_0_0_var(--color-btn-sky-b)]',
  },
  lavender: {
    link: 'bg-btn-lavender-e text-btn-lavender-a border-btn-lavender-a hover:bg-btn-lavender-d',
    layer:
      'bg-btn-lavender-c shadow-[0_0_0_2px_var(--color-btn-lavender-b),_0_0.25rem_0_0_var(--color-btn-lavender-a)] group-active:shadow-[0_0_0_2px_var(--color-btn-lavender-b),_0_0.1em_0_0_var(--color-btn-lavender-b)]',
  },
  sakura: {
    link: 'bg-btn-sakura-e text-btn-sakura-a border-btn-sakura-a hover:bg-btn-sakura-d',
    layer:
      'bg-btn-sakura-c shadow-[0_0_0_2px_var(--color-btn-sakura-b),_0_0.25rem_0_0_var(--color-btn-sakura-a)] group-active:shadow-[0_0_0_2px_var(--color-btn-sakura-b),_0_0.1em_0_0_var(--color-btn-sakura-b)]',
  },
  accent: {
    link: 'bg-btn-accent-e text-btn-accent-a border-btn-accent-a hover:bg-btn-accent-d uppercase',
    layer:
      'bg-btn-accent-c shadow-[0_0_0_2px_var(--color-btn-accent-b),_0_0.25rem_0_0_var(--color-btn-accent-a)] group-active:shadow-[0_0_0_2px_var(--color-btn-accent-b),_0_0.1em_0_0_var(--color-btn-accent-b)]',
  },
};

const activeVariantClasses = computed(() => variantClasses[props.variant]);
</script>

<template>
  <RouterLink
    :to="to"
    :class="[
      'group relative inline-flex items-center gap-2 cursor-pointer outline-none no-underline text-[0.85rem] font-semibold font-accent px-3 py-2 rounded-xl transition-all duration-[150ms] ease-out border-2 hover:translate-y-[0.1em] active:translate-y-[0.25rem] [&.active]:font-bold [&:hover_svg]:-rotate-8 [&:hover_svg]:scale-110 [&:hover_svg]:transition-transform [&:hover_svg]:duration-200 preserve-3d will-change-transform',
      activeVariantClasses.link,
    ]"
    active-class="active"
  >
    <span
      :class="[
        'absolute inset-0 rounded-[inherit] transition-all duration-[150ms] ease-out -z-10 group-hover:translate-y-[0.15rem] group-active:translate-y-0 group-active:translate-z-[-1em] translate-3d-button',
        activeVariantClasses.layer,
      ]"
    ></span>
    <slot name="icon"></slot>
    <span v-if="label" class="hidden xl:block">{{ label }}</span>
    <slot></slot>
  </RouterLink>
</template>
