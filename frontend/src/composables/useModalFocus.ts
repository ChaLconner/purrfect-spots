import {
  ref,
  onMounted,
  onUnmounted,
  getCurrentInstance,
  nextTick,
  watch,
  type Ref,
} from 'vue';
import { useFocusTrap } from './useAccessibility';

export function useModalFocus(
  modalContainer: Ref<HTMLElement | null>,
  options: {
    onClose: () => void;
    lockScroll?: boolean;
  }
): { handleKeydown: (e: KeyboardEvent) => void; trapFocus: (e: KeyboardEvent) => void } {
  const previousFocus = ref<HTMLElement | null>(null);
  const focusTrap = useFocusTrap(modalContainer);
  let isActive = false;

  const activate = (container: HTMLElement): void => {
    if (!isActive) {
      previousFocus.value = document.activeElement as HTMLElement;
      if (options.lockScroll !== false) {
        document.body.style.overflow = 'hidden';
      }
      isActive = true;
    }

    nextTick(() => {
      if (modalContainer.value === container) {
        container.focus();
      }
    });
  };

  const deactivate = (): void => {
    if (!isActive) return;

    if (options.lockScroll !== false) {
      document.body.style.overflow = '';
    }
    isActive = false;

    if (previousFocus.value && previousFocus.value !== document.body) {
      previousFocus.value.focus();
    }
    previousFocus.value = null;
  };

  const trapFocus = (e: KeyboardEvent): void => {
    if (!modalContainer.value) return;

    const focusableElements = focusTrap.getFocusableElements();

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

  if (getCurrentInstance()) {
    onMounted(() => {
      if (modalContainer.value) {
        activate(modalContainer.value);
      }
    });

    // Modal content can be conditionally rendered after this composable mounts.
    // Activate focus and scroll locking when its container actually appears.
    watch(
      modalContainer,
      (container, previousContainer) => {
        if (container) {
          activate(container);
        } else if (previousContainer) {
          deactivate();
        }
      },
      { flush: 'post' }
    );

    onUnmounted(() => {
      deactivate();
    });
  }

  return {
    handleKeydown,
    trapFocus,
  };
}
