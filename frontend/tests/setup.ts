
import { config } from '@vue/test-utils';
import { vi } from 'vitest';



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
  $t: (msg: string): string => msg
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

// Stub Image class for Node/JSDOM to prevent loading static public assets which fail with path error
vi.stubGlobal('Image', class {
  _src = '';
  onload: () => void = (): void => {};
  onerror: () => void = (): void => {};
  height = 0;
  width = 0;
  set src(val: string) {
    this._src = val;
    // Simulate async load
    setTimeout(() => {
        if (typeof this.onload === 'function') {
            this.onload();
        }
    }, 0);
  }
  get src(): string { return this._src; }
});

// Mock URL.createObjectURL and URL.revokeObjectURL
if (typeof URL !== 'undefined') {
  URL.createObjectURL = vi.fn(() => 'blob:mock-url');
  URL.revokeObjectURL = vi.fn();
} else {
  vi.stubGlobal('URL', {
    createObjectURL: vi.fn(() => 'blob:mock-url'),
    revokeObjectURL: vi.fn(),
  });
}
