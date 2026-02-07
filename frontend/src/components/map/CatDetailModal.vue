<template>
  <transition
    enter-active-class="transition-all duration-300 ease-out"
    leave-active-class="transition-all duration-200 ease-in"
    enter-from-class="opacity-0 scale-95"
    leave-to-class="opacity-0 scale-95"
  >
    <div
      v-if="cat"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click="$emit('close')"
    >
      <div class="modal-container" @click.stop>
        <!-- Image with gradient overlay -->
        <div class="relative h-64">
          <img
            :src="cat.image_url"
            :alt="cat.location_name || 'Cat'"
            class="w-full h-full object-cover"
            loading="lazy"
            decoding="async"
          />
          <div
            class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"
          ></div>

          <!-- Close button (3D Style) -->
          <button class="close-btn-3d" aria-label="Close" @click="$emit('close')">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="w-5 h-5"
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

          <!-- Location badge (3D Style) -->
          <div class="absolute bottom-4 left-4">
            <span class="location-badge-3d">
              {{ cat.location_name }}
            </span>
          </div>
        </div>

        <!-- Content -->
        <div class="p-6 pt-5">
          <div class="text-center mb-6">
            <h3 class="modal-title">Cat Spotted!</h3>
            <p class="modal-subtitle">Click direction for navigation</p>
          </div>

          <!-- Description Box (3D Style) -->
          <div class="description-box-3d">
            <p class="description-text">
              {{ cleanDescription || 'A lovely cat was spotted here.' }}
            </p>
          </div>

          <!-- Tags (3D pills) -->
          <div v-if="tags.length > 0" class="flex flex-wrap gap-2 justify-center mb-6">
            <button
              v-for="tag in tags"
              :key="tag"
              class="tag-btn-3d"
              @click="$emit('tag-click', tag)"
            >
              #{{ tag }}
            </button>
          </div>

          <!-- Action button (3D Style) -->
          <div class="flex flex-col gap-3 mt-4">
            <button class="directions-btn-3d" @click="$emit('get-directions', cat)">
              GET DIRECTIONS
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { CatLocation } from '@/types/api';
import { extractTags, getCleanDescription } from '@/store/catsStore';

const props = defineProps<{
  cat: CatLocation | null;
}>();

defineEmits<{
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
</script>

<style scoped>
/* 3D Modal Container */
.modal-container {
  position: relative;
  max-width: 24rem;
  width: 100%;
  background: var(--color-btn-shade-e);
  border: 3px solid var(--color-btn-shade-a);
  border-radius: 1.5rem;
  overflow: hidden;
  box-shadow:
    0 0 0 3px var(--color-btn-shade-b),
    0 0.6em 0 0 var(--color-btn-shade-a);
  transform: translateY(-0.3em);
}

/* 3D Close Button */
.close-btn-3d {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 2.25rem;
  height: 2.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-btn-accent-e);
  border: 2px solid var(--color-btn-accent-a);
  border-radius: 50%;
  color: var(--color-btn-accent-a);
  cursor: pointer;
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
  z-index: 10;
}

.close-btn-3d::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-accent-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-accent-b),
    0 0.2em 0 0 var(--color-btn-accent-a);
  transform: translate3d(0, 0.2em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.close-btn-3d:hover {
  background: var(--color-btn-accent-d);
  transform: translate(0, 0.1em);
}

.close-btn-3d:active {
  transform: translate(0, 0.2em);
}

.close-btn-3d:active::before {
  transform: translate3d(0, 0, -1em);
}

.close-btn-3d svg {
  position: relative;
  z-index: 1;
}

/* 3D Location Badge */
.location-badge-3d {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 2rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-btn-shade-a);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.2em 0 0 var(--color-btn-shade-a);
}

/* Modal Typography */
.modal-title {
  font-family: 'Quicksand', sans-serif;
  font-weight: 800;
  font-size: 1.5rem;
  color: var(--color-btn-brown-b);
  margin-bottom: 0.25rem;
}

.modal-subtitle {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-btn-shade-b);
}

/* 3D Description Box */
.description-box-3d {
  position: relative;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  background: var(--color-btn-lavender-e);
  border: 2px solid var(--color-btn-lavender-a);
  border-radius: 1rem;
  box-shadow:
    0 0 0 2px var(--color-btn-lavender-b),
    0 0.25em 0 0 var(--color-btn-lavender-a);
}

.description-text {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-btn-lavender-a);
  text-align: center;
  line-height: 1.6;
}

/* 3D Tag Buttons */
.tag-btn-3d {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 0.375rem 0.75rem;
  background: var(--color-btn-sky-e);
  border: 2px solid var(--color-btn-sky-a);
  border-radius: 2rem;
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-btn-sky-a);
  cursor: pointer;
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.tag-btn-3d::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-sky-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-sky-b),
    0 0.2em 0 0 var(--color-btn-sky-a);
  transform: translate3d(0, 0.2em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.tag-btn-3d:hover {
  background: var(--color-btn-sky-d);
  transform: translate(0, 0.1em);
}

.tag-btn-3d:active {
  transform: translate(0, 0.2em);
}

.tag-btn-3d:active::before {
  transform: translate3d(0, 0, -1em);
}

/* 3D Directions Button */
.directions-btn-3d {
  position: relative;
  width: 100%;
  padding: 1rem;
  background: var(--color-btn-accent-e);
  border: 3px solid var(--color-btn-accent-a);
  border-radius: 1rem;
  font-family: 'Quicksand', sans-serif;
  font-size: 1rem;
  font-weight: 800;
  color: var(--color-btn-accent-a);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transform-style: preserve-3d;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.directions-btn-3d::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-accent-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 3px var(--color-btn-accent-b),
    0 0.4em 0 0 var(--color-btn-accent-a);
  transform: translate3d(0, 0.4em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
}

.directions-btn-3d:hover {
  background: var(--color-btn-accent-d);
  transform: translate(0, 0.2em);
}

.directions-btn-3d:active {
  transform: translate(0, 0.4em);
}

.directions-btn-3d:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 3px var(--color-btn-accent-b),
    0 0.1em 0 0 var(--color-btn-accent-b);
}
</style>
