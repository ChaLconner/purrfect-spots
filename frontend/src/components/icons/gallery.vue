<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
    viewBox="0 0 256 256"
    :fill="color"
    :class="className"
  >
    <path
      d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM156,88a12,12,0,1,1-12,12A12,12,0,0,1,156,88Zm60,112H40V160l52-52a8,8,0,0,1,11.31,0L144,148.69l20-20a8,8,0,0,1,11.31,0L216,169.37V200Z"
    />
  </svg>
</template>

<script setup lang="ts">
interface Props {
  size?: number | string;
  color?: string;
  className?: string;
}

withDefaults(defineProps<Props>(), {
  size: 32,
  color: 'currentColor',
  className: '',
});
</script>
