<template>
  <div class="flex flex-col items-center justify-center min-h-screen relative overflow-hidden bg-cream px-4 text-center">
    <GhibliBackground />
    <div class="relative z-10 p-8 sm:p-12 bg-white/80 backdrop-blur-md rounded-[2.5rem] shadow-xl max-w-lg w-full border-2 border-sage/20">
      <div class="text-7xl mb-4 animate-bounce-slow">🐾</div>
      <h1 class="text-5xl font-heading font-extrabold text-brown mb-3 tracking-tight">404</h1>
      <p class="text-xl font-heading font-bold text-brown mb-2">{{ $t('notFound.title') }}</p>
      <p class="text-base font-body text-brown-meta mb-8 leading-relaxed">{{ $t('notFound.message') }}</p>
      <BaseButton to="/" variant="ghibli-primary" size="lg">
        {{ $t('notFound.goHome') }}
      </BaseButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import BaseButton from '@/components/ui/BaseButton.vue';
</script>
