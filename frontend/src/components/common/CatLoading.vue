<template>
  <div class="cat-loading-container" :class="containerClass">
    <DotLottieVue 
      :style="lottieStyle"
      autoplay 
      loop 
      src="https://lottie.host/embed/5c7ed735-9d3b-4f87-a3db-2e5a1d8c7b6f/HU0MXXkATE.json"
    />
    <div v-if="showText" class="text-center mt-4">
      <h3 class="text-lg font-semibold text-gray-700 mb-2">{{ title }}</h3>
      <p class="text-sm text-gray-500">{{ subtitle }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, withDefaults } from 'vue';
import { DotLottieVue } from '@lottiefiles/dotlottie-vue';

interface Props {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'hero';
  showText?: boolean;
  title?: string;
  subtitle?: string;
  centered?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showText: true,
  title: '🐱 กำลังประมวลผล...',
  subtitle: 'กรุณารอสักครู่ เราพยายามหาแมวให้คุณ',
  centered: true,
});

const lottieStyle = computed(() => {
  const sizes = {
    sm: { height: '80px', width: '80px' },
    md: { height: '120px', width: '120px' },
    lg: { height: '180px', width: '180px' },
    xl: { height: '250px', width: '250px' },
    hero: { height: '400px', width: '400px' },
  };
  return sizes[props.size];
});

const containerClass = computed(() => {
  return [
    'cat-loading',
    {
      'flex flex-col items-center justify-center min-h-[200px]': props.centered,
      'inline-flex flex-col items-center': !props.centered,
    }
  ];
});
</script>

<style scoped>
.cat-loading-container {
  user-select: none;
}

.cat-loading {
  animation: gentle-bounce 2s ease-in-out infinite;
}

@keyframes gentle-bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .cat-loading-container :deep(.dotlottie-canvas) {
    max-width: 90vw;
    height: auto !important;
  }
}
</style>
