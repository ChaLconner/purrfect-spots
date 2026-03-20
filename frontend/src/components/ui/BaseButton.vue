<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';

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
  'inline-flex items-center justify-center font-bold rounded-full transition-all duration-300 border-none outline-none cursor-pointer font-nunito disabled:opacity-60 disabled:cursor-not-allowed';

// Variant classes
const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-sage text-white shadow-soft hover:-translate-y-0.5 hover:shadow-card hover:bg-[#6da491] active:scale-95';
    case 'secondary':
      return 'bg-[#f6c1b1] text-brown shadow-soft hover:-translate-y-0.5 hover:shadow-card hover:bg-[#e5b0a0] active:scale-95';
    case 'ghost':
      return 'bg-transparent text-brown hover:bg-white/35';
    case 'ghibli-primary':
      return 'bg-sage-dark text-white shadow-[0_4px_12px_rgba(109,139,106,0.3)] hover:bg-[#5a7558] hover:shadow-[0_6px_16px_rgba(109,139,106,0.4)] hover:-translate-y-px active:scale-98';
    case 'ghibli-secondary':
      return 'bg-[#a85d2e] text-white shadow-[0_4px_12px_rgba(168,93,46,0.3)] hover:bg-[#8c4d26] hover:shadow-[0_6px_16px_rgba(168,93,46,0.4)] hover:-translate-y-px active:scale-98';
    case 'danger':
      return 'bg-red-500 text-white shadow-soft hover:bg-red-600 hover:-translate-y-0.5 active:scale-95';
    case 'outline':
      return 'bg-transparent border-2 border-sage text-sage hover:bg-sage hover:text-white';
    default:
      return 'bg-sage text-white shadow-soft hover:-translate-y-0.5 hover:shadow-card hover:bg-[#6da491] active:scale-95'; // Default to primary
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
    <template v-if="loading">
      <svg
        class="animate-spin h-5 w-5 text-current"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </template>
    <template v-else>
      <slot name="icon-left"></slot>
      <slot></slot>
      <slot name="icon-right"></slot>
    </template>
  </RouterLink>

  <!-- External Link -->
  <a
    v-else-if="isExternalLink"
    :href="href"
    target="_blank"
    rel="noopener noreferrer"
    :class="classes"
  >
    <template v-if="loading">
      <svg
        class="animate-spin h-5 w-5 text-current"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </template>
    <template v-else>
      <slot name="icon-left"></slot>
      <slot></slot>
      <slot name="icon-right"></slot>
    </template>
  </a>

  <!-- Button -->
  <button v-else :type="type || 'button'" :class="classes" :disabled="disabled || loading">
    <template v-if="loading">
      <svg
        class="animate-spin h-5 w-5 text-current"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </template>
    <template v-else>
      <slot name="icon-left"></slot>
      <slot></slot>
      <slot name="icon-right"></slot>
    </template>
  </button>
</template>
