<template>
  <div class="tags-input-container">
    <!-- Tags Display -->
    <div class="tags-wrapper">
      <TransitionGroup name="tag">
        <span
          v-for="(tag, index) in modelValue"
          :key="tag"
          class="tag-chip"
        >
          <span class="tag-text">#{{ tag }}</span>
          <button
            type="button"
            class="tag-remove"
            aria-label="Remove tag"
            @click="removeTag(index)"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </span>
      </TransitionGroup>
      
      <!-- Input Field -->
      <input
        ref="inputRef"
        v-model="inputValue"
        type="text"
        :placeholder="modelValue.length >= maxTags ? 'Max tags reached' : placeholder"
        :disabled="modelValue.length >= maxTags || disabled"
        class="tag-input"
        @keydown.enter.prevent="addTag"
        @keydown="handleInputKeydown"
        @keydown.backspace="handleBackspace"
        @blur="addTag"
        @focus="$emit('focus', $event)"
      />
    </div>
    
    <!-- Helper Text -->
    <div class="tags-helper">
      <span class="tags-count" :class="{ 'at-limit': modelValue.length >= maxTags }">
        {{ modelValue.length }}/{{ maxTags }} tags
      </span>
      <span v-if="inputValue && inputValue.length > maxTagLength" class="tag-warning">
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
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void;
  (e: 'focus', event: FocusEvent): void;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Add tags (press Enter or comma)',
  maxTags: 20,
  maxTagLength: 50,
  disabled: false
});

const emit = defineEmits<Emits>();

const inputRef = ref<HTMLInputElement | null>(null);
const inputValue = ref('');

// Sanitize tag to match backend rules
const sanitizeTag = (tag: string): string => {
  // Remove # prefix if present
  let cleaned = tag.replace(/^#/, '');
  
  // Keep only alphanumeric, Thai characters, underscores, spaces, and hyphens
  cleaned = cleaned.replace(/[^a-zA-Z0-9\u0E00-\u0E7F_\s-]/g, '');
  
  // Normalize whitespace and convert to lowercase
  cleaned = cleaned.replace(/\s+/g, ' ').trim().toLowerCase();
  
  // Enforce max length
  return cleaned.slice(0, props.maxTagLength);
};

const addTag = () => {
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

const removeTag = (index: number) => {
  const newTags = [...props.modelValue];
  newTags.splice(index, 1);
  emit('update:modelValue', newTags);
};

const handleInputKeydown = (e: KeyboardEvent) => {
  if (e.key === ',') {
    e.preventDefault();
    addTag();
  }
};

const handleBackspace = () => {
  if (inputValue.value === '' && props.modelValue.length > 0) {
    removeTag(props.modelValue.length - 1);
  }
};

// Focus the input when clicking the container
const focusInput = () => {
  inputRef.value?.focus();
};

// Expose focus method
defineExpose({ focus: focusInput });
</script>

<style scoped>
.tags-input-container {
  width: 100%;
}

.tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.7);
  border: 2px solid #e7e5e4;
  border-radius: 0.75rem;
  min-height: 52px;
  transition: all 0.2s ease;
  cursor: text;
}

.tags-wrapper:focus-within {
  border-color: #c1714f;
  box-shadow: 0 0 0 4px rgba(193, 113, 79, 0.1);
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem 0.25rem 0.75rem;
  background: linear-gradient(135deg, #c1714f 0%, #a65d37 100%);
  color: white;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  animation: tag-enter 0.2s ease;
}

.tag-text {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tag-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  padding: 0;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.15s ease;
  color: white;
}

.tag-remove:hover {
  background: rgba(255, 255, 255, 0.4);
  transform: scale(1.1);
}

.tag-input {
  flex: 1;
  min-width: 120px;
  padding: 0.25rem 0;
  border: none;
  background: transparent;
  font-size: 0.875rem;
  font-weight: 500;
  color: #57534e;
  outline: none;
}

.tag-input::placeholder {
  color: #a8a29e;
}

.tag-input:disabled {
  cursor: not-allowed;
}

.tags-helper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
  padding: 0 0.25rem;
  font-size: 0.75rem;
}

.tags-count {
  color: #78716c;
  transition: color 0.2s ease;
}

.tags-count.at-limit {
  color: #c1714f;
  font-weight: 600;
}

.tag-warning {
  color: #dc2626;
  font-weight: 500;
}

/* Transition animations */
.tag-enter-active,
.tag-leave-active {
  transition: all 0.2s ease;
}

.tag-enter-from {
  opacity: 0;
  transform: scale(0.8);
}

.tag-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.tag-move {
  transition: transform 0.2s ease;
}

@keyframes tag-enter {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Mobile adjustments */
@media (max-width: 640px) {
  .tags-wrapper {
    padding: 0.5rem 0.75rem;
  }
  
  .tag-chip {
    font-size: 0.8rem;
    padding: 0.2rem 0.4rem 0.2rem 0.6rem;
  }
  
  .tag-text {
    max-width: 100px;
  }
}
</style>
