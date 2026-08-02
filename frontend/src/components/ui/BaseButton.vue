<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';
import BaseButtonContent from './BaseButtonContent.vue';

// Define props
const props = defineProps<{
  variant?:
    | 'primary'
    | 'secondary'
    | 'ghost'
    | 'ghibli-primary'
    | 'ghibli-secondary'
    | 'danger'
    | 'outline';
  size?: 'sm' | 'md' | 'lg';
  type?: 'button' | 'submit' | 'reset';
  to?: string;
  href?: string;
  disabled?: boolean;
  loading?: boolean;
  block?: boolean;
  icon?: string;
}>();

// Base classes for all buttons
const baseClasses =
  'inline-flex items-center justify-center font-bold rounded-full transition-all duration-300 border-none outline-none focus-visible:ring-2 focus-visible:ring-sage focus-visible:ring-offset-2 cursor-pointer font-nunito disabled:opacity-60 disabled:cursor-not-allowed gap-2';

// Variant classes
const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-sage text-white shadow-soft hover:-translate-y-0.5 hover:shadow-card hover:bg-sage-dark active:scale-95';
    case 'secondary':
      return 'bg-terracotta-200 text-brown-dark shadow-soft hover:-translate-y-0.5 hover:shadow-card hover:bg-terracotta-300 active:scale-95';
    case 'ghost':
      return 'bg-transparent text-brown hover:bg-cream-dark/40';
    case 'ghibli-primary':
      return 'bg-sage-dark text-white shadow-[0_4px_12px_rgba(91,120,88,0.3)] hover:bg-sage hover:shadow-[0_6px_16px_rgba(91,120,88,0.4)] hover:-translate-y-px active:scale-98';
    case 'ghibli-secondary':
      return 'bg-terracotta text-white shadow-[0_4px_12px_rgba(214,122,79,0.3)] hover:bg-terracotta-dark hover:shadow-[0_6px_16px_rgba(214,122,79,0.4)] hover:-translate-y-px active:scale-98';
    case 'danger':
      return 'bg-red-500 text-white shadow-soft hover:bg-red-600 hover:-translate-y-0.5 active:scale-95';
    case 'outline':
      return 'bg-transparent border-2 border-sage text-sage hover:bg-sage hover:text-white';
    default:
      return 'bg-sage text-white shadow-soft hover:-translate-y-0.5 hover:shadow-card hover:bg-sage-dark active:scale-95';
  }
});

// Size classes
const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'px-4 py-1.5 text-sm';
    case 'lg':
      return 'px-8 py-4 text-lg';
    default:
      return 'px-6 py-3 text-base'; // Default to md
  }
});

const classes = computed(() => {
  return [
    baseClasses,
    variantClasses.value,
    sizeClasses.value,
    props.block ? 'w-full flex' : '',
    props.loading ? 'cursor-wait opacity-80' : '',
  ].join(' ');
});

const isRouterLink = computed(() => !!props.to);
const isExternalLink = computed(() => !!props.href);
</script>

<template>
  <!-- Router Link -->
  <RouterLink v-if="isRouterLink" :to="to!" :class="classes">
    <BaseButtonContent :loading="loading">
      <template #icon-left><slot name="icon-left"></slot></template>
      <slot></slot>
      <template #icon-right><slot name="icon-right"></slot></template>
    </BaseButtonContent>
  </RouterLink>

  <!-- External Link -->
  <a
    v-else-if="isExternalLink"
    :href="href"
    target="_blank"
    rel="noopener noreferrer"
    :class="classes"
  >
    <BaseButtonContent :loading="loading">
      <template #icon-left><slot name="icon-left"></slot></template>
      <slot></slot>
      <template #icon-right><slot name="icon-right"></slot></template>
    </BaseButtonContent>
  </a>

  <!-- Button -->
  <button v-else :type="type || 'button'" :class="classes" :disabled="disabled || loading">
    <BaseButtonContent :loading="loading">
      <template #icon-left><slot name="icon-left"></slot></template>
      <slot></slot>
      <template #icon-right><slot name="icon-right"></slot></template>
    </BaseButtonContent>
  </button>
</template>
