<template>
  <div class="gallery-page min-h-screen relative overflow-x-hidden">
    <GhibliBackground />

    <div class="gallery-container max-w-7xl mx-auto py-2 px-1 sm:px-2 lg:px-4">
      <!-- Ghibli Style Header with Search -->
      <GalleryHeader />

      <div class="gallery-mint-container p-0 min-h-[600px] w-full relative z-[5]">
        <!-- Loading state -->
        <output v-if="loading" class="loading-container" aria-live="polite">
          <GhibliLoader :text="$t('galleryPage.loading')" />
        </output>

        <!-- Error state -->
        <ErrorState v-else-if="error" :message="error" @retry="fetchImages" />

        <!-- Empty state -->
        <EmptyState
          v-else-if="visibleImages.length === 0"
          :title="$t('galleryPage.empty.title')"
          :message="$t('galleryPage.empty.message')"
          :sub-message="$t('galleryPage.empty.subMessage')"
          :action-text="$t('galleryPage.empty.action')"
          action-link="/upload"
        />

        <!-- Gallery Grid -->
        <GalleryGrid
          v-else
          :images="visibleImages"
          :has-more="hasMoreImages"
          :loading-more="loadingMore"
          @open-modal="openModal"
          @load-more="loadMoreImages"
        />
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
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { GalleryService } from '@/services/galleryService';
import { isDev } from '@/utils/env';
import { GALLERY_CONFIG } from '@/utils/constants';
import GalleryHeader from '@/components/gallery/GalleryHeader.vue';
import GalleryGrid from '@/components/gallery/GalleryGrid.vue';
import { useCatsStore } from '@/store';
import type { CatLocation } from '@/types/api';

import GalleryModal from '@/components/gallery/GalleryModal.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import ErrorState from '@/components/ui/ErrorState.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useSeo } from '@/composables/useSeo';

// SEO
const { setMetaTags, resetMetaTags } = useSeo();
const { t } = useI18n();

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

// Pagination and virtual scrolling
const currentPage = ref(1);
const imagesPerPage = GALLERY_CONFIG.IMAGES_PER_PAGE;
const visibleImages = ref<CatLocation[]>([]);
const hasMoreImages = ref(false);
const totalImages = ref(0); // Track total for modal navigation
const isDeepLinked = ref(false); // Track if current view is a deep link to a specific image

onMounted(() => {
  // We rely on the authStore.isInitialized watcher to trigger fetchImages
  // This avoids double-fetching on page reload.

  // Check for search query in URL on mount
  if (route.query.q) {
    catsStore.setGallerySearchQuery(route.query.q as string);
  }

  // Set SEO meta tags
  setMetaTags({
    title: `${t('galleryPage.seo.title')} | Purrfect Spots`,
    description: t('galleryPage.seo.description'),
    type: 'website',
  });
});

onUnmounted(() => {
  // Reset SEO meta tags
  resetMetaTags();
  cleanupPreloads();
});

// Watch search query from store to update URL and fetch data
watch(
  () => catsStore.gallerySearchQuery,
  (newQuery) => {
    // Sync URL query param
    const query = { ...route.query };
    if (newQuery) {
      query.q = newQuery;
    } else {
      delete query.q;
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

// Watch images to trigger preload
watch(
  () => visibleImages.value.length,
  (newCount, oldCount) => {
    if (newCount > 0 && oldCount === 0) {
      preloadFirstImages();
    }
  }
);

// Watch route query specifically for browser back/forward buttons affecting search
watch(
  () => route.query.q,
  (newSearch) => {
    const term = (newSearch as string) || '';
    if (term !== catsStore.gallerySearchQuery) {
      catsStore.setGallerySearchQuery(term);
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

    // Reset to general Gallery SEO
    setMetaTags({
      title: `${t('galleryPage.seo.title')} | Purrfect Spots`,
      description: t('galleryPage.seo.description'),
      type: 'website',
    });
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

// Watch selected image for dynamic SEO updates
watch(
  () => selectedImage.value,
  (image) => {
    if (image) {
      const title = image.location_name
        ? `${image.location_name} | Purrfect Spots`
        : `${t('galleryPage.seo.defaultTitle')} | Purrfect Spots`;
      const description = image.description || t('galleryPage.seo.defaultImageDescription');
      // Use efficient image URL for sharing if possible, or fallback
      const imageUrl = image.image_url;

      setMetaTags({
        title,
        description,
        image: imageUrl,
        type: 'article',
      });
    }
  }
);

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
    const query = catsStore.gallerySearchQuery;
    let newImages: CatLocation[] = [];
    let hasNext = false;
    let total = 0;

    if (query) {
      // Server-side Search - Now with pagination!
      const response = await GalleryService.search({
        query,
        page: currentPage.value,
        limit: imagesPerPage,
      });

      newImages = response.results || [];
      total = response.total || 0;
      // Simple hasMore logic for search: if we got exactly 'limit' results, there's likely more.
      // Or if we know the total:
      hasNext = visibleImages.value.length + newImages.length < total;
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
    console.error(`[Gallery] Error fetching data:`, err);
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
  // Remove ID from Path - using undefined to avoid trailing slash or empty string issues
  router.push({
    name: 'Gallery',
    params: { id: undefined },
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

// Store preloaded links for cleanup
const preloadedLinks: HTMLLinkElement[] = [];

// Preload first few images for better performance
function preloadFirstImages() {
  // Avoid duplicate preloads
  if (preloadedLinks.length > 0) return;

  const imagesToPreload = visibleImages.value.slice(0, 6);

  imagesToPreload.forEach((image, index) => {
    if (image.image_url) {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'image';
      // Use smaller size for preloading (300px) only if supported (Supabase)
      let preloadUrl = image.image_url;
      if (image.image_url.includes('supabase.co')) {
        preloadUrl = image.image_url.includes('width=')
          ? image.image_url.replace(/width=\d+/, 'width=300')
          : `${image.image_url}${image.image_url.includes('?') ? '&' : '?'}width=300`;
      }
      link.href = preloadUrl;
      link.setAttribute('fetchpriority', index === 0 ? 'high' : 'low');
      document.head.appendChild(link);
      preloadedLinks.push(link);
    }
  });
}

function cleanupPreloads() {
  preloadedLinks.forEach((link) => {
    if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
  });
  preloadedLinks.length = 0;
}

// Watch for auth initialization to fetch gallery data
// This handles both initial load (wait for auth) and subsequent updates
// immediate: true ensures it runs if auth is already initialized (e.g. client-side nav)
import { useAuthStore } from '@/store/authStore';
const authStore = useAuthStore();

watch(
  () => authStore.isInitialized,
  (isInit) => {
    if (isInit) {
      // Auth is ready (either logged in or guest confirmed)
      // Now safe to fetch data with correct auth context
      fetchImages();
    }
  },
  { immediate: true }
);

// We don't need to call fetchImages in onMounted anymore because the watcher handles it.
// If isInitialized is false, we wait. If true, watcher runs.
onMounted(() => {
  // Check for search query in URL on mount
  if (route.query.q) {
    catsStore.setGallerySearchQuery(route.query.q as string);
  }

  // Set SEO meta tags
  setMetaTags({
    title: `${t('galleryPage.seo.title')} | Purrfect Spots`,
    description: t('galleryPage.seo.description'),
    type: 'website',
  });
});

onUnmounted(() => {
  // Reset SEO meta tags
  resetMetaTags();
  cleanupPreloads();
});
</script>

<style scoped>
/* Scoped styles specific to GalleryView layout */
.gallery-container {
  /* Ensure container doesn't overflow horizontally */
  overflow-x: hidden;
}

.gallery-page {
  background-color: #fffbf6;
}
</style>
