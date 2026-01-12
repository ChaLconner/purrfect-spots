<template>
  <div 
    class="skeleton-loader" 
    :style="{ 
      width: width, 
      height: height, 
      borderRadius: borderRadius 
    }"
  ></div>
</template>

<script setup lang="ts">
defineProps({
  width: {
    type: String,
    default: '100%'
  },
  height: {
    type: String,
    default: '100%'
  },
  borderRadius: {
    type: String,
    default: '0.5rem'
  }
});
</script>

<style scoped>
.skeleton-loader {
  background: #f0f0f0;
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  display: inline-block;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
