<template>
  <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
    <div class="flex flex-col">
      <h1 class="text-2xl font-bold text-brown-900 font-display tracking-tight">
        {{ title }}
      </h1>
      <p v-if="subtitle" class="text-sm text-brown-500 font-medium mt-0.5">
        {{ subtitle }}
      </p>
    </div>

    <div class="flex items-center gap-3 w-full sm:w-auto">
      <slot name="actions"></slot>
      
      <div v-if="showSearch" class="relative w-full sm:max-w-md group">
        <svg
          class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-brown-400 group-focus-within:text-terracotta-500 transition-colors pointer-events-none"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          :value="modelValue"
          type="text"
          :placeholder="searchPlaceholder"
          class="w-full pl-10 pr-10 py-2 border border-sand-300 rounded-xl bg-white focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 transition-colors font-medium text-brown-800 outline-none"
          @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        />
        <button
          v-if="modelValue"
          class="absolute right-4 top-1/2 -translate-y-1/2 text-brown-400 hover:text-brown-700 p-1 rounded-full hover:bg-sand-100 transition-colors"
          @click="$emit('update:modelValue', '')"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
  modelValue?: string;
  showSearch?: boolean;
  searchPlaceholder?: string;
}>();

defineEmits(['update:modelValue']);
</script>
