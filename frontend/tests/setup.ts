import { config } from '@vue/test-utils';
import { vi } from 'vitest';

console.log('Vitest Setup Loaded');

import { createI18n } from 'vue-i18n';

// Avoid JSDOM attempting to load static assets warnings (if any)
config.global.stubs = {
  'router-link': true,
  'router-view': true,
  'i18n-t': { template: '<span class="i18n-stub"><slot /></span>' },
};

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en: {} },
  missingWarn: false,
  fallbackWarn: false
});

config.global.plugins = [i18n];
config.global.mocks = {
  $t: (msg: string) => msg
};

// Mock intersection observer if used
const IntersectionObserverMock = vi.fn(function() {
  return {
    disconnect: vi.fn(),
    observe: vi.fn(),
    takeRecords: vi.fn(),
    unobserve: vi.fn(),
  };
});

vi.stubGlobal('IntersectionObserver', IntersectionObserverMock);

// Mock window.scrollTo
vi.stubGlobal('scrollTo', vi.fn());

// Mock ResizeObserver
vi.stubGlobal('ResizeObserver', vi.fn(function() {
  return {
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  };
}));
