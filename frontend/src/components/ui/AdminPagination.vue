<template>
  <div
    v-if="show"
    class="px-6 py-4 border-t border-sand-200 flex items-center justify-between"
  >
    <button
      :disabled="page === 1"
      class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      @click="page > 1 && $emit('update:page', page - 1)"
    >
      {{ previousText || 'Previous' }}
    </button>
    <span class="text-sm text-brown-600">{{ pageText || `Page ${page}` }}</span>
    <button
      :disabled="itemsLength < limit || page * limit >= totalItems"
      class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      @click="$emit('update:page', page + 1)"
    >
      {{ nextText || 'Next' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  page: number;
  limit: number;
  totalItems: number;
  itemsLength: number;
  previousText?: string;
  nextText?: string;
  pageText?: string;
  alwaysShow?: boolean;
}>();

defineEmits<{
  (e: 'update:page', newPage: number): void;
}>();

const show = computed(() => {
  return props.alwaysShow || props.itemsLength > 0 || props.page > 1;
});
</script>
