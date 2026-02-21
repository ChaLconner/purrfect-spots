<template>
  <div class="w-full">
    <!-- Tags Display -->
    <div
      class="flex flex-wrap items-center gap-2 py-3 px-4 sm:py-2 sm:px-3 bg-white/70 border-2 border-stone-200 rounded-xl min-h-[52px] transition-all duration-200 cursor-text focus-within:border-[#c1714f] focus-within:ring-4 focus-within:ring-[#c1714f]/10"
      @click="focusInput"
    >
      <TransitionGroup
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 scale-[0.8]"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-200 ease-out absolute"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-[0.8]"
        move-class="transition-transform duration-200 ease-out"
      >
        <span
          v-for="(tag, index) in modelValue"
          :key="tag"
          class="inline-flex items-center gap-1 py-1 pl-3 pr-2 bg-gradient-to-br from-[#c1714f] to-[#a65d37] text-white rounded-full text-sm font-medium whitespace-nowrap sm:text-[0.8rem] sm:py-0.5 sm:pl-2.5 sm:pr-1.5 shadow-sm"
        >
          <span class="max-w-[150px] sm:max-w-[100px] overflow-hidden text-ellipsis">#{{ tag }}</span>
          <button
            type="button"
            class="flex items-center justify-center w-5 h-5 p-0 bg-white/20 border-none rounded-full cursor-pointer transition-all duration-150 text-white hover:bg-white/40 hover:scale-110 focus:outline-none"
            aria-label="Remove tag"
            @click.stop="removeTag(index)"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </span>
      </TransitionGroup>

      <!-- Input Field -->
      <input
        :id="id"
        ref="inputRef"
        v-model="inputValue"
        type="text"
        :placeholder="modelValue.length >= maxTags ? 'Max tags reached' : placeholder"
        :disabled="modelValue.length >= maxTags || disabled"
        class="flex-1 min-w-[120px] py-1 border-none bg-transparent text-sm font-medium text-stone-600 outline-none placeholder:text-stone-500 disabled:cursor-not-allowed"
        @keydown.enter.prevent="addTag"
        @keydown="handleInputKeydown"
        @keydown.backspace="handleBackspace"
        @blur="addTag"
        @focus="$emit('focus', $event)"
      />
    </div>

    <!-- Helper Text -->
    <div class="flex justify-between items-center mt-2 px-1 text-xs">
      <span
        class="transition-colors duration-200"
        :class="modelValue.length >= maxTags ? 'text-[#c1714f] font-semibold' : 'text-stone-500'"
      >
        {{ modelValue.length }}/{{ maxTags }} tags
      </span>
      <span v-if="inputValue && inputValue.length > maxTagLength" class="text-red-600 font-medium">
        Tag too long (max {{ maxTagLength }} chars)
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Props {
  modelValue: string[];
  placeholder?: string;
  maxTags?: number;
  maxTagLength?: number;
  disabled?: boolean;
  id?: string;
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void;
  (e: 'focus', event: FocusEvent): void;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Add tags (press Enter or comma)',
  maxTags: 20,
  maxTagLength: 50,
  disabled: false,
});

const emit = defineEmits<Emits>();

const inputRef = ref<HTMLInputElement | null>(null);
const inputValue = ref('');

// Sanitize tag to match backend rules
const sanitizeTag = (tag: string): string => {
  // Remove # prefix if present
  let cleaned = tag.replace(/^#/, '');

  // Keep only alphanumeric, Thai characters, underscores, spaces, and hyphens
  cleaned = cleaned.replaceAll(/[^a-zA-Z0-9\u0E00-\u0E7F_\s-]/g, '');

  // Normalize whitespace and convert to lowercase
  cleaned = cleaned.replaceAll(/\s+/g, ' ').trim().toLowerCase();

  // Enforce max length
  return cleaned.slice(0, props.maxTagLength);
};

const addTag = (): void => {
  if (!inputValue.value.trim()) return;
  if (props.modelValue.length >= props.maxTags) return;

  const newTag = sanitizeTag(inputValue.value);

  if (!newTag) {
    inputValue.value = '';
    return;
  }

  // Check for duplicates
  if (props.modelValue.includes(newTag)) {
    inputValue.value = '';
    return;
  }

  emit('update:modelValue', [...props.modelValue, newTag]);
  inputValue.value = '';
};

const removeTag = (index: number): void => {
  const newTags = [...props.modelValue];
  newTags.splice(index, 1);
  emit('update:modelValue', newTags);
};

const handleInputKeydown = (e: KeyboardEvent): void => {
  if (e.key === ',') {
    e.preventDefault();
    addTag();
  }
};

const handleBackspace = (): void => {
  if (inputValue.value === '' && props.modelValue.length > 0) {
    removeTag(props.modelValue.length - 1);
  }
};

// Focus the input when clicking the container
const focusInput = (): void => {
  inputRef.value?.focus();
};

// Expose focus method
defineExpose({ focus: focusInput });
</script>
