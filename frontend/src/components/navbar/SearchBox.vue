<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import type { LocationQueryValue } from 'vue-router';
import { useCatsStore } from '../../store';
import { useDebounce } from '@/composables/useDebounce';
import Search from '../icons/search.vue';

const searchQuery = ref('');
const debouncedSearch = useDebounce(searchQuery, 500); // 500ms debounce
const router = useRouter();
const route = useRoute();
const catsStore = useCatsStore();

// Helper to handle array query params
const getSearchString = (val: LocationQueryValue | LocationQueryValue[]): string => {
  const firstVal = Array.isArray(val) ? val[0] : val;
  return firstVal ?? '';
};

// Initialize search from route query
if (route.query.search) {
  searchQuery.value = getSearchString(route.query.search);
}

// Watch for route changes to update search input
watch(
  () => route.query.search,
  (newSearch) => {
    const searchStr = getSearchString(newSearch);
    if (searchStr !== searchQuery.value) {
      searchQuery.value = searchStr;
    }
  }
);

// Watch debounced search to update store automatically
watch(debouncedSearch, (newValue) => {
  catsStore.setSearchQuery(newValue);

  // Optional: Update URL query param if on map/home without reloading
  if (route.path === '/map' || route.path === '/') {
    const query = { ...route.query };
    if (newValue) {
      query.search = newValue;
    } else {
      delete query.search;
    }
    router.replace({ query });
  }
});

const handleSearch = (): void => {
  // Force navigation if not on map
  if (route.path !== '/map' && route.path !== '/') {
    router.push({ path: '/map', query: { search: searchQuery.value } });
  }
};

const clearSearch = (): void => {
  searchQuery.value = '';
  // Store update will happen via debounce watcher, but we can force it for UI responsiveness if needed
  // But let's let debounce handle it or setting it directly if instant clear is desired.
  // Actually, for clear, we usually want instant.
  catsStore.setSearchQuery('');
};
</script>

<template>
  <div
    class="group/search relative flex items-center gap-2 bg-btn-shade-e border-2 border-btn-shade-a rounded-full py-[0.35rem] pr-[0.35rem] pl-5 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] w-full max-w-[400px] shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.25em_0_0_var(--color-btn-shade-a)] focus-within:bg-white focus-within:shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.35em_0_0_var(--color-btn-shade-a)] focus-within:-translate-y-0.5"
    style="transform-style: preserve-3d"
  >
    <input
      v-model="searchQuery"
      type="text"
      placeholder="Find a spot..."
      class="border-none bg-transparent outline-none font-accent text-[0.9rem] font-medium text-btn-shade-a flex-1 py-1 min-w-0 placeholder-btn-shade-b placeholder:italic placeholder:opacity-100"
      autocomplete="off"
      @keyup.enter="handleSearch"
    />
    <button
      v-if="searchQuery"
      class="group relative w-8 h-8 rounded-full border-2 cursor-pointer flex items-center justify-center transition-all duration-[175ms] ease-[cubic-bezier(0,0,1,1)] shrink-0 active:translate-y-[0.2em] hover:translate-y-[0.1em] bg-[#ffcccc] border-[#dc4a4a] text-[#dc4a4a] hover:bg-[#ffbbbb]"
      style="transform-style: preserve-3d"
      aria-label="Clear search"
      @click="clearSearch"
    >
      <span
        class="absolute inset-0 rounded-[inherit] transition-all duration-[175ms] ease-[cubic-bezier(0,0,1,1)] group-hover:translate-y-[0.2em] group-active:translate-y-0 group-active:translate-z-[-1em] bg-[#ffaaaa] shadow-[0_0_0_2px_#f5a5a5,_0_0.2em_0_0_#dc4a4a] group-active:shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.05em_0_0_var(--color-btn-shade-b)]"
        style="transform: translate3d(0, 0.2em, -1em)"
      ></span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="relative z-10"
      >
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>
    <button
      v-else
      class="group relative w-8 h-8 rounded-full border-2 cursor-pointer flex items-center justify-center transition-all duration-[175ms] ease-[cubic-bezier(0,0,1,1)] shrink-0 active:translate-y-[0.2em] hover:translate-y-[0.1em] bg-btn-shade-d border-btn-shade-a hover:bg-[var(--color-btn-shade-c)]"
      style="transform-style: preserve-3d"
      aria-label="Search"
      @click="handleSearch"
    >
      <span
        class="absolute inset-0 rounded-[inherit] transition-all duration-[175ms] ease-[cubic-bezier(0,0,1,1)] group-hover:translate-y-[0.2em] group-active:translate-y-0 group-active:translate-z-[-1em] bg-btn-shade-c shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.2em_0_0_var(--color-btn-shade-a)] group-active:shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.05em_0_0_var(--color-btn-shade-b)]"
        style="transform: translate3d(0, 0.2em, -1em)"
      ></span>
      <Search class="w-4 h-4 text-btn-shade-a relative z-10" />
    </button>
  </div>
</template>
