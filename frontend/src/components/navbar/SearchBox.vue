<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useCatsStore } from '../../store';
import Search from '../icons/search.vue';

const searchQuery = ref('');
const router = useRouter();
const route = useRoute();
const catsStore = useCatsStore();

// Initialize search from route query
if (route.query.search) {
  searchQuery.value = route.query.search as string;
}

// Watch for route changes to update search
watch(
  () => route.query.search,
  (newSearch) => {
    if (newSearch) {
      searchQuery.value = newSearch as string;
    }
  }
);

const handleSearch = () => {
  catsStore.setSearchQuery(searchQuery.value);

  if (route.path !== '/map' && route.path !== '/') {
    router.push({ path: '/map', query: { search: searchQuery.value } });
  }
};

watch(searchQuery, (newValue) => {
  if (!newValue.trim()) {
    catsStore.setSearchQuery('');
  }
});

const clearSearch = () => {
  searchQuery.value = '';
  catsStore.setSearchQuery('');
  if (route.path === '/map') {
    // Update URL without reloading if on map
    router.replace({ ...route, query: { ...route.query, search: undefined } });
  }
};
</script>

<template>
  <div class="search-box">
    <input
      v-model="searchQuery"
      type="text"
      placeholder="Find a spot..."
      class="search-input"
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #fffdf5;
  border: 2px solid rgba(139, 90, 43, 0.1);
  border-radius: 2rem;
  padding: 0.35rem 0.35rem 0.35rem 1.25rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  width: 100%;
  box-shadow: 0 2px 8px rgba(139, 90, 43, 0.03);
}

.search-box:focus-within {
  border-color: #d4845a;
  background: #fff;
  box-shadow:
    0 4px 12px rgba(212, 132, 90, 0.15),
    inset 0 1px 2px rgba(139, 90, 43, 0.05);
  transform: translateY(-1px);
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
  color: #5a4a3a;
  flex: 1;
  padding: 0.2rem 0;
  min-width: 0;
}

.search-input::placeholder {
  color: #b0a090;
  font-style: italic;
  opacity: 0.8;
}

.search-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #f5a962 0%, #e89445 100%);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(232, 148, 69, 0.3);
}

.search-btn:hover {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 4px 10px rgba(232, 148, 69, 0.5);
  background: linear-gradient(135deg, #fbbd7e 0%, #f5a962 100%);
}

.search-btn.clear-mode {
  background: linear-gradient(135deg, #d47979 0%, #c96262 100%);
  box-shadow: 0 2px 6px rgba(201, 98, 98, 0.3);
  color: white;
}

.search-btn.clear-mode:hover {
  transform: scale(1.1) rotate(-5deg);
  box-shadow: 0 4px 10px rgba(201, 98, 98, 0.5);
  background: linear-gradient(135deg, #e08888 0%, #d47979 100%);
}

.search-icon {
  width: 1rem;
  height: 1rem;
  color: white;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}
</style>
