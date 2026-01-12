<script setup lang="ts">
import { toastState } from '../../store/toast';
import ToastItem from './ToastItem.vue';
</script>

<template>
  <div 
    aria-live="assertive" 
    class="pointer-events-none fixed inset-0 z-[10000] flex flex-col items-end justify-end px-4 py-6 sm:p-6"
  >
    <!-- Container for toasts -->
    <div class="flex flex-col w-full max-w-sm gap-2 pointer-events-none">
       <ToastItem 
         v-for="toast in toastState.toasts" 
         :key="toast.id" 
         :toast="toast" 
       />
    </div>
  </div>
</template>
