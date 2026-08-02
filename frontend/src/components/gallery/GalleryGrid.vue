<template>
  <div>
    <DynamicScroller :items="chunkedImages" :min-item-size="200" class="scroller" page-mode>
      <template #default="{ item, index, active }">
        <DynamicScrollerItem
          :item="item"
          :active="active"
          :data-index="index"
        >
          <div
            class="grid grid-cols-2 md:grid-cols-4 auto-rows-[200px] lg:auto-rows-[240px] xl:auto-rows-[260px] grid-flow-dense gap-1 lg:gap-1.5"
            role="grid"
            :aria-label="t('galleryPage.aria.galleryChunk')"
          >
            <button
              v-for="(image, subIndex) in item.images"
              :key="image.id"
              type="button"
              class="w-full h-full mb-0 p-0 border-none bg-transparent text-left focus:outline-none focus-visible:[&_.image-card]:outline-3 focus-visible:[&_.image-card]:outline-secondary focus-visible:[&_.image-card]:outline-offset-4 animate-[galleryFadeIn_0.6s_cubic-bezier(0.2,0.8,0.2,1)_both] [animation-delay:var(--gallery-delay)]"
              :class="[
                getBentoClass(Number(item.index) + Number(subIndex)),
              ]"
              :style="{ '--gallery-delay': `${(Number(subIndex) % 10) * 0.05}s` }"
              :aria-label="
                t('galleryPage.aria.viewCat', {
                  location: image.location_name || t('galleryPage.modal.aCat'),
                })
              "
              @click="$emit('open-modal', image, Number(item.index) + Number(subIndex))"
            >
              <!-- Glass-framed Image Card -->
              <div
                class="image-card group relative bg-transparent rounded cursor-pointer transition-transform duration-300 ease-in-out overflow-hidden w-full h-full"
              >
                <!-- Placeholder -->
                <div
                  v-if="!loadedImages[image.id]"
                  class="absolute inset-0 z-10 h-full w-full rounded bg-[#f0fdf4] after:absolute after:inset-0 after:-translate-x-full after:animate-[shimmer_1.5s_infinite] after:bg-gradient-to-r after:from-transparent after:via-white/60 after:to-transparent after:content-['']"
                  aria-hidden="true"
                >
                  <div class="flex h-full w-full items-center justify-center">
                    <div
                      class="h-3 w-3 rounded-full bg-[#5a4a3a]/10 animate-[pulseDot_1.5s_ease-in-out_infinite]"
                    ></div>
                  </div>
                </div>

                <!-- Actual Image with native lazy loading -->
                <div
                  class="relative block h-full w-full overflow-hidden rounded shadow-none transition-shadow duration-300 ease-in-out"
                >
                  <img
                    loading="lazy"
                    decoding="async"
                    width="800"
                    height="600"
                    :src="image.image_url"
                    :srcset="generateSrcSet(image.image_url)"
                    sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
                    :alt="
                      image.location_name
                        ? t('galleryPage.modal.aCatAt', { location: image.location_name })
                        : t('galleryPage.modal.aCat')
                    "
                    class="block h-full w-full scale-100 rounded object-cover opacity-0 shadow-md transition-[transform,opacity] duration-500 ease-in-out group-hover:scale-105"
                    :class="{ 'opacity-100': loadedImages[image.id] }"
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
      class="flex h-4 w-full flex-col items-center gap-3 p-8"
      aria-hidden="true"
    ></div>
    <span v-if="loadingMore" class="sr-only" role="status" aria-live="polite">
      {{ t('galleryPage.loading') }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import { IMAGE_CONFIG, GALLERY_CONFIG } from '@/utils/constants';
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

const loadedImages = shallowRef<Record<string, boolean>>({});
const loadMoreTrigger = ref<HTMLElement | null>(null);
const loadMoreObserver = ref<IntersectionObserver | null>(null);

const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024);

let resizeTimer: ReturnType<typeof setTimeout> | null = null;
const updateWidth = (): void => {
  if (resizeTimer) clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    windowWidth.value = globalThis.innerWidth;
  }, 100);
};

// Bento & Chunking
const CHUNK_SIZE = 20;
const srcSetCache = new Map<string, string>();
const SRC_SET_CACHE_MAX_SIZE = 500;

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
  if (windowWidth.value >= 768) cols = 4;

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
  const cached = srcSetCache.get(url);
  if (cached) return cached;
  const widths = [300, 500, 800];

  const srcSet = widths
    .map((width) => {
      // 1. Supabase Storage (Native)
      if (url.includes('supabase.co')) {
        const newUrl = url.includes('width=')
          ? url.replace(/width=\d+/, `width=${width}`)
          : `${url}${url.includes('?') ? '&' : '?'}width=${width}`;
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
  if (srcSetCache.size >= SRC_SET_CACHE_MAX_SIZE) {
    const oldest = srcSetCache.keys().next().value;
    if (oldest) srcSetCache.delete(oldest);
  }
  srcSetCache.set(url, srcSet);
  return srcSet;
}

// Image Loading
function handleImageLoad(id: string): void {
  loadedImages.value = { ...loadedImages.value, [id]: true };
}

function handleImageError(id: string, event: Event): void {
  const target = event.target as HTMLImageElement;
  if (target.src !== IMAGE_CONFIG.PLACEHOLDER_URL) {
    target.src = IMAGE_CONFIG.PLACEHOLDER_URL;
  }
  // Clear shimmer on error

  loadedImages.value = { ...loadedImages.value, [id]: true };
}

// Infinite Scroll Observer
function setupLoadMoreObserver(): void {
  // Ensure we disconnect previous observer to avoid leaks
  if (loadMoreObserver.value) {
    loadMoreObserver.value.disconnect();
    loadMoreObserver.value = null;
  }

  if (!loadMoreTrigger.value || !props.hasMore) return;

  loadMoreObserver.value = new IntersectionObserver(
    (entries) => {
      const [entry] = entries;
      // Added isIntersecting AND check if already loading to prevent race conditions
      if (entry.isIntersecting && props.hasMore && !props.loadingMore) {
        emit('load-more');
      }
    },
    {
      root: null, // Scanned viewport
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
  if (loadMoreObserver.value) {
    loadMoreObserver.value.disconnect();
    loadMoreObserver.value = null;
  }
  loadedImages.value = {};
});

// Watchers
watch(
  () => props.images,
  () => {
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
