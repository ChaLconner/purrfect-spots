<script setup lang="ts">
import { computed, ref } from 'vue';

defineOptions({
  inheritAttrs: false,
});

const props = defineProps<{
  modelValue: string | number;
  type?: string;
  placeholder?: string;
  label?: string;
  id?: string;
  error?: string;
  block?: boolean;
  required?: boolean;
  disabled?: boolean;
  rows?: number; // For textarea
  isTextarea?: boolean;
  autocomplete?: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void;
}>();

const showPassword = ref(false);

const inputType = computed(() => {
  if (props.type === 'password' && showPassword.value) {
    return 'text';
  }
  return props.type || 'text';
});

const baseInputClasses =
  'w-full bg-white/50 border-2 border-sage/20 rounded-xl px-4 py-3 outline-none focus:border-sage focus:ring-4 focus:ring-sage/10 transition-all placeholder:text-brown-light/50 disabled:opacity-50 disabled:cursor-not-allowed text-brown';

const inputClasses = computed(() => {
  return [
    baseInputClasses,
    props.error ? 'border-terracotta focus:border-terracotta focus:ring-terracotta/10' : '',
    props.type === 'password' ? 'pr-10' : '',
  ].join(' ');
});

const updateValue = (event: Event) => {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement;
  emit('update:modelValue', target.value);
};
</script>

<template>
  <div :class="[{ 'w-full': block, 'mb-4': !error }]">
    <label v-if="label" :for="id" class="block text-sm font-bold text-brown mb-2 ml-1">
      {{ label }} <span v-if="required" class="text-terracotta">*</span>
    </label>

    <div class="relative">
      <textarea
        v-if="isTextarea"
        v-bind="$attrs"
        :id="id"
        :value="modelValue"
        :rows="rows || 3"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :class="inputClasses"
        @input="updateValue"
      ></textarea>

      <template v-else>
        <input
          v-bind="$attrs"
          :id="id"
          :type="inputType"
          :value="modelValue"
          :placeholder="placeholder"
          :disabled="disabled"
          :required="required"
          :autocomplete="autocomplete"
          :class="inputClasses"
          @input="updateValue"
        />

        <button
          v-if="type === 'password'"
          type="button"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-sage transition-colors flex items-center justify-center p-1"
          :aria-label="showPassword ? 'Hide password' : 'Show password'"
          @click="showPassword = !showPassword"
        >
          <!-- Eye Icon (Hide) -->
          <svg
            v-if="showPassword"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="w-5 h-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
            />
          </svg>
          <!-- Eye Icon (Show) -->
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="w-5 h-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </button>
      </template>
    </div>

    <p v-if="error" class="text-terracotta text-xs mt-1 ml-1 font-bold">{{ error }}</p>
  </div>
</template>
