<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop with blur -->
    <div 
      class="absolute inset-0 bg-stone-900/40 backdrop-blur-sm transition-opacity duration-300"
      @click="close"
    ></div>

    <!-- Modal Content -->
    <div 
      class="relative bg-white/95 backdrop-blur-md rounded-3xl shadow-2xl p-8 max-w-sm w-full border border-white/50 transform transition-all duration-300 scale-100"
      role="dialog"
      aria-modal="true"
    >
      <!-- Decorative Cat Element -->
      <div class="absolute -top-12 left-1/2 transform -translate-x-1/2 w-24 h-24 bg-[#C97B49] rounded-full flex items-center justify-center border-4 border-white shadow-lg">
        <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>

      <div class="mt-8 text-center space-y-4">
        <h3 class="text-2xl font-heading font-bold text-brown">Login Required</h3>
        
        <p class="text-brown-light leading-relaxed">
          Join our community to share your purrfect discoveries! You need to be logged in to upload spots.
        </p>

        <div class="pt-4 space-y-3">
          <button 
            @click="handleLogin"
            class="w-full py-3 bg-[#C97B49] text-white font-heading font-bold rounded-xl shadow-lg hover:bg-[#A85D2E] hover:scale-[1.02] transition-all duration-300"
          >
            Log In Now
          </button>
          
          <button 
            @click="close"
            class="w-full py-3 bg-stone-100 text-stone-500 font-heading font-bold rounded-xl hover:bg-stone-200 transition-all duration-300"
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  isOpen: boolean
}>();

const emit = defineEmits(['close', 'login']);

const close = () => {
  emit('close');
};

const handleLogin = () => {
  emit('login');
};
</script>

<style scoped>
.font-heading {
  font-family: 'Nunito', sans-serif;
}
</style>
