<script setup lang="ts">
import { computed, ref } from 'vue';
import EyeIcon from '@/components/icons/EyeIcon.vue';
import EyeOffIcon from '@/components/icons/EyeOffIcon.vue';

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

const updateValue = (event: Event): void => {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement;
  emit('update:modelValue', target.value);
};
</script>

<template>
  <div :class="[block ? 'w-full' : '', 'mb-4']">
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
          <EyeOffIcon v-if="showPassword" />
          <!-- Eye Icon (Show) -->
          <EyeIcon v-else />
        </button>
      </template>
    </div>

    <p v-if="error" class="text-terracotta text-xs mt-1 ml-1 font-bold">{{ error }}</p>
  </div>
</template>
