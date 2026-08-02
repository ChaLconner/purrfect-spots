<template>
  <div class="min-h-screen bg-[#fdf8f6] py-20 px-4 relative overflow-hidden">
    <GhibliBackground />
    <div class="max-w-4xl mx-auto bg-white/80 backdrop-blur-md rounded-3xl p-8 md:p-12 shadow-xl border border-white/50 relative z-10">
      <h1 class="text-4xl font-bold text-brown-900 mb-8 font-['Nunito']">{{ $t('termsOfService.title') }}</h1>

      <div ref="contentRef" class="prose-brown max-w-none text-brown-700"></div>

      <div class="mt-8 pt-8 border-t border-sand-200">
        <router-link to="/" class="text-terracotta-600 hover:text-terracotta-700 font-medium">
          {{ $t('termsOfService.backHome') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useLegalPageContent } from '@/composables/useLegalPageContent';

const { contentRef } = useLegalPageContent('termsOfService.content');
void contentRef;
</script>
