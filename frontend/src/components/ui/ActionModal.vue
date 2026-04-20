<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    @click="close"
  >
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6" @click.stop>
      <h3 class="text-lg font-bold text-brown-900 mb-4">{{ title }}</h3>
      
      <div v-if="warning" class="mb-4 text-sm text-red-600 font-medium">
        {{ warning }}
      </div>

      <slot></slot>

      <div class="flex justify-end gap-3 mt-6">
        <button
          class="px-4 py-2 border border-sand-300 rounded-md text-brown-700 hover:bg-sand-50 transition-colors"
          @click="close"
        >
          {{ cancelText || 'Cancel' }}
        </button>
        <button
          class="px-4 py-2 rounded-md text-white font-medium transition-colors"
          :class="confirmButtonClass || 'bg-terracotta-600 hover:bg-terracotta-700'"
          :disabled="disableConfirm"
          @click="$emit('confirm')"
        >
          {{ confirmText || 'Confirm' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: boolean;
  title: string;
  warning?: string;
  cancelText?: string;
  confirmText?: string;
  confirmButtonClass?: string;
  disableConfirm?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'confirm'): void;
}>();

const close = (): void => {
  emit('update:modelValue', false);
};
</script>
