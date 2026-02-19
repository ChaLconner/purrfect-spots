<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  variant?: 'glass' | 'white' | 'flat' | 'image';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}>();

const baseClasses = 'transition-all duration-300 rounded-3xl overflow-hidden';

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'glass':
      return 'backdrop-blur-md bg-white/70 border border-white/50 shadow-card';
    case 'white':
      return 'bg-white shadow-lg border border-stone-100';
    case 'image':
      return 'bg-white/40 backdrop-blur-xl border border-white/60 shadow-sm transition-all duration-500 ease-out';
    case 'flat':
      return 'bg-cream-light border border-cream-dark/50';
    default:
      return 'backdrop-blur-md bg-white/70 border border-white/50 shadow-card';
  }
});

const paddingClasses = computed(() => {
  switch (props.padding) {
    case 'none':
      return 'p-0';
    case 'sm':
      return 'p-3';
    case 'lg':
      return 'p-8';
    default:
      return 'p-5'; // md default
  }
});

const hoverClasses = computed(() => {
  if (!props.hover) return '';
  switch (props.variant) {
    case 'image':
      return 'hover:scale-[1.02] hover:shadow-lg hover:bg-white/50 hover:border-white/80 cursor-pointer';
    default:
      return 'hover:scale-[1.02] hover:shadow-xl cursor-pointer';
  }
});

const classes = computed(() => {
  return [baseClasses, variantClasses.value, paddingClasses.value, hoverClasses.value].join(' ');
});
</script>

<template>
  <div :class="classes">
    <slot></slot>
  </div>
</template>
