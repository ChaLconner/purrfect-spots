<script setup lang="ts">
import { defineAsyncComponent } from 'vue';

const GhibliBackground = defineAsyncComponent(
  () => import('@/components/ui/GhibliBackground.vue')
);

withDefaults(
  defineProps<{
    illustrationText?: string;
    showDeferredVisuals?: boolean;
  }>(),
  {
    illustrationText: '',
    showDeferredVisuals: true,
  }
);
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4 sm:p-8 relative overflow-hidden bg-[#eaf6f3]">
    <GhibliBackground v-if="showDeferredVisuals" />

    <div
      class="grid grid-cols-1 md:grid-cols-2 w-full max-w-[1000px] md:min-h-[600px] bg-white/50 backdrop-blur-[20px] rounded-[2rem] shadow-[0_25px_50px_-12px_rgba(0,0,0,0.1),_0_0_0_1px_rgba(255,255,255,0.4)_inset,_-0_-2px_0_rgba(255,255,255,0.1)_inset] overflow-hidden relative z-10 max-md:max-w-[480px] max-md:min-h-fit"
    >
      <!-- Left Side - Illustration -->
      <div
        class="bg-gradient-to-br from-[rgba(127,183,164,0.85)] via-[rgba(149,196,180,0.85)] to-[rgba(168,212,197,0.85)] flex flex-col items-center justify-center p-6 sm:p-8 md:p-12 relative overflow-hidden max-md:order-[-1]"
      >
        <div class="text-center z-10">
          <img
            src="/cat-illustration.webp"
            alt="Cat Illustration"
            fetchpriority="high"
            loading="eager"
            class="w-[120px] h-[120px] sm:w-[160px] sm:h-[160px] md:w-[280px] md:h-[280px] object-cover rounded-full border-4 md:border-6 border-white/40 shadow-[0_20px_40px_rgba(0,0,0,0.15),_0_0_0_8px_rgba(255,255,255,0.1)] md:shadow-[0_20px_40px_rgba(0,0,0,0.15),_0_0_0_12px_rgba(255,255,255,0.1)] animate-[float_6s_ease-in-out_infinite] transition-transform duration-300 hover:scale-105 block mx-auto"
          />
          <div class="mt-8">
            <h2 class="font-['Nunito'] text-[1.4rem] md:text-[1.8rem] font-extrabold text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.1)] mb-2">
              Purrfect Spots
            </h2>
            <p class="font-sans text-[0.9rem] md:text-base text-white/90 max-w-[250px] mx-auto leading-relaxed">
              {{ illustrationText || $t('auth.discoverSpots') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Right Side - Content Slot -->
      <div class="p-6 sm:p-8 md:p-12 flex flex-col justify-center">
      <slot></slot>
      </div>
    </div>
  </div>
</template>
