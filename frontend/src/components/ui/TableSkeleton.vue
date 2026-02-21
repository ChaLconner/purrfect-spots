<template>
  <tr v-for="r in rows" :key="r" class="animate-pulse border-b border-sand-100 last:border-0">
    <td
      v-for="c in columns"
      :key="c"
      class="px-6 py-4 whitespace-nowrap"
      :class="{ 'text-right': c === columns }"
    >
      <!-- Avatar Column -->
      <div v-if="c === avatarColumn" class="flex items-center">
        <div class="h-10 w-10 bg-sand-200 rounded-full flex-shrink-0"></div>
        <div class="ml-4 space-y-2">
          <div class="h-4 bg-sand-200 rounded w-32"></div>
          <div class="h-3 bg-sand-100 rounded w-20"></div>
        </div>
      </div>

      <!-- Checkbox Column -->
      <div v-else-if="c === checkboxColumn" class="h-4 w-4 bg-sand-200 rounded"></div>

      <!-- Action Column (Last column usually) -->
      <div v-else-if="c === columns" class="flex justify-end gap-2">
        <div class="h-8 w-16 bg-sand-100 rounded-lg"></div>
        <div class="h-8 w-16 bg-sand-100 rounded-lg"></div>
      </div>

      <!-- Standard Text Column -->
      <div v-else class="space-y-1">
        <div class="h-4 bg-sand-200 rounded" :style="{ width: getRandomWidth() }"></div>
        <!-- Occasional second line -->
        <div
          v-if="r % 2 === 0"
          class="h-3 bg-sand-100 rounded"
          :style="{ width: getRandomWidth(40, 60) }"
        ></div>
      </div>
    </td>
  </tr>
</template>

<script setup lang="ts">
/**
 * TableSkeleton Component
 *
 * A reusable skeleton loader for table rows to provide a consistent loading state
 * across the admin dashboard.
 */

interface Props {
  rows?: number;
  columns?: number;
  avatarColumn?: number; // Column index (1-based) to show avatar
  checkboxColumn?: number; // Column index (1-based) to show checkbox
}

withDefaults(defineProps<Props>(), {
  rows: 5,
  columns: 4,
  avatarColumn: -1,
  checkboxColumn: -1,
});

// Helper to get random width string for more natural look
const getRandomWidth = (min = 60, max = 90) => {
  const width = Math.floor(Math.random() * (max - min + 1)) + min;
  return `${width}px`;
};
</script>
