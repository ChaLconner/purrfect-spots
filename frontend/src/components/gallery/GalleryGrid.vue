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
          <div
            class="grid grid-cols-2 md:grid-cols-4 auto-rows-[200px] lg:auto-rows-[240px] xl:auto-rows-[260px] grid-flow-dense gap-1 lg:gap-1.5"
            role="grid"
            :aria-label="t('galleryPage.aria.galleryChunk')"
          >
            <button
              v-for="(image, subIndex) in item.images"
              :key="image.id"
              type="button"
              class="w-full h-full mb-0 p-0 border-none bg-transparent text-left focus:outline-none focus-visible:[&_.image-card]:outline-3 focus-visible:[&_.image-card]:outline-secondary focus-visible:[&_.image-card]:outline-offset-4 animate-[galleryFadeIn_0.6s_cubic-bezier(0.2,0.8,0.2,1)_both]"
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
              <div
                class="image-card group relative bg-transparent rounded cursor-pointer transition-transform duration-300 ease-in-out overflow-hidden w-full h-full"
              >
                <!-- Placeholder -->
                <div
                  v-if="!loadedImages[image.id]"
                  class="image-placeholder absolute inset-0 z-10 bg-[#f0fdf4] rounded after:content-[''] after:absolute after:inset-0 after:bg-gradient-to-r after:from-transparent after:via-white/60 after:to-transparent after:animate-[shimmer_1.5s_infinite] after:-translate-x-full h-full w-full"
                  aria-hidden="true"
                >
                  <div class="placeholder-content flex items-center justify-center w-full h-full">
                    <div
                      class="soot-dot w-3 h-3 bg-[#5a4a3a]/10 rounded-full animate-[pulseDot_1.5s_ease-in-out_infinite]"
                    ></div>
                  </div>
                </div>

                <!-- Treat Button Overlay -->
                <div
                  class="absolute bottom-2 right-2 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity z-20"
                  role="group"
                >
                  <button
                    class="treat-item-btn group absolute bottom-2 right-2 bg-transparent border-none cursor-pointer p-0 transition-all z-20"
                    :title="t('galleryPage.modal.giveTreats')"
                    :aria-label="t('galleryPage.aria.giveTreat')"
                    @click.stop="handleGiveTreat(image)"
                  >
                    <div
                      class="treat-btn-inner transition-transform duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] drop-shadow-md group-hover:-translate-y-0.5 group-hover:scale-110 group-active:scale-95"
                    >
                      <img
                        src="/give-treat.png"
                        :alt="t('profile.treats')"
                        class="w-12 h-12 object-contain"
                      />
                    </div>
                  </button>
                </div>

                <!-- Actual Image with native lazy loading -->
                <div
                  class="image-wrapper relative rounded overflow-hidden w-full h-full block shadow-none transition-shadow duration-300 ease-in-out"
                >
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
                    class="gallery-image w-full h-full object-cover block rounded scale-100 transition-[transform,opacity] duration-500 ease-in-out opacity-0 group-hover:scale-105 shadow-md"
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
      class="load-more flex flex-col items-center gap-3 p-8 h-4 w-full"
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
const updateWidth = (): void => {
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
