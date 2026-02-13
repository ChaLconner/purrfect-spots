<template>
  <div class="p-16 text-center flex flex-col items-center justify-center min-h-[400px]">
    <div
      class="w-20 h-20 bg-sage/20 rounded-full flex items-center justify-center mb-6 text-sage-dark"
    >
      <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
    </div>
    <h3 class="text-3xl font-heading font-bold text-brown mb-4">Spot Added!</h3>
    <p class="text-brown-light mb-10 text-lg">Thank you for contributing to the map.</p>
    <div class="flex flex-col sm:flex-row gap-4 justify-center w-full max-w-md">
      <button
        class="px-8 py-3 bg-white border-2 border-terracotta text-terracotta font-heading font-bold rounded-xl hover:bg-terracotta hover:text-white transition-all duration-300 transform hover:-translate-y-1"
        @click="$emit('upload-another')"
      >
        Upload Another
      </button>
      <button
        class="px-8 py-3 font-heading font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
        style="background-color: #c97b49; color: white"
        @click="$emit('view-map')"
      >
        View Map
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  'upload-another': [];
  'view-map': [];
}>();
</script>
