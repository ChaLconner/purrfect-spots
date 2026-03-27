<script setup lang="ts">
import { useI18n } from 'vue-i18n';

defineProps<{
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  isLoading?: boolean;
}>();

const { t } = useI18n();

defineEmits<{
  close: [];
  confirm: [];
}>();
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center z-[200] p-4"
    >
      <div
        class="bg-white rounded-xl md:rounded-2xl shadow-xl p-4 sm:p-6 md:p-8 w-full max-w-sm text-center relative border-t-4"
        :class="{
          'border-red-500': variant === 'danger',
          'border-yellow-500': variant === 'warning',
          'border-blue-500': variant === 'info' || !variant,
        }"
      >
        <slot name="icon">
          <div
            class="mx-auto mb-4 w-16 h-16 rounded-full flex items-center justify-center"
            :class="{
              'bg-red-50': variant === 'danger',
              'bg-yellow-50': variant === 'warning',
              'bg-blue-50': variant === 'info' || !variant,
            }"
          >
            <svg
              v-if="variant === 'danger'"
              xmlns="http://www.w3.org/2000/svg"
              class="h-8 w-8 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <svg
              v-else-if="variant === 'warning'"
              xmlns="http://www.w3.org/2000/svg"
              class="h-8 w-8 text-yellow-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              class="h-8 w-8 text-blue-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        </slot>

        <h3 class="text-lg sm:text-xl font-heading font-bold text-brown mb-2">
          {{ title }}
        </h3>
        <slot>
          <p class="text-stone-500 mb-6 text-sm sm:text-base">
            {{ message }}
          </p>
        </slot>

        <div class="flex justify-center gap-3">
          <button
            class="px-5 py-2 text-stone-500 hover:bg-stone-50 rounded-lg font-medium transition-colors cursor-pointer"
            :disabled="isLoading"
            @click="$emit('close')"
          >
            {{ cancelText || t('common.cancel') }}
          </button>
          <button
            :disabled="isLoading"
            class="px-5 py-2 text-white rounded-lg shadow-md font-bold transition-all cursor-pointer flex items-center justify-center gap-2"
            :class="{
              'bg-red-500 hover:bg-red-600': variant === 'danger',
              'bg-yellow-500 hover:bg-yellow-600': variant === 'warning',
              'bg-blue-500 hover:bg-blue-600': variant === 'info' || !variant,
            }"
            @click="$emit('confirm')"
          >
            <svg v-if="isLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            {{ confirmText || t('common.confirm') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
