<template>
  <div>
    <h1 class="text-3xl font-bold text-brown-900 font-display">Dashboard</h1>
    <p class="mt-1 text-brown-600">System Overview.</p>

    <div
      v-if="!adminStore.isLoading && adminStore.stats.total_users > 0"
      class="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      <div class="bg-white p-6 rounded-2xl shadow-sm border border-sand-100">
        <h3 class="text-sm font-medium text-brown-500 uppercase tracking-wider">Total Users</h3>
        <p class="mt-2 text-3xl font-bold text-brown-900">{{ adminStore.stats.total_users }}</p>
      </div>
      <div class="bg-white p-6 rounded-2xl shadow-sm border border-sand-100">
        <h3 class="text-sm font-medium text-brown-500 uppercase tracking-wider">Total Photos</h3>
        <p class="mt-2 text-3xl font-bold text-terracotta-600">
          {{ adminStore.stats.total_photos }}
        </p>
      </div>
      <div class="bg-white p-6 rounded-2xl shadow-sm border border-sand-100">
        <h3 class="text-sm font-medium text-brown-500 uppercase tracking-wider">Total Reports</h3>
        <p class="mt-2 text-3xl font-bold text-terracotta-600">
          {{ adminStore.stats.total_reports }}
        </p>
      </div>
      <div class="bg-white p-6 rounded-2xl shadow-sm border border-sand-100">
        <h3 class="text-sm font-medium text-brown-500 uppercase tracking-wider">Pending Reports</h3>
        <p class="mt-2 text-3xl font-bold text-red-600">{{ adminStore.stats.pending_reports }}</p>
      </div>
    </div>
    <div
      v-else-if="adminStore.isLoading"
      class="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      <div
        v-for="n in 4"
        :key="n"
        class="bg-white p-6 rounded-2xl shadow-sm border border-sand-100"
      >
        <SkeletonLoader width="50%" height="0.875rem" />
        <div class="mt-2">
          <SkeletonLoader width="30%" height="2.25rem" />
        </div>
      </div>
    </div>
    <div v-else class="mt-8">
      <p class="text-brown-500">No stats available or failed to load.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useAdminStore } from '@/store/adminStore';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';

const adminStore = useAdminStore();

onMounted(() => {
  adminStore.fetchStats();
});
</script>
