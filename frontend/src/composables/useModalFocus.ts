import { ref, onMounted, onUnmounted, nextTick, type Ref } from 'vue';

export function useModalFocus(
  modalContainer: Ref<HTMLElement | null>,
  options: {
    onClose: () => void;
    lockScroll?: boolean;
  }
): { handleKeydown: (e: KeyboardEvent) => void; trapFocus: (e: KeyboardEvent) => void } {
  const previousFocus = ref<HTMLElement | null>(null);

  const trapFocus = (e: KeyboardEvent): void => {
    if (!modalContainer.value) return;

    const focusableElements = modalContainer.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey) {
      // Shift + Tab
      if (
        document.activeElement === firstElement ||
        document.activeElement === modalContainer.value
      ) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  };

  const handleKeydown = (e: KeyboardEvent): void => {
    if (e.key === 'Escape') {
      options.onClose();
    } else if (e.key === 'Tab') {
      trapFocus(e);
    }
  };

  onMounted(() => {
    previousFocus.value = document.activeElement as HTMLElement;
    if (options.lockScroll !== false) {
      document.body.style.overflow = 'hidden';
    }

    nextTick(() => {
      modalContainer.value?.focus();
    });
  });

  onUnmounted(() => {
    if (options.lockScroll !== false) {
      document.body.style.overflow = '';
    }
    if (previousFocus.value) {
      previousFocus.value.focus();
    }
  });

  return {
    handleKeydown,
    trapFocus,
  };
}
