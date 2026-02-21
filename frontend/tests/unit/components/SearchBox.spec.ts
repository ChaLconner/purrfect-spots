import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import SearchBox from '@/components/navbar/SearchBox.vue';
import { createPinia, setActivePinia } from 'pinia';
import { useCatsStore } from '@/store/catsStore';
import { useRouter, useRoute } from 'vue-router';
import { ref, reactive, nextTick } from 'vue';

// Mock dependencies
vi.mock('vue-router', () => ({
  useRouter: vi.fn(),
  useRoute: vi.fn(),
}));

// Mock useDebounce to behave appropriately
// Typically useDebounce returns a ref that updates after delay.
// For testing, we can implement a fake one or just pass through if we want instant.
// Let's implement a fake that we can control or just one that syncs immediately for simplicity in most tests,
// but the component relies on the debounce return value to update the store.
// If we return the source ref, it works like no debounce.
vi.mock('@/composables/useDebounce', () => ({
  useDebounce: (val: any) => val,
}));

describe('SearchBox.vue', () => {
  let mockRouter: { push: ReturnType<typeof vi.fn>; replace: ReturnType<typeof vi.fn> };
  let mockRoute: any;

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();

    mockRouter = {
      push: vi.fn(),
      replace: vi.fn(),
    };
    
    // Make route reactive
    mockRoute = reactive({
      query: {},
      path: '/',
    });

    (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
    (useRoute as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockRoute);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('should initialize search from route query', () => {
    mockRoute.query.search = 'cat';
    const wrapper = mount(SearchBox);
    const input = wrapper.find('input');
    expect(input.element.value).toBe('cat');
  });

  it('should update search input when route query changes', async () => {
    const wrapper = mount(SearchBox);
    const input = wrapper.find('input');
    
    mockRoute.query.search = 'new search';
    await nextTick();
    
    expect(input.element.value).toBe('new search');
  });

  it('should update store and router when typing', async () => {
    const wrapper = mount(SearchBox);
    const store = useCatsStore();
    const input = wrapper.find('input');

    await input.setValue('typing');
    // Since useDebounce is mocked to pass-through, it should trigger watch immediately
    await nextTick();

    // Check state instead of spy
    expect(store.searchQuery).toBe('typing');
    // It also tries to replace route if on map/home
    expect(mockRouter.replace).toHaveBeenCalledWith(expect.objectContaining({
      query: { search: 'typing' }
    }));
  });

  it('should navigate to map on enter', async () => {
    mockRoute.path = '/profile'; // Ensure we are not on map or home
    const wrapper = mount(SearchBox);
    const input = wrapper.find('input');
    await input.setValue('go map');
    
    await input.trigger('keyup.enter');
    
    expect(mockRouter.push).toHaveBeenCalledWith({
      path: '/map',
      query: { search: 'go map' }
    });
  });

  it('should clear search', async () => {
    mockRoute.query.search = 'initial';
    const wrapper = mount(SearchBox);
    const input = wrapper.find('input');
    
    expect(input.element.value).toBe('initial');
    
    // Find clear button (only shows when query exists)
    const clearBtn = wrapper.find('button[aria-label="Clear search"]');
    expect(clearBtn.exists()).toBe(true);
    
    await clearBtn.trigger('click');
    
    expect(input.element.value).toBe('');
    expect(useCatsStore().searchQuery).toBe('');
  });

  it('should handle array query params (use first)', async () => {
    mockRoute.query.search = ['first', 'second'];
    const wrapper = mount(SearchBox);
    const input = wrapper.find('input');
    
    // Should align with useRoute logic (usually auto-handles, but if manual check exists)
    // If component uses route.query.search string it might be array.
    // If we expect it to handle array gracefully (e.g. take first).
    expect(input.element.value).toBe('first'); 
  });
});
