<template>
  <div
    class="min-h-[400px] flex flex-col items-center justify-center p-8 text-center animate-fadeIn"
  >
    <!-- Animated Glow Background -->
    <div class="relative mb-8 group">
      <div
        class="absolute inset-0 bg-red-400/20 blur-[60px] rounded-full transform scale-150 animate-pulse"
        style="animation-duration: 3s"
      ></div>
      <h3
        class="relative text-3xl md:text-5xl font-bold text-white drop-shadow-sm font-serif tracking-wide leading-tight"
      >
        <span class="whitespace-pre-line">{{ title }}</span>
      </h3>
    </div>

    <!-- Error Message -->
    <p
      class="text-[#5A4A3A]/90 text-lg mb-10 font-medium max-w-md leading-relaxed tracking-wide relative z-10"
    >
      {{ message }}
    </p>

    <!-- Retry Button -->
    <button
      class="group relative px-10 py-3.5 overflow-hidden bg-white/40 hover:bg-white/60 backdrop-blur-md border border-white/60 rounded-full transition-all duration-500 shadow-sm hover:shadow-lg hover:-translate-y-0.5 cursor-pointer z-10"
      @click="$emit('retry')"
    >
      <span
        class="relative z-10 font-bold text-[#5A4A3A] group-hover:text-[#3A2A1A] transition-colors tracking-wide"
      >
        {{ retryText }}
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps({
  title: {
    type: String,
    default: 'Something went\nwrong',
  },
  message: {
    type: String,
    default: 'An unexpected error occurred.',
  },
  retryText: {
    type: String,
    default: 'Try Again',
  },
});

defineEmits(['retry']);
</script>
