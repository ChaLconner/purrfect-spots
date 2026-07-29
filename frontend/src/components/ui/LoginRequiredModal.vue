<script setup lang="ts">
import BaseModal from './BaseModal.vue';

defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits(['close', 'login']);

const close = (): void => {
  emit('close');
};

const handleLogin = (): void => {
  emit('login');
};
</script>

<template>
  <BaseModal :is-open="isOpen" max-width="sm" :show-close-button="false" @close="close">
    <!-- Decorative Cat Element -->
    <div
      class="absolute -top-12 left-1/2 transform -translate-x-1/2 w-24 h-24 bg-terracotta rounded-full flex items-center justify-center border-4 border-white shadow-lg"
    >
      <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
    </div>

    <div class="mt-8 text-center space-y-4 font-body">
      <h3 class="text-2xl font-heading font-bold text-brown">Login Required</h3>

      <p class="text-brown-light leading-relaxed">
        Join our community to share your purrfect discoveries! You need to be logged in to upload
        spots.
      </p>

      <div class="pt-4 space-y-3">
        <button
          class="w-full py-3 bg-terracotta text-white font-heading font-bold rounded-xl shadow-lg hover:bg-terracotta-dark transition-all duration-300 cursor-pointer"
          @click="handleLogin"
        >
          Log In Now
        </button>

        <button
          class="w-full py-3 bg-sand-100 text-sand-600 font-heading font-bold rounded-xl hover:bg-sand-200 transition-all duration-300 cursor-pointer"
          @click="close"
        >
          Maybe Later
        </button>
      </div>
    </div>
  </BaseModal>
</template>
