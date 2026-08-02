<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue';

const props = withDefaults(
  defineProps<{
    isOpen: boolean;
    maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
    closeOnEscape?: boolean;
    closeOnBackdrop?: boolean;
    showCloseButton?: boolean;
    teleportDisabled?: boolean;
  }>(),
  {
    maxWidth: 'md',
    closeOnEscape: true,
    closeOnBackdrop: true,
    showCloseButton: true,
    teleportDisabled: false,
  }
);

const isTestEnv = import.meta.env.MODE === 'test';
const shouldDisableTeleport = computed(() => props.teleportDisabled || isTestEnv);

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const handleKeyDown = (event: KeyboardEvent): void => {
  if (props.isOpen && props.closeOnEscape && event.key === 'Escape') {
    emit('close');
  }
};

const handleBackdropClick = (): void => {
  if (props.closeOnBackdrop) {
    emit('close');
  }
};

watch(
  () => props.isOpen,
  (val) => {
    if (typeof window !== 'undefined') {
      if (val) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    }
  }
);

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
  if (typeof window !== 'undefined') {
    document.body.style.overflow = '';
  }
});

const maxWidthClass = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  full: 'max-w-full m-4',
}[props.maxWidth];
</script>

<template>
  <Teleport to="body" :disabled="shouldDisableTeleport">
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center z-[1000] p-4 overflow-y-auto"
        @click.self="handleBackdropClick"
      >
        <Transition
          enter-active-class="transition duration-300 ease-out"
          enter-from-class="opacity-0 scale-95 translate-y-2.5"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition duration-200 ease-in"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 translate-y-2.5"
          appear
        >
          <div
            class="bg-cream-light rounded-2xl shadow-xl p-6 w-full relative border-2 border-sage/20 font-body my-auto"
            :class="maxWidthClass"
          >
            <button
              v-if="showCloseButton"
              type="button"
              class="absolute top-4 right-4 text-stone-400 hover:text-stone-600 w-8 h-8 rounded-full flex items-center justify-center transition-colors hover:bg-stone-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-sage cursor-pointer"
              aria-label="Close modal"
              @click="emit('close')"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
            <slot></slot>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
