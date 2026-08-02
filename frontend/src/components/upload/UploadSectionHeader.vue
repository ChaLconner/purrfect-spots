<template>
  <div class="flex items-baseline justify-between border-b border-stone-200 pb-4">
    <h2 class="text-2xl font-heading font-bold text-brown flex items-center">
      {{ t(titleKey) }}
      <svg
        v-if="!isAuthenticated"
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5 ml-2 text-stone-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        title="Login required"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
    </h2>
    <div class="flex items-center gap-2">
      <span v-if="infoKey" class="text-sm font-medium text-stone-500 uppercase tracking-widest">
        {{ t(infoKey) }}
      </span>
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

defineProps<{
  titleKey: string;
  infoKey?: string;
  isAuthenticated: boolean;
}>();

const { t } = useI18n();
</script>
