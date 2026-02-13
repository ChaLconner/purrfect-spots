<template>
  <transition
    enter-active-class="transition-all duration-500 ease-out"
    leave-active-class="transition-all duration-300 ease-in"
    enter-from-class="opacity-0 translate-x-full"
    leave-to-class="opacity-0 translate-x-12"
  >
    <div
      v-if="cat"
      class="fixed inset-0 z-[100] flex justify-end items-stretch pointer-events-auto"
      @click="$emit('close')"
    >
      <div class="minimal-panel w-full max-w-[450px]" @click.stop>
        <!-- Close Action (Top Corner) -->
        <button class="close-x-btn" aria-label="Close" @click="$emit('close')">
          <svg
            viewBox="0 0 24 24"
            width="24"
            height="24"
            stroke="currentColor"
            stroke-width="2.5"
            fill="none"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <div class="panel-inner custom-scrollbar">
          <!-- Image Section -->
          <div class="image-wrapper">
            <img
              :src="cat.image_url"
              :alt="cat.location_name || 'Cat'"
              class="main-image"
              loading="lazy"
            />
          </div>

          <!-- Content Section -->
          <div class="details-section">
            <div class="location-label">
              {{ cat.location_name }}
            </div>

            <h2 class="cat-name">Cat Spotted!</h2>

            <div class="description-text font-zen-maru">
              {{ cleanDescription || 'A beautiful cat was found at this location.' }}
            </div>

            <div v-if="tags.length > 0" class="tags-row">
              <span v-for="tag in tags" :key="tag" class="tag-text">#{{ tag }}</span>
            </div>
          </div>
        </div>

        <!-- Footer Action -->
        <div class="footer-action">
          <button class="elegant-btn" @click="$emit('get-directions', cat)">GET DIRECTIONS</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue';
import type { CatLocation } from '@/types/api';
import { extractTags, getCleanDescription } from '@/store/catsStore';

const props = defineProps<{
  cat: CatLocation | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'tag-click', tag: string): void;
  (e: 'get-directions', cat: CatLocation): void;
}>();

const cleanDescription = computed(() => {
  if (!props.cat) return '';
  const desc = getCleanDescription(props.cat.description);
  return desc === '-' ? '' : desc;
});

const tags = computed(() => {
  if (!props.cat) return [];
  return extractTags(props.cat.description);
});

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    emit('close');
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.minimal-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: calc(100vh - 3rem);
  margin: 1.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 1.5rem;
  box-shadow: -10px 20px 40px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

/* Close Button - Simple X */
.close-x-btn {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  z-index: 20;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: none;
  border: none;
  cursor: pointer;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  transition: opacity 0.2s;
}

.close-x-btn:hover {
  opacity: 0.7;
}

.panel-inner {
  flex-grow: 1;
  overflow-y: auto;
}

/* Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f3f4f6;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #f3f4f6;
  border-radius: 10px;
}

/* Image */
.image-wrapper {
  width: 100%;
  aspect-ratio: 1/1;
  overflow: hidden;
}

.main-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Content */
.details-section {
  padding: 2rem;
}

.location-label {
  font-family: 'Quicksand', sans-serif;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--color-sage);
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.cat-name {
  font-family: 'Quicksand', sans-serif;
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-brown-dark);
  margin-bottom: 1.5rem;
  line-height: 1.2;
}

.description-text {
  font-size: 1rem;
  line-height: 1.6;
  color: #4b5563;
  margin-bottom: 1.5rem;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.tag-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: #9ca3af;
}

/* Action Button */
.footer-action {
  padding: 2rem;
  padding-top: 0;
}

.elegant-btn {
  width: 100%;
  padding: 1.25rem;
  background: var(--color-brown);
  border: none;
  border-radius: 1rem;
  color: white;
  font-family: 'Quicksand', sans-serif;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.3s ease;
}

.elegant-btn:hover {
  background: var(--color-brown-dark);
  box-shadow: 0 10px 20px rgba(139, 77, 45, 0.2);
  transform: translateY(-2px);
}

.elegant-btn:active {
  transform: translateY(0);
}

@media (max-width: 640px) {
  .minimal-panel {
    margin: 0;
    height: 100vh;
    border-radius: 0;
    max-width: 100%;
  }
}
</style>
