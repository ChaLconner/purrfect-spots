<template>
  <output class="flex justify-center w-full mb-10" aria-live="polite">
    <div
      class="flex items-center gap-8 py-3.5 px-10 bg-white/90 backdrop-blur-sm rounded-full shadow-[0_4px_6px_-1px_rgba(0,0,0,0.02),0_2px_4px_-1px_rgba(0,0,0,0.02)] border border-white/50 transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-[0_10px_15px_-3px_rgba(0,0,0,0.05),0_4px_6px_-2px_rgba(0,0,0,0.025)] hover:bg-white/95"
    >
      <div class="flex items-baseline gap-2">
        <output
          class="font-nunito text-xl font-extrabold text-[#5a4632] leading-none"
          :aria-label="t('galleryPage.stats.totalPhotos')"
          >{{ totalCount }}</output
        >
        <span class="font-sans text-sm font-medium text-[#7d7d7d] lowercase tracking-[0.02em]">{{
          t('galleryPage.stats.photo', totalCount)
        }}</span>
      </div>
      <div
        v-if="totalCount !== visibleCount"
        class="w-px h-6 bg-gradient-to-b from-transparent via-[#cbd5e0] to-transparent"
        aria-hidden="true"
      ></div>
      <div v-if="totalCount !== visibleCount" class="flex items-baseline gap-2">
        <output class="font-nunito text-xl font-extrabold text-[#5a4632] leading-none">{{
          visibleCount
        }}</output>
        <span class="font-sans text-sm font-medium text-[#7d7d7d] lowercase tracking-[0.02em]">{{
          t('galleryPage.stats.showing')
        }}</span>
      </div>
    </div>
  </output>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

defineProps<{
  totalCount: number;
  visibleCount: number;
}>();
</script>
