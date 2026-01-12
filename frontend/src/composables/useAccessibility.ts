/**
 * useAccessibility Composable
 * 
 * Provides accessibility utilities:
 * - Focus management for modals/dialogs
 * - Screen reader announcements
 * - Keyboard navigation helpers
 */
import { ref, onMounted, onUnmounted, nextTick } from 'vue';

// Live region for screen reader announcements
let announcer: HTMLElement | null = null;

function getOrCreateAnnouncer(): HTMLElement {
  if (announcer && document.body.contains(announcer)) {
    return announcer;
  }

  announcer = document.createElement('div');
  announcer.id = 'a11y-announcer';
  announcer.setAttribute('role', 'status');
  announcer.setAttribute('aria-live', 'polite');
  announcer.setAttribute('aria-atomic', 'true');
  Object.assign(announcer.style, {
    position: 'absolute',
    width: '1px',
    height: '1px',
    padding: '0',
    margin: '-1px',
    overflow: 'hidden',
    clip: 'rect(0, 0, 0, 0)',
    whiteSpace: 'nowrap',
    border: '0'
  });
  document.body.appendChild(announcer);
  
  return announcer;
}

/**
 * Announce message to screen readers
 */
export function announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
  const el = getOrCreateAnnouncer();
  el.setAttribute('aria-live', priority);
  
  // Clear and set message (ensures it's announced even if same)
  el.textContent = '';
  requestAnimationFrame(() => {
    el.textContent = message;
  });
}

/**
 * Focus trap for modals/dialogs
 */
export function useFocusTrap(containerRef: { value: HTMLElement | null }) {
  const previousActiveElement = ref<HTMLElement | null>(null);
  
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]'
  ].join(', ');

  function getFocusableElements(): HTMLElement[] {
    if (!containerRef.value) return [];
    return Array.from(containerRef.value.querySelectorAll<HTMLElement>(focusableSelectors))
      .filter(el => el.offsetParent !== null); // Visible elements only
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key !== 'Tab') return;
    
    const focusable = getFocusableElements();
    if (focusable.length === 0) return;

    const firstFocusable = focusable[0];
    const lastFocusable = focusable[focusable.length - 1];

    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstFocusable) {
        event.preventDefault();
        lastFocusable.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastFocusable) {
        event.preventDefault();
        firstFocusable.focus();
      }
    }
  }

  function activate() {
    previousActiveElement.value = document.activeElement as HTMLElement;
    
    nextTick(() => {
      const focusable = getFocusableElements();
      if (focusable.length > 0) {
        focusable[0].focus();
      } else if (containerRef.value) {
        containerRef.value.focus();
      }
    });

    document.addEventListener('keydown', handleKeyDown);
  }

  function deactivate() {
    document.removeEventListener('keydown', handleKeyDown);
    
    if (previousActiveElement.value && previousActiveElement.value.focus) {
      previousActiveElement.value.focus();
    }
  }

  return {
    activate,
    deactivate,
    getFocusableElements
  };
}

/**
 * Focus management for modals
 */
export function useModalFocus(isOpen: { value: boolean }, modalRef: { value: HTMLElement | null }) {
  const { activate, deactivate } = useFocusTrap(modalRef);

  function handleEscape(event: KeyboardEvent) {
    if (event.key === 'Escape' && isOpen.value) {
      // Emit close event - caller should handle this
      event.preventDefault();
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', handleEscape);
  });

  onUnmounted(() => {
    document.removeEventListener('keydown', handleEscape);
    if (isOpen.value) {
      deactivate();
    }
  });

  return {
    activateFocusTrap: activate,
    deactivateFocusTrap: deactivate
  };
}

/**
 * Keyboard navigation for lists/grids
 */
export function useArrowKeyNavigation(
  items: { value: HTMLElement[] | NodeListOf<HTMLElement> },
  options: {
    loop?: boolean;
    orientation?: 'horizontal' | 'vertical' | 'both';
  } = {}
) {
  const { loop = true, orientation = 'both' } = options;

  function handleKeyDown(event: KeyboardEvent) {
    const itemsList = Array.from(items.value);
    const currentIndex = itemsList.findIndex(el => el === document.activeElement);
    if (currentIndex === -1) return;

    let nextIndex = currentIndex;

    switch (event.key) {
      case 'ArrowUp':
        if (orientation !== 'horizontal') {
          nextIndex = currentIndex - 1;
          event.preventDefault();
        }
        break;
      case 'ArrowDown':
        if (orientation !== 'horizontal') {
          nextIndex = currentIndex + 1;
          event.preventDefault();
        }
        break;
      case 'ArrowLeft':
        if (orientation !== 'vertical') {
          nextIndex = currentIndex - 1;
          event.preventDefault();
        }
        break;
      case 'ArrowRight':
        if (orientation !== 'vertical') {
          nextIndex = currentIndex + 1;
          event.preventDefault();
        }
        break;
      case 'Home':
        nextIndex = 0;
        event.preventDefault();
        break;
      case 'End':
        nextIndex = itemsList.length - 1;
        event.preventDefault();
        break;
      default:
        return;
    }

    // Handle looping
    if (loop) {
      if (nextIndex < 0) nextIndex = itemsList.length - 1;
      if (nextIndex >= itemsList.length) nextIndex = 0;
    } else {
      nextIndex = Math.max(0, Math.min(nextIndex, itemsList.length - 1));
    }

    itemsList[nextIndex]?.focus();
  }

  return { handleKeyDown };
}

/**
 * Skip link for keyboard navigation
 */
export function useSkipLink(targetId: string) {
  function skipToContent() {
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  }

  return { skipToContent };
}

export default {
  announce,
  useFocusTrap,
  useModalFocus,
  useArrowKeyNavigation,
  useSkipLink
};
