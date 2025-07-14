<template>
  <div class="loading-spinner" :class="containerClass">
    <DotLottieVue 
      :style="lottieStyle"
      autoplay 
      loop 
      :src="animationSrc" 
    />
    <span v-if="showText" class="mt-2 text-sm font-medium" :class="textColor">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, withDefaults } from 'vue';
import { DotLottieVue } from '@lottiefiles/dotlottie-vue';

interface Props {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  showText?: boolean;
  textColor?: string;
  animation?: 'cat' | 'loading' | 'spinner';
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  text: 'กำลังโหลด...',
  showText: false,
  textColor: 'text-gray-600',
  animation: 'cat',
});

const lottieStyle = computed(() => {
  const sizes = {
    sm: { height: '60px', width: '60px' },
    md: { height: '100px', width: '100px' },
    lg: { height: '150px', width: '150px' },
    xl: { height: '200px', width: '200px' },
  };
  return sizes[props.size];
});

const containerClass = computed(() => {
  return 'flex flex-col items-center justify-center';
});

const animationSrc = computed(() => {
  // Using a reliable cat animation URL
  return 'https://lottie.host/embed/5c7ed735-9d3b-4f87-a3db-2e5a1d8c7b6f/HU0MXXkATE.json';
});
</script>

<style scoped>
.loading-spinner {
  user-select: none;
  pointer-events: none;
}

/* Ensure the animation is centered and smooth */
:deep(.dotlottie-canvas) {
  border-radius: 8px;
}
</style>