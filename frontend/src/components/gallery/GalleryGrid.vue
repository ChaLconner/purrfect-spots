<template>
  <div class="gallery-content">
    <DynamicScroller :items="chunkedImages" :min-item-size="200" class="scroller" page-mode>
      <template #default="{ item, index, active }">
        <DynamicScrollerItem
          :item="item"
          :active="active"
          :size-dependencies="[item.images.length, windowWidth]"
          :data-index="index"
        >
          <div class="gallery-grid" role="grid" :aria-label="t('galleryPage.aria.galleryChunk')">
            <button
              v-for="(image, subIndex) in item.images"
              :key="image.id"
              type="button"
              class="gallery-item p-0 border-none bg-transparent text-left"
              :class="[
                getBentoClass(item.index + subIndex),
                { 'item-loaded': loadedImages[image.id] },
              ]"
              :style="{ 'animation-delay': `${(subIndex % 10) * 0.05}s` }"
              :aria-label="
                t('galleryPage.aria.viewCat', {
                  location: image.location_name || t('galleryPage.modal.aCat'),
                })
              "
              @click="$emit('open-modal', image, item.index + subIndex)"
            >
              <!-- Glass-framed Image Card -->
              <div class="image-card group">
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

                <!-- Treat Button Overlay -->
                <div
                  class="absolute bottom-2 right-2 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity z-20"
                  role="group"
                >
                  <button
                    class="treat-item-btn group absolute bottom-2 right-2 transition-all z-20"
                    :title="t('galleryPage.modal.giveTreats')"
                    :aria-label="t('galleryPage.aria.giveTreat')"
                    @click.stop="handleGiveTreat(image)"
                  >
                    <div class="treat-btn-inner">
                      <img
                        src="/give-treat.png"
                        :alt="t('profile.treats')"
                        class="w-12 h-12 object-contain"
                      />
                    </div>
                  </button>
                </div>

                <!-- Actual Image with native lazy loading -->
                <div class="image-wrapper">
                  <img
                    loading="lazy"
                    :src="image.image_url"
                    :srcset="generateSrcSet(image.image_url)"
                    sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
                    :alt="
                      image.location_name
                        ? t('galleryPage.modal.aCatAt', { location: image.location_name })
                        : t('galleryPage.modal.aCat')
                    "
                    class="gallery-image shadow-md"
                    :class="{ 'image-visible': loadedImages[image.id] }"
                    @load="handleImageLoad(image.id)"
                    @error="handleImageError(image.id, $event)"
                  />
                </div>
              </div>
            </button>
          </div>
        </DynamicScrollerItem>
      </template>
    </DynamicScroller>

    <!-- Load More -->
    <div
      v-if="hasMore && !loadingMore"
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import { useSubscriptionStore } from '@/store/subscriptionStore';
import { useToastStore, useAuthStore } from '@/store';
import { IMAGE_CONFIG, GALLERY_CONFIG } from '@/utils/constants';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import type { CatLocation } from '@/types/api';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps<{
  images: CatLocation[];
  hasMore: boolean;
  loadingMore: boolean;
}>();

const emit = defineEmits<{
  (e: 'open-modal', image: CatLocation, index: number): void;
  (e: 'load-more'): void;
}>();

const loadedImages = ref<Record<string, boolean>>({});
const loadMoreTrigger = ref<HTMLElement | null>(null);
const loadMoreObserver = ref<IntersectionObserver | null>(null);

const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024);

let resizeTimer: ReturnType<typeof setTimeout> | null = null;
const updateWidth = () => {
  if (resizeTimer) clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    windowWidth.value = globalThis.innerWidth;
  }, 100);
};

// Bento & Chunking
const CHUNK_SIZE = 20;

const chunkedImages = computed(() => {
  const chunks = [];
  for (let i = 0; i < props.images.length; i += CHUNK_SIZE) {
    chunks.push({
      id: i,
      index: i,
      images: props.images.slice(i, i + CHUNK_SIZE),
    });
  }
  return chunks;
});

function getBentoClass(index: number): string {
  // Determine current column count based on windowWidth
  // Breakpoints must match CSS media queries
  let cols = 2;
  if (windowWidth.value >= 1280) cols = 5;
  else if (windowWidth.value >= 1024) cols = 4;
  else if (windowWidth.value >= 640) cols = 3;

  // The simplified Bento pattern (28 cells per 20 items) works perfectly for:
  // - 2 columns (28 / 2 = 14 rows)
  // - 4 columns (28 / 4 = 7 rows)
  // It leaves gaps for 3 and 5 columns.
  // For those breakpoints, we revert to a standard grid to avoid visual glitches.
  if (cols !== 2 && cols !== 4) {
    return 'col-span-1 row-span-1';
  }

  const remainder = index % 20;
  if (remainder === 0) return 'col-span-2 row-span-2';
  if (remainder === 13) return 'col-span-2 row-span-2';
  if (remainder === 6) return 'col-span-2 row-span-1';
  if (remainder === 19) return 'col-span-2 row-span-1';
  return 'col-span-1 row-span-1';
}

// Generate responsive sources for ANY image (Supabase or S3 via proxy)
function generateSrcSet(url: string): string {
  if (!url) return '';
  const widths = [300, 500, 800];

  return widths
    .map((width) => {
      // 1. Supabase Storage (Native)
      if (url.includes('supabase.co')) {
        let newUrl = url;
        if (url.includes('width=')) {
          newUrl = url.replace(/width=\d+/, `width=${width}`);
        } else {
          const sep = url.includes('?') ? '&' : '?';
          newUrl = `${url}${sep}width=${width}`;
        }
        return `${newUrl} ${width}w`;
      }

      // 2. S3 / External (Proxy)
      // Remove any existing proxy params to start fresh from original URL if possible
      // Assuming 'wsrv.nl' is used: decode original url param
      let cleanUrl = url;
      if (url.includes('wsrv.nl') && url.includes('url=')) {
        const match = url.match(/url=([^&]+)/);
        if (match && match[1]) {
          cleanUrl = decodeURIComponent(match[1]);
        }
      }

      return `https://wsrv.nl/?url=${encodeURIComponent(cleanUrl)}&w=${width}&q=80&output=webp ${width}w`;
    })
    .join(', ');
}

// Image Loading
function handleImageLoad(id: string): void {
  loadedImages.value[id] = true;
}

function handleImageError(id: string, event: Event): void {
  const target = event.target as HTMLImageElement;
  if (target.src !== IMAGE_CONFIG.PLACEHOLDER_URL) {
    target.src = IMAGE_CONFIG.PLACEHOLDER_URL;
  }
  // Clear shimmer on error
  loadedImages.value[id] = true;
}

// Treats
async function handleGiveTreat(image: CatLocation): Promise<void> {
  const authStore = useAuthStore();
  const toastStore = useToastStore();

  if (!authStore.isAuthenticated) {
    toastStore.addToast({
      title: t('auth.signInRequired'),
      message: t('galleryPage.modal.signInToTreat'),
      type: 'warning',
    });
    return;
  }

  const subscriptionStore = useSubscriptionStore();
  try {
    await subscriptionStore.giveTreat(image.id, 1);
    toastStore.addToast({
      title: t('profile.treatGiven'),
      message: t('galleryPage.modal.treatsGiven', { amount: 1 }),
      type: 'success',
    });
  } catch (e: unknown) {
    const msg =
      e instanceof Error
        ? e.message
        : (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
          'Failed to give treat';
    toastStore.addToast({
      title: t('galleryPage.modal.treatFailed'),
      message: msg,
      type: 'error',
    });
  }
}

// Infinite Scroll Observer
function setupLoadMoreObserver(): void {
  if (loadMoreObserver.value) loadMoreObserver.value.disconnect();
  if (!loadMoreTrigger.value || !props.hasMore) return;

  loadMoreObserver.value = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && props.hasMore && !props.loadingMore) {
          emit('load-more');
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

// Lifecycle
onMounted(() => {
  window.addEventListener('resize', updateWidth);
  // Initial observer setup
  setupLoadMoreObserver();
});

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth);
  if (loadMoreObserver.value) loadMoreObserver.value.disconnect();
  loadedImages.value = {};
});

// Watchers
watch(
  () => props.images,
  () => {
    // Sync loaded images state
    props.images.forEach((image) => {
      if (!(image.id in loadedImages.value)) {
        loadedImages.value[image.id] = false;
      }
    });

    // Re-setup observer on data change
    nextTick(() => setupLoadMoreObserver());
  },
  { deep: false, immediate: true }
);

watch(
  () => props.loadingMore,
  async () => {
    await nextTick();
    setupLoadMoreObserver();
  }
);
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
  outline: 3px solid var(--color-secondary);
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

/* Treat Button */
.treat-item-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}

.treat-btn-inner {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.15));
}

.treat-item-btn:hover .treat-btn-inner {
  transform: translateY(-2px) scale(1.1);
}

.treat-item-btn:active .treat-btn-inner {
  transform: scale(0.95);
}

/* Load More */
.load-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
}
</style>
