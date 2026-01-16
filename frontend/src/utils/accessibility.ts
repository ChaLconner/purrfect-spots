/**
 * Accessibility Utilities
 * 
 * Helper functions for improving accessibility throughout the application.
 */

/**
 * Announce a message to screen readers using ARIA live regions
 */
export function announceToScreenReader(
  message: string, 
  priority: 'polite' | 'assertive' = 'polite'
): void {
  const announcer = document.getElementById('sr-announcer') || createAnnouncer();
  announcer.setAttribute('aria-live', priority);
  
  // Clear and set message to trigger announcement
  announcer.textContent = '';
  requestAnimationFrame(() => {
    announcer.textContent = message;
  });
}

/**
 * Create the screen reader announcer element if it doesn't exist
 */
function createAnnouncer(): HTMLElement {
  const announcer = document.createElement('div');
  announcer.id = 'sr-announcer';
  announcer.setAttribute('aria-live', 'polite');
  announcer.setAttribute('aria-atomic', 'true');
  announcer.className = 'sr-only';
  announcer.style.cssText = `
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  `;
  document.body.appendChild(announcer);
  return announcer;
}

/**
 * Trap focus within an element (useful for modals)
 */
export function trapFocus(element: HTMLElement): () => void {
  const focusableElements = element.querySelectorAll<HTMLElement>(
    'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];
  
  function handleKeyDown(e: KeyboardEvent) {
    if (e.key !== 'Tab') return;
    
    if (e.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstFocusable) {
        lastFocusable?.focus();
        e.preventDefault();
      }
    } else {
      // Tab
      if (document.activeElement === lastFocusable) {
        firstFocusable?.focus();
        e.preventDefault();
      }
    }
  }
  
  element.addEventListener('keydown', handleKeyDown);
  firstFocusable?.focus();
  
  // Return cleanup function
  return () => {
    element.removeEventListener('keydown', handleKeyDown);
  };
}

/**
 * Skip to main content functionality
 */
export function setupSkipLink(): void {
  const skipLink = document.getElementById('skip-to-main');
  const mainContent = document.getElementById('main-content') || document.querySelector('main');
  
  if (skipLink && mainContent) {
    skipLink.addEventListener('click', (e) => {
      e.preventDefault();
      (mainContent as HTMLElement).focus();
      mainContent.scrollIntoView({ behavior: 'smooth' });
    });
  }
}

/**
 * Check if reduced motion is preferred
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Check if high contrast is preferred
 */
export function prefersHighContrast(): boolean {
  return window.matchMedia('(prefers-contrast: more)').matches;
}

/**
 * Get color scheme preference
 */
export function getColorSchemePreference(): 'light' | 'dark' | 'no-preference' {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  if (window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light';
  }
  return 'no-preference';
}

/**
 * Generate a unique ID for accessibility purposes
 */
export function generateA11yId(prefix: string = 'a11y'): string {
  return `${prefix}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Check if an element is visible to screen readers
 */
export function isVisibleToScreenReader(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);
  
  // Check if hidden via CSS
  if (style.display === 'none' || style.visibility === 'hidden') {
    return false;
  }
  
  // Check aria-hidden
  if (element.getAttribute('aria-hidden') === 'true') {
    return false;
  }
  
  // Check if off-screen
  const rect = element.getBoundingClientRect();
  if (rect.width === 0 && rect.height === 0) {
    // Could be sr-only element, check if it has text
    return element.textContent?.trim().length > 0;
  }
  
  return true;
}

/**
 * Add keyboard navigation to a list of items
 */
export function setupArrowKeyNavigation(
  container: HTMLElement,
  itemSelector: string,
  options: { vertical?: boolean; wrap?: boolean } = {}
): () => void {
  const { vertical = true, wrap = true } = options;
  
  function handleKeyDown(e: KeyboardEvent) {
    const items = Array.from(container.querySelectorAll<HTMLElement>(itemSelector));
    const currentIndex = items.findIndex(item => item === document.activeElement);
    
    if (currentIndex === -1) return;
    
    let nextIndex: number | null = null;
    
    if (vertical) {
      if (e.key === 'ArrowDown') {
        nextIndex = currentIndex + 1;
      } else if (e.key === 'ArrowUp') {
        nextIndex = currentIndex - 1;
      }
    } else {
      if (e.key === 'ArrowRight') {
        nextIndex = currentIndex + 1;
      } else if (e.key === 'ArrowLeft') {
        nextIndex = currentIndex - 1;
      }
    }
    
    // Home and End keys
    if (e.key === 'Home') {
      nextIndex = 0;
    } else if (e.key === 'End') {
      nextIndex = items.length - 1;
    }
    
    if (nextIndex !== null) {
      e.preventDefault();
      
      if (wrap) {
        nextIndex = (nextIndex + items.length) % items.length;
      } else {
        nextIndex = Math.max(0, Math.min(nextIndex, items.length - 1));
      }
      
      items[nextIndex]?.focus();
    }
  }
  
  container.addEventListener('keydown', handleKeyDown);
  
  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
}
