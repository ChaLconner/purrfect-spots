<template>
  <div
    class="inline-block h-[var(--skeleton-height)] w-[var(--skeleton-width)] rounded-[var(--skeleton-radius)] bg-[#f0f0f0] bg-[linear-gradient(90deg,#f0f0f0_25%,#e0e0e0_50%,#f0f0f0_75%)] bg-[length:200%_100%] animate-shimmer"
    :style="skeletonStyle"
  ></div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
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

const skeletonStyle = computed<Record<string, string>>(() => ({
  '--skeleton-width': props.width,
  '--skeleton-height': props.height,
  '--skeleton-radius': props.borderRadius,
}));
</script>
