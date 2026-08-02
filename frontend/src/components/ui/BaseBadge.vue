<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'outline';
    size?: 'sm' | 'md' | 'lg';
  }>(),
  {
    variant: 'primary',
    size: 'md',
  }
);
</script>

<template>
  <span
    class="inline-flex items-center justify-center font-medium rounded-full transition-colors"
    :class="[
      {
        'bg-brown text-cream': variant === 'primary',
        'bg-sage text-white': variant === 'secondary',
        'bg-terracotta text-white': variant === 'accent',
        'bg-sage-dark text-white': variant === 'success',
        'bg-amber-500 text-white': variant === 'warning',
        'bg-red-500 text-white': variant === 'error',
        'border border-brown/30 text-brown-text bg-cream/50': variant === 'outline',
      },
      {
        'px-2 py-0.5 text-xs': size === 'sm',
        'px-3 py-1 text-xs sm:text-sm': size === 'md',
        'px-4 py-1.5 text-sm sm:text-base': size === 'lg',
      },
    ]"
  >
    <slot></slot>
  </span>
</template>
