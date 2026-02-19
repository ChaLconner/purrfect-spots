<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import ErrorState from '@/components/ui/ErrorState.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import type { CatLocation } from '@/types/api';

const props = defineProps<{
  uploads: CatLocation[];
  isLoading: boolean;
  error: string | null;
  isOwnProfile?: boolean;
  userName?: string;
}>();

const { t, locale } = useI18n();

defineEmits<{
  (e: 'open-image', upload: CatLocation): void;
  (e: 'retry'): void;
}>();

// Responsive Columns
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024);
const updateWidth = () => {
  windowWidth.value = globalThis.innerWidth;
};

onMounted(() => {
  globalThis.addEventListener('resize', updateWidth);
});

onUnmounted(() => {
  globalThis.removeEventListener('resize', updateWidth);
});

const cols = computed(() => {
  if (windowWidth.value >= 1024) return 4;
  if (windowWidth.value >= 768) return 3;
  return 2;
});

// Row Chunking for Virtual Scrolling
const rows = computed(() => {
  const result = [];
  for (let i = 0; i < props.uploads.length; i += cols.value) {
    result.push({
      id: `row-${i}`,
      items: props.uploads.slice(i, i + cols.value),
    });
  }
  return result;
});
</script>

<template>
  <div>
    <!-- Gallery Section Header -->
    <div class="mb-6">
      <h2
        class="text-xl sm:text-2xl font-heading font-bold text-brown text-center md:text-left pl-2 mb-3 sm:mb-4 border-l-4 border-terracotta"
      >
        {{
          isOwnProfile
            ? t('profile.myCollection')
            : t('profile.userCollection', { name: userName || t('profile.unknownUser') })
        }}
      </h2>
    </div>

    <!-- Tab Content: Uploads -->
    <div class="min-h-[300px]">
      <!-- Loading State -->
      <div v-if="isLoading" class="flex flex-col justify-center items-center py-20">
        <GhibliLoader :text="t('profile.gatheringMemories')" />
      </div>

      <!-- Error State -->
      <ErrorState v-else-if="error" :message="error" @retry="$emit('retry')" />

      <!-- No Uploads State -->
      <EmptyState
        v-else-if="uploads.length === 0"
        :title="t('profile.welcomeHome')"
        :message="t('profile.emptyGalleryMessage')"
        :sub-message="t('profile.emptyGallerySubMessage')"
        :action-text="isOwnProfile ? t('profile.shareFirstSpot') : undefined"
        :action-link="isOwnProfile ? '/upload' : undefined"
      />

      <!-- Uploads Grid with Virtual Scrolling -->
      <DynamicScroller
        v-else
        :items="rows"
        :min-item-size="200"
        key-field="id"
        class="profile-scroller"
      >
        <template #default="{ item, index, active }">
          <DynamicScrollerItem
            :item="item"
            :active="active"
            :size-dependencies="[cols]"
            :data-index="index"
            class="profile-row"
          >
            <div
              class="grid gap-3 sm:gap-4 md:gap-6 p-2 sm:p-3 md:p-4 w-full"
              :style="{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }"
            >
              <button
                v-for="upload in item.items"
                :key="upload.id"
                class="group relative aspect-square rounded-xl sm:rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-500 bg-stone-100 text-left"
                @click="$emit('open-image', upload)"
              >
                <!-- Image with Hover Zoom -->
                <img
                  :src="upload.image_url"
                  :alt="upload.description || t('galleryPage.modal.aCat')"
                  class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                  loading="lazy"
                />

                <!-- Elegant Overlay -->
                <div
                  class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent lg:opacity-0 lg:group-hover:opacity-100 opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4"
                >
                  <p
                    class="text-white font-heading font-bold text-sm truncate filter drop-shadow-md transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300"
                  >
                    {{ upload.location_name || t('profile.mysterySpot') }}
                  </p>
                  <p
                    class="text-white/80 text-xs truncate filter drop-shadow-md transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300 delay-75"
                  >
                    {{ new Date(upload.uploaded_at).toLocaleDateString(locale) }}
                  </p>
                </div>
              </button>
            </div>
          </DynamicScrollerItem>
        </template>
      </DynamicScroller>
    </div>
  </div>
</template>

<style scoped>
.profile-scroller {
  height: 100%;
  max-height: 80vh;
}

.profile-row {
  width: 100%;
}
</style>
