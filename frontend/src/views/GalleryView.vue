<template>
  <div class="gallery-page min-h-screen relative overflow-x-hidden">
    <GhibliBackground />

    <div class="gallery-container max-w-7xl mx-auto py-2 px-1 sm:px-2 lg:px-4">
      <!-- Ghibli Style Header with Search -->
      <GalleryHeader />

      <!-- Mint Green Theme Container -->
      <!-- Clean Container (Removed Mint Frame) -->
      <div class="gallery-mint-container p-0 min-h-[600px] w-full relative z-[5]">
        <!-- Gallery Stats Removed -->

        <!-- Loading state -->
        <div v-if="loading" class="loading-container" role="status" aria-live="polite">
          <GhibliLoader text="Finding cute cats..." />
        </div>

        <!-- Error state -->
        <ErrorState v-else-if="error" :message="error" @retry="fetchImages" />

        <!-- Empty state -->
        <EmptyState
          v-else-if="visibleImages.length === 0"
          title="A Quiet Spot"
          message="No photos have been discovered here yet."
          sub-message="Be the first to share a moment in this collection."
          action-text="Upload Photo"
          action-link="/upload"
        />

        <!-- Virtual Scroller Gallery -->
        <div v-else class="gallery-content">
          <DynamicScroller :items="chunkedImages" :min-item-size="200" class="scroller" page-mode>
            <template #default="{ item, index, active }">
              <DynamicScrollerItem
                :item="item"
                :active="active"
                :size-dependencies="[item.images.length, windowWidth]"
                :data-index="index"
              >
                <div class="gallery-grid" role="grid" aria-label="Cat photo gallery chunk">
                  <div
                    v-for="(image, subIndex) in item.images"
                    :key="image.id"
                    class="gallery-item"
                    :class="[
                      getBentoClass(item.index + subIndex),
                      { 'item-loaded': loadedImages[image.id] },
                    ]"
                    :style="{ 'animation-delay': `${(subIndex % 10) * 0.05}s` }"
                    role="gridcell"
                    tabindex="0"
                    :aria-label="`View photo: ${image.location_name || 'Cat photo'}`"
                    @click="openModal(image, item.index + subIndex)"
                    @keydown.enter="openModal(image, item.index + subIndex)"
                    @keydown.space.prevent="openModal(image, item.index + subIndex)"
                  >
                    <!-- Glass-framed Image Card -->
                    <div class="image-card">
                      <!-- Placeholder -->
                      <div
                        v-if="!loadedImages[image.id]"
                        class="image-placeholder h-full w-full"
                        aria-hidden="true"
                      >
                        <div class="placeholder-content">
                          <div class="soot-dot"></div>
                        </div>
                      </div>

                      <!-- Actual Image with native lazy loading -->
                      <div class="image-wrapper">
                        <img
                          loading="lazy"
                          :src="image.image_url"
                          :alt="image.location_name || 'Cat photo'"
                          class="gallery-image shadow-md"
                          :class="{ 'image-visible': loadedImages[image.id] }"
                          @load="handleImageLoad(image.id)"
                          @error="handleImageError"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </DynamicScrollerItem>
            </template>
          </DynamicScroller>
          <!-- Load More -->
          <div
            v-if="hasMoreImages && !loadingMore"
            ref="loadMoreTrigger"
            class="load-more h-4 w-full"
            aria-hidden="true"
          ></div>
          <div
            v-if="loadingMore"
            class="py-4 flex justify-center w-full"
            role="status"
            aria-live="polite"
          >
            <GhibliLoader size="small" />
          </div>
        </div>
      </div>

      <!-- Modal -->
      <GalleryModal
        :image="selectedImage"
        :images="modalImages"
        :current-index="modalCurrentIndex"
        :total-images="modalTotalImages"
        @close="closeModal"
        @navigate="handleModalNavigate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch, onErrorCaptured, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { GalleryService } from '@/services/galleryService';
import { isDev } from '@/utils/env';
import { IMAGE_CONFIG, GALLERY_CONFIG } from '@/utils/constants';
import GalleryHeader from '@/components/gallery/GalleryHeader.vue';
import { useCatsStore } from '@/store';
import type { CatLocation } from '@/types/api';

import GalleryModal from '@/components/gallery/GalleryModal.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import ErrorState from '@/components/ui/ErrorState.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useSeo } from '@/composables/useSeo';
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';

// SEO
const { setMetaTags, resetMetaTags } = useSeo();

const props = defineProps<{
  id?: string;
}>();

// Handle browser extension errors
onErrorCaptured((err: unknown) => {
  if (
    err instanceof Error &&
    err.message &&
    (err.message.includes('message channel closed') ||
      err.message.includes(
        'asynchronous response by returning true, but the message channel closed'
      ) ||
      err.message.includes(
        'A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received'
      ) ||
      err.message.includes('ResizeObserver loop')) // Common with virtual scrollers
  ) {
    if (isDev()) {
      console.warn('⚠️ Browser/Extension error caught in Gallery component:', err.message);
    }
    return false;
  }
  return true;
});

const route = useRoute();
const router = useRouter();
const catsStore = useCatsStore();

const loading = ref(true);
const loadingMore = ref(false);
const error = ref('');
const selectedImage = ref<CatLocation | null>(null);
const currentImageIndex = ref(-1);
const loadedImages = ref<Record<string, boolean>>({});
// removed imageElements ref and galleryContainer ref as they are no longer needed
const loadMoreTrigger = ref<HTMLElement | null>(null);
const loadMoreObserver = ref<IntersectionObserver | null>(null);

// Pagination and virtual scrolling
const currentPage = ref(1);
const imagesPerPage = GALLERY_CONFIG.IMAGES_PER_PAGE;
const visibleImages = ref<CatLocation[]>([]);
const hasMoreImages = ref(false);
const totalImages = ref(0); // Track total for modal navigation
const isDeepLinked = ref(false); // Track if current view is a deep link to a specific image

const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024);

const updateWidth = () => {
  windowWidth.value = window.innerWidth;
};

// Determine chunk size based on convenient strict grid alignment (LCM of 2,3,4,5 = 60)
const CHUNK_SIZE = 60;

const chunkedImages = computed(() => {
  const chunks = [];
  for (let i = 0; i < visibleImages.value.length; i += CHUNK_SIZE) {
    chunks.push({
      id: i, // Unique ID for the chunk (based on start index)
      index: i, // Start index for Bento calculation
      images: visibleImages.value.slice(i, i + CHUNK_SIZE),
    });
  }
  return chunks;
});

onMounted(() => {
  window.addEventListener('resize', updateWidth);
  fetchImages();

  // Check for search query in URL on mount
  if (route.query.search) {
    catsStore.setSearchQuery(route.query.search as string);
  }

  // Set SEO meta tags
  setMetaTags({
    title: 'Gallery | Purrfect Spots',
    description:
      'Browse our collection of adorable cat photos from around the world. Find your favorite feline friends and discover cat-friendly locations.',
    type: 'website',
  });
});

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth);

  if (loadMoreObserver.value) {
    loadMoreObserver.value.disconnect();
    loadMoreObserver.value = null;
  }

  // Clear loaded images state completely
  loadedImages.value = {};

  // Reset SEO meta tags
  resetMetaTags();
});

// Watch visibleImages to manage memory and initialization
watch(
  visibleImages,
  () => {
    // Initialize loadedImages for new visible images
    visibleImages.value.forEach((image) => {
      if (!(image.id in loadedImages.value)) {
        loadedImages.value[image.id] = false;
      }
    });
  },
  { deep: false }
);

// Watch for DOM updates to setup load more observer
watch(
  [visibleImages, loadingMore],
  async () => {
    await nextTick();
    setupLoadMoreObserver();
  },
  { deep: false }
);

// Watch search query from store to update URL and fetch data
watch(
  () => catsStore.searchQuery,
  (newQuery) => {
    // Sync URL query param
    const query = { ...route.query };
    if (newQuery) {
      query.search = newQuery;
    } else {
      delete query.search;
    }
    // Replace to avoid cluttering history, preserve path params
    router.replace({ params: route.params, query });

    fetchGalleryData(true);
  }
);

// Watch URL changes to sync modal state (using Path Params now)
watch(
  () => props.id,
  () => {
    syncStateFromUrl();
  }
);

// Watch route query specifically for browser back/forward buttons affecting search
watch(
  () => route.query.search,
  (newSearch) => {
    const term = (newSearch as string) || '';
    if (term !== catsStore.searchQuery) {
      catsStore.setSearchQuery(term);
    }
  }
);

// Computed props for modal to handle both list and deep link scenarios
const modalImages = computed(() => {
  return isDeepLinked.value && selectedImage.value ? [selectedImage.value] : visibleImages.value;
});

const modalTotalImages = computed(() => {
  return isDeepLinked.value ? 1 : totalImages.value;
});

const modalCurrentIndex = computed(() => {
  return isDeepLinked.value ? 0 : currentImageIndex.value;
});

async function syncStateFromUrl() {
  const imageId = props.id;

  if (!imageId) {
    selectedImage.value = null;
    currentImageIndex.value = -1;
    isDeepLinked.value = false;
    document.body.style.overflow = ''; // Ensure scroll is restored
    return;
  }

  // Find the image in current loaded list
  const index = visibleImages.value.findIndex((img) => img.id.toString() === imageId);

  if (index !== -1) {
    selectedImage.value = visibleImages.value[index];
    currentImageIndex.value = index;
    isDeepLinked.value = false;
  } else {
    // If not found in current loaded items, fetch it specifically
    try {
      selectedImage.value = await GalleryService.getPhotoById(imageId);
      currentImageIndex.value = 0; // It's the only image in the modal list
      isDeepLinked.value = true;
    } catch (err: unknown) {
      console.error('Failed to load deep linked image:', err);
      // If failed, clear URL to avoid stuck state
      closeModal();
    }
  }
}

async function fetchGalleryData(reset = false) {
  if (reset) {
    loading.value = true;
    currentPage.value = 1;
    visibleImages.value = [];
    hasMoreImages.value = true;
    totalImages.value = 0;
  } else {
    loadingMore.value = true;
  }

  error.value = '';

  try {
    const query = catsStore.searchQuery;
    let newImages: CatLocation[] = [];
    let hasNext = false;
    let total = 0;

    if (query) {
      // Server-side Search
      const response = await GalleryService.search({
        query,
        limit: 100, // Current backend search limit
      });

      newImages = response.results || [];
      hasNext = false; // Search endpoint doesn't support pagination yet
      total = response.total || newImages.length;
    } else {
      // Server-side Pagination
      const response = await GalleryService.getImages({
        page: currentPage.value,
        limit: imagesPerPage,
      });

      newImages = response.images || [];
      if (response.pagination) {
        hasNext = response.pagination.has_more;
        total = response.pagination.total;
      }
    }

    if (reset) {
      visibleImages.value = newImages;
    } else {
      visibleImages.value.push(...newImages);
    }

    hasMoreImages.value = hasNext;
    if (total > 0) totalImages.value = total;
    else totalImages.value = visibleImages.value.length;

    // Initial sync with URL after data load (only on first load)
    if (reset && props.id) {
      nextTick(() => syncStateFromUrl());
    }
  } catch (err: unknown) {
    const message = (err as Error).message || 'Failed to load images from server';
    error.value = message;
    if (reset) visibleImages.value = [];
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

// Wrapper for initial mounting
function fetchImages() {
  fetchGalleryData(true);
}

function handleImageLoad(id: number | string) {
  loadedImages.value[id] = true;
}

// Removed old setupLazyLoading and simplified loadMoreObserver

function setupLoadMoreObserver() {
  // Clean up previous observer
  if (loadMoreObserver.value) {
    loadMoreObserver.value.disconnect();
  }

  if (!loadMoreTrigger.value || !hasMoreImages.value) return;

  // Create new observer for load more trigger
  loadMoreObserver.value = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && hasMoreImages.value && !loadingMore.value) {
          loadMoreImages();
        }
      });
    },
    {
      rootMargin: GALLERY_CONFIG.LOAD_MORE_ROOT_MARGIN,
      threshold: GALLERY_CONFIG.LAZY_LOAD_THRESHOLD,
    }
  );

  loadMoreObserver.value.observe(loadMoreTrigger.value);
}

function loadMoreImages() {
  if (loadingMore.value || !hasMoreImages.value) return;

  // Increment page and fetch
  currentPage.value++;
  fetchGalleryData(false);
}

function openModal(image: CatLocation, index: number) {
  // Update URL using Path Parameter
  router.push({
    name: 'Gallery',
    params: { id: image.id },
    query: route.query, // Preserve search query
  });
}

function closeModal() {
  // Remove ID from Path
  router.push({
    name: 'Gallery',
    params: { id: '' }, // Empty ID to go back to list
    query: route.query,
  });
}

function handleModalNavigate(direction: 'prev' | 'next') {
  if (isDeepLinked.value) return; // Disable navigation for single deep linked image
  if (currentImageIndex.value < 0) return;

  // currentImageIndex is now the global index in visibleImages
  let newIndex = currentImageIndex.value;

  if (direction === 'prev' && newIndex > 0) {
    newIndex = newIndex - 1;
  } else if (direction === 'next' && newIndex < visibleImages.value.length - 1) {
    newIndex = newIndex + 1;
  }

  if (newIndex !== currentImageIndex.value) {
    const nextImage = visibleImages.value[newIndex];
    if (nextImage) {
      // With infinite scroll, we don't need to jump pages, just ensure it's loaded
      // Since we only navigate within visibleImages, it is by definition loaded

      // Use replace for navigation to allow back button to close modal
      router.replace({
        name: 'Gallery',
        params: { id: nextImage.id },
        query: route.query,
      });
    }
  }
}

function handleImageError(event: Event) {
  const target = event.target as HTMLImageElement;
  target.src = IMAGE_CONFIG.PLACEHOLDER_URL;
}

function getBentoClass(index: number): string {
  // Bento Pattern (Repeats every 12 items)
  // 0: Large (2x2)
  // 7: Wide (2x1)
  const remainder = index % 10;

  if (remainder === 0) return 'col-span-2 row-span-2';
  if (remainder === 6) return 'col-span-2 row-span-1';

  return 'col-span-1 row-span-1';
}
</script>

<style scoped>
/* ========================================
   Gallery Grid (Bento)
   ======================================== */
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-auto-rows: 200px; /* Fixed row height for Bento cells */
  grid-auto-flow: dense;
  gap: 0.25rem;
}

@media (min-width: 640px) {
  .gallery-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1024px) {
  .gallery-grid {
    grid-template-columns: repeat(4, 1fr);
    grid-auto-rows: 240px;
    gap: 0.375rem;
  }
}

@media (min-width: 1280px) {
  .gallery-grid {
    grid-template-columns: repeat(5, 1fr);
    grid-auto-rows: 260px;
  }
}

/* Gallery Item */
.gallery-item {
  /* margin-bottom is handled by grid gap */
  margin-bottom: 0;
  width: 100%;
  height: 100%;
  animation: galleryFadeIn 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.gallery-item:focus {
  outline: none;
}

.gallery-item:focus-visible .image-card {
  outline: 3px solid #7fb7a4;
  outline-offset: 4px;
}

@keyframes galleryFadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Bento Spans */
.col-span-2 {
  grid-column: span 2;
}
.row-span-2 {
  grid-row: span 2;
}
.row-span-1 {
  grid-row: span 1;
}

.image-card {
  background-color: transparent;
  border-radius: 0.25rem;
  position: relative;
  cursor: pointer;
  transition: transform 0.3s ease;
  overflow: hidden;
  height: 100%;
  width: 100%;
}

.image-wrapper {
  position: relative;
  border-radius: 0.25rem;
  overflow: hidden;
  width: 100%;
  height: 100%;
  display: block;
  box-shadow: none;
  transition: box-shadow 0.3s ease;
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border-radius: 0.25rem;
  transform: scale(1);
  transition:
    transform 0.5s ease,
    opacity 0.5s ease;
  opacity: 0;
}

.gallery-image.image-visible {
  opacity: 1;
}

.image-card:hover .gallery-image {
  transform: scale(1.05);
}

/* Image Placeholder */
.image-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10;
  background: #f0fdf4;
  border-radius: 0.25rem;
}

.image-placeholder::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  animation: shimmer 1.5s infinite;
  transform: translateX(-100%);
}

.placeholder-content {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.soot-dot {
  width: 12px;
  height: 12px;
  background-color: rgba(90, 74, 58, 0.1);
  border-radius: 50%;
  animation: pulseDot 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

@keyframes pulseDot {
  0%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
}

/* ========================================
   Load More
   ======================================== */
.load-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
}
</style>
