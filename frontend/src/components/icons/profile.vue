<template>
  <svg
    viewBox="0 0 24 24"
    :fill="fill"
    :stroke="color"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :width="size"
    :height="size"
    :class="className"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
</template>

<script setup lang="ts">
interface Props {
  size?: number | string;
  color?: string;
  fill?: string;
  className?: string;
}

withDefaults(defineProps<Props>(), {
  size: '100%',
  color: 'currentColor',
  fill: 'none',
  className: '',
});
</script>
