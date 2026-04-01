<template>
  <div class="gallery-page min-h-screen relative overflow-x-hidden bg-[#fffbf6]">
    <GhibliBackground />

    <div class="gallery-container max-w-7xl mx-auto py-2 px-1 sm:px-2 lg:px-4 overflow-x-hidden">
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
        @update:liked="handleImageLikedUpdate"
        @update:likes-count="handleImageLikesCountUpdate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, onErrorCaptured, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { GalleryService } from '@/services/galleryService';
import { isDev } from '@/utils/env';
import GalleryHeader from '@/components/gallery/GalleryHeader.vue';
import GalleryGrid from '@/components/gallery/GalleryGrid.vue';
import type { CatLocation } from '@/types/api';
import { useGalleryState } from '@/composables/useGalleryState';
import { useCatsStore, useAuthStore } from '@/store';

const authStore = useAuthStore();

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

const {
  loading,
  loadingMore,
  error,
  visibleImages,
  hasMoreImages,
  totalImages,
  fetchImages,
  loadMoreImages,
  cleanupPreloads,
} = useGalleryState(computed(() => authStore.isInitialized));

const selectedImage = ref<CatLocation | null>(null);
const currentImageIndex = ref(-1);

// Pagination and virtual scrolling
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
let searchDebounce: ReturnType<typeof setTimeout> | null = null;
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

    if (searchDebounce) clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      fetchImages(() => {
        if (props.id) {
          syncStateFromUrl();
        }
      });
    }, 400); // 400ms debounce for smoother UX
  }
);

// Watch URL changes to sync modal state (using Path Params now)
watch(
  () => props.id,
  () => {
    syncStateFromUrl();
  }
);

// Watch images to trigger preload is now handled internally in useGalleryState

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

function handleImageLikedUpdate(val: boolean): void {
  if (selectedImage.value) {
    selectedImage.value.liked = val;
  }
}

function handleImageLikesCountUpdate(val: number): void {
  if (selectedImage.value) {
    selectedImage.value.likes_count = val;
  }
}

async function syncStateFromUrl(): Promise<void> {
  // Wait for auth before syncing to avoid context issues or 401s
  if (!authStore.isInitialized) return;

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

// Data fetching and pagination logic is delegated to useGalleryState

function openModal(image: CatLocation, index: number): void {
  // Update URL using Path Parameter
  router.push({
    name: 'Gallery',
    params: { id: image.id },
    query: route.query, // Preserve search query
  });
}

function closeModal(): void {
  // Remove ID from Path - using undefined to avoid trailing slash or empty string issues
  router.push({
    name: 'Gallery',
    params: { id: undefined },
    query: route.query,
  });
}

function handleModalNavigate(direction: 'prev' | 'next'): void {
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

// Preloading logic delegated to useGalleryState
watch(
  () => authStore.isInitialized,
  (isInit) => {
    if (isInit) {
      // Auth is ready (either logged in or guest confirmed)
      // Now safe to fetch data with correct auth context
      fetchImages(() => {
        if (props.id) {
          syncStateFromUrl();
        }
      });
    }
  },
  { immediate: true }
);
</script>
