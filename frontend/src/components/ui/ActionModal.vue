<script setup lang="ts">
import BaseModal from './BaseModal.vue';

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

<template>
  <BaseModal :is-open="modelValue" max-width="md" @close="close">
    <h3 class="text-xl font-heading font-bold text-brown mb-4">{{ title }}</h3>

    <div v-if="warning" class="mb-4 text-sm text-red-600 font-medium">
      {{ warning }}
    </div>

    <slot></slot>

    <div class="flex justify-end gap-3 mt-6">
      <button
        class="px-4 py-2 border border-sand-300 rounded-xl text-brown hover:bg-sand-100 transition-colors font-medium cursor-pointer"
        @click="close"
      >
        {{ cancelText || 'Cancel' }}
      </button>
      <button
        class="px-4 py-2 rounded-xl text-white font-bold transition-all cursor-pointer shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
        :class="confirmButtonClass || 'bg-terracotta hover:bg-terracotta-dark'"
        :disabled="disableConfirm"
        @click="$emit('confirm')"
      >
        {{ confirmText || 'Confirm' }}
      </button>
    </div>
  </BaseModal>
</template>
