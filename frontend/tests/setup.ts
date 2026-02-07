import { config } from '@vue/test-utils';
import { vi } from 'vitest';

console.log('Vitest Setup Loaded');

// Stub img tag globally to avoid JSDOM attempting to load static assets
config.global.stubs = {
  img: { template: '<div class="img-stub"></div>' },
  'router-link': true,
  'router-view': true,
};

// Mock intersection observer if used
const IntersectionObserverMock = vi.fn(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  takeRecords: vi.fn(),
  unobserve: vi.fn(),
}));

vi.stubGlobal('IntersectionObserver', IntersectionObserverMock);

// Mock window.scrollTo
vi.stubGlobal('scrollTo', vi.fn());

// Mock ResizeObserver
vi.stubGlobal('ResizeObserver', vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
})));
