<template>
  <div
    class="inline-block bg-[#f0f0f0] bg-[linear-gradient(90deg,#f0f0f0_25%,#e0e0e0_50%,#f0f0f0_75%)] bg-[length:200%_100%] animate-shimmer"
    :style="{
      width: width,
      height: height,
      borderRadius: borderRadius,
    }"
  ></div>
</template>

<script setup lang="ts">
defineProps({
  width: {
    type: String,
    default: '100%',
  },
  height: {
    type: String,
    default: '100%',
  },
  borderRadius: {
    type: String,
    default: '0.5rem',
  },
});
</script>
