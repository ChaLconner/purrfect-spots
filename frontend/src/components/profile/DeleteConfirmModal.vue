<script setup lang="ts">
import { useI18n } from 'vue-i18n';

defineProps<{
  isOpen: boolean;
  isDeleting: boolean;
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
        class="bg-white rounded-xl md:rounded-2xl shadow-xl p-4 sm:p-6 md:p-8 w-full max-w-sm text-center relative border-t-4 border-red-500"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-12 w-12 sm:h-14 sm:w-14 md:h-16 md:w-16 text-red-100 mx-auto mb-3 sm:mb-4 bg-red-50 rounded-full p-2 sm:p-2.5 md:p-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
        <h3 class="text-lg sm:text-xl font-heading font-bold text-brown mb-1.5 sm:mb-2">
          {{ t('profile.deleteMemoryTitle') }}
        </h3>
        <p class="text-stone-500 mb-4 sm:mb-6 text-sm sm:text-base">
          {{ t('profile.deleteMemoryMessage') }}
        </p>

        <div class="flex justify-center gap-2 sm:gap-3">
          <button
            class="px-4 sm:px-5 py-2 text-stone-500 hover:bg-stone-50 rounded-lg font-medium transition-colors cursor-pointer text-sm sm:text-base"
            @click="$emit('close')"
          >
            {{ t('common.keepIt') }}
          </button>
          <button
            :disabled="isDeleting"
            class="px-4 sm:px-5 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg shadow-md font-bold transition-all disabled:opacity-50 cursor-pointer text-sm sm:text-base"
            @click="$emit('confirm')"
          >
            {{ isDeleting ? t('common.deleting') : t('common.yesDelete') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
