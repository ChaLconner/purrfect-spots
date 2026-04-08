<script setup lang="ts">
import { useRouter } from 'vue-router';

interface Props {
  title?: string;
  message?: string;
  subMessage?: string;
  actionText?: string;
  actionLink?: string;
  icon?: 'peek' | 'nap' | 'wait' | 'box';
}

const props = defineProps<Props>();
const router = useRouter();

const currentIcon =
  props.icon ||
  (['peek', 'nap', 'wait', 'box'][Math.floor(Math.random() * 4)] as
    | 'peek'
    | 'nap'
    | 'wait'
    | 'box');

const handleAction = (): void => {
  if (props.actionLink) {
    router.push(props.actionLink);
  }
};
</script>

<template>
  <div
    class="min-h-[450px] flex flex-col items-center justify-center p-8 text-center animate-fade-in relative overflow-hidden rounded-[2rem]"
  >
    <!-- Background Glow -->
    <div
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-terracotta/5 blur-[100px] rounded-full"
    ></div>

    <!-- Illustration Area -->
    <div class="relative mb-8 group">
      <div
        class="absolute inset-0 bg-terracotta/10 blur-[50px] rounded-full scale-150 opacity-0 group-hover:opacity-100 transition-opacity duration-700"
      ></div>

      <!-- Ghibli-style Illustrations -->
      <div
        class="relative z-10 w-48 h-48 md:w-56 md:h-56 mx-auto flex items-center justify-center bg-white/40 backdrop-blur-md rounded-full border border-white/60 shadow-inner overflow-hidden"
      >
        <!-- Peek Style -->
        <svg
          v-if="currentIcon === 'peek'"
          viewBox="0 0 200 200"
          class="w-32 h-32 md:w-40 md:h-40 text-stone-300 transform group-hover:scale-110 group-hover:translate-y--2 transition-transform duration-700"
        >
          <path
            d="M40 160 Q100 170 160 160 L160 100 Q160 60 100 60 Q40 60 40 100 Z"
            fill="currentColor"
            opacity="0.6"
          />
          <path
            d="M70 60 L60 30 L90 55 Z M130 60 L140 30 L110 55 Z"
            fill="currentColor"
            opacity="0.8"
          />
          <circle cx="85" cy="100" r="5" fill="white" opacity="0.8" />
          <circle cx="115" cy="100" r="5" fill="white" opacity="0.8" />
        </svg>

        <!-- Nap Style -->
        <svg
          v-else-if="currentIcon === 'nap'"
          viewBox="0 0 200 200"
          class="w-32 h-32 md:w-40 md:h-40 text-stone-300 group-hover:scale-105 transition-transform duration-700"
        >
          <path
            d="M30 140 Q100 160 170 140 Q160 90 100 90 Q40 90 30 140 Z"
            fill="currentColor"
            opacity="0.6"
          />
          <path
            d="M70 115 Q85 110 100 115 M115 115 Q130 110 145 115"
            stroke="white"
            stroke-width="3"
            fill="none"
            opacity="0.6"
          />
          <path
            d="M150 140 Q170 120 160 100"
            stroke="currentColor"
            stroke-width="4"
            fill="none"
            opacity="0.4"
          />
        </svg>

        <!-- Wait Style -->
        <svg
          v-else-if="currentIcon === 'wait'"
          viewBox="0 0 200 200"
          class="w-32 h-32 md:w-40 md:h-40 text-stone-300 group-hover:rotate-2 transition-transform duration-700"
        >
          <path
            d="M70 160 L130 160 L130 80 Q130 50 100 50 Q70 50 70 80 Z"
            fill="currentColor"
            opacity="0.6"
          />
          <path
            d="M80 50 L75 25 L95 45 Z M120 50 L125 25 L105 45 Z"
            fill="currentColor"
            opacity="0.8"
          />
          <path
            d="M90 150 Q100 160 110 150"
            stroke="white"
            stroke-width="3"
            fill="none"
            opacity="0.5"
          />
        </svg>

        <!-- Box Style (Default) -->
        <svg
          v-else
          viewBox="0 0 200 200"
          class="w-32 h-32 md:w-40 md:h-40 text-stone-300 transform group-hover:scale-110 group-hover:rotate-3 transition-transform duration-700"
        >
          <path fill="currentColor" opacity="0.4" d="M100 40 L130 80 L70 80 Z" />
          <path
            fill="currentColor"
            opacity="0.6"
            d="M40 100 Q40 60 100 60 Q160 60 160 100 L160 160 Q100 170 40 160 Z"
          />
          <circle cx="80" cy="110" r="10" fill="white" opacity="0.5" />
          <circle cx="120" cy="110" r="10" fill="white" opacity="0.5" />
          <path
            d="M90 135 Q100 145 110 135"
            stroke="white"
            stroke-width="4"
            fill="none"
            opacity="0.5"
          />
        </svg>

        <!-- Floating Dust Particles -->
        <div
          class="absolute w-2 h-2 bg-yellow-400/30 rounded-full animate-ping top-10 right-10"
        ></div>
        <div
          class="absolute w-1.5 h-1.5 bg-terracotta/20 rounded-full animate-bounce bottom-12 left-14"
          style="animation-delay: 1s"
        ></div>
      </div>
    </div>

    <!-- Text Content -->
    <div class="relative z-10 max-w-md space-y-4">
      <h3 class="text-3xl md:text-4xl font-heading font-bold text-brown tracking-tight">
        {{ title || 'Quiet Corner' }}
      </h3>

      <div class="space-y-2">
        <p class="text-brown-light text-lg md:text-xl font-body leading-relaxed">
          {{ message }}
        </p>
        <p v-if="subMessage" class="text-stone-400 text-sm md:text-base italic">
          {{ subMessage }}
        </p>
      </div>

      <!-- Action Button -->
      <div v-if="actionText && actionLink" class="pt-6">
        <button
          class="px-10 py-4 bg-terracotta text-white rounded-full font-bold shadow-[0_10px_20px_-5px_rgba(210,105,30,0.3)] hover:shadow-[0_15px_30px_-8px_rgba(210,105,30,0.4)] hover:-translate-y-1 active:scale-95 transition-all duration-300"
          @click="handleAction"
        >
          {{ actionText }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.animate-fade-in {
  animation: fade-in 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
