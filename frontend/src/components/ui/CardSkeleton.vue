<script setup lang="ts">
/**
 * CardSkeleton Component
 *
 * Pre-designed skeleton card for gallery/profile image loading states.
 * Uses SkeletonLoader internally for consistency.
 */
import SkeletonLoader from './SkeletonLoader.vue';

interface Props {
  variant?: 'gallery' | 'profile' | 'list';
  count?: number;
}

const _props = withDefaults(defineProps<Props>(), {
  variant: 'gallery',
  count: 1,
});
</script>

<template>
  <div
    class="card-skeleton-container"
    :class="{
      'grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4': variant === 'gallery',
      'space-y-4': variant === 'profile' || variant === 'list',
    }"
  >
    <template v-for="i in count" :key="i">
      <!-- Gallery Card Skeleton -->
      <div
        v-if="variant === 'gallery'"
        class="bg-white rounded-[1rem] overflow-hidden shadow-[0_2px_8px_rgba(0,0,0,0.05)]"
      >
        <SkeletonLoader height="200px" border-radius="1rem" />
      </div>

      <!-- Profile Card Skeleton -->
      <div
        v-else-if="variant === 'profile'"
        class="bg-white rounded-[1.5rem] shadow-[0_4px_12px_rgba(0,0,0,0.08)]"
      >
        <div class="flex items-center gap-4 p-6">
          <SkeletonLoader width="80px" height="80px" border-radius="50%" />
          <div class="flex-1 space-y-3">
            <SkeletonLoader width="60%" height="1.5rem" />
            <SkeletonLoader width="80%" height="1rem" />
            <SkeletonLoader width="40%" height="0.75rem" />
          </div>
        </div>
      </div>

      <!-- List Item Skeleton -->
      <div v-else-if="variant === 'list'" class="bg-white rounded-[0.75rem] mb-2 last:mb-0">
        <div class="flex items-center gap-3 p-4">
          <SkeletonLoader width="48px" height="48px" border-radius="0.5rem" />
          <div class="flex-1 space-y-2">
            <SkeletonLoader width="70%" height="1rem" />
            <SkeletonLoader width="50%" height="0.75rem" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
