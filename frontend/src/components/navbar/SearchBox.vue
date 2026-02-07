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

const handleSearch = () => {
  // Force navigation if not on map
  if (route.path !== '/map' && route.path !== '/') {
    router.push({ path: '/map', query: { search: searchQuery.value } });
  }
};

const clearSearch = () => {
  searchQuery.value = '';
  // Store update will happen via debounce watcher, but we can force it for UI responsiveness if needed
  // But let's let debounce handle it or setting it directly if instant clear is desired.
  // Actually, for clear, we usually want instant.
  catsStore.setSearchQuery('');
};
</script>

<template>
  <div class="search-box">
    <input
      v-model="searchQuery"
      type="text"
      placeholder="Find a spot..."
      class="search-input"
      autocomplete="off"
      @keyup.enter="handleSearch"
    />
    <button
      v-if="searchQuery"
      class="search-btn clear-mode"
      aria-label="Clear search"
      @click="clearSearch"
    >
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
      >
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>
    <button v-else class="search-btn" aria-label="Search" @click="handleSearch">
      <Search class="search-icon" />
    </button>
  </div>
</template>

<style scoped>
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 2rem;
  padding: 0.35rem 0.35rem 0.35rem 1.25rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  width: 100%;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.25em 0 0 var(--color-btn-shade-a);
  transform-style: preserve-3d;
}

.search-box:focus-within {
  background: #fff;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.35em 0 0 var(--color-btn-shade-a);
  transform: translateY(-2px);
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-btn-shade-a);
  flex: 1;
  padding: 0.2rem 0;
  min-width: 0;
}

.search-input::placeholder {
  color: var(--color-btn-shade-b);
  font-style: italic;
  opacity: 1;
}

/* 3D Search Button */
.search-btn {
  position: relative;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: var(--color-btn-shade-d);
  border: 2px solid var(--color-btn-shade-a);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
  flex-shrink: 0;
  transform-style: preserve-3d;
}

.search-btn::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-shade-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.2em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.2em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.search-btn:hover {
  background: var(--color-btn-shade-c);
  transform: translate(0, 0.1em);
}

.search-btn:hover::before {
  transform: translate3d(0, 0.2em, -1em);
}

.search-btn:active {
  transform: translate(0, 0.2em);
}

.search-btn:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.05em 0 0 var(--color-btn-shade-b);
}

/* Clear mode - red theme */
.search-btn.clear-mode {
  background: #ffcccc;
  border-color: #dc4a4a;
  color: #dc4a4a;
}

.search-btn.clear-mode::before {
  background: #ffaaaa;
  box-shadow:
    0 0 0 2px #f5a5a5,
    0 0.2em 0 0 #dc4a4a;
}

.search-btn.clear-mode:hover {
  background: #ffbbbb;
}

.search-icon {
  width: 1rem;
  height: 1rem;
  color: var(--color-btn-shade-a);
  position: relative;
  z-index: 1;
}
</style>
