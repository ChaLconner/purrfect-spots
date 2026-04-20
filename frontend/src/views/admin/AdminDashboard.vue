<template>
  <div>
    <h1 class="text-2xl font-bold text-brown-900 font-display transition-all duration-300">
      {{ t('admin.dashboard.title') }}
    </h1>
    <p class="mt-0.5 text-sm text-brown-600">{{ t('admin.dashboard.subtitle') }}</p>

    <!-- Stats Cards -->
    <div
      v-if="!adminStore.isLoading && adminStore.stats.total_users > 0"
      class="admin-dashboard-stats"
    >
      <div
        v-for="(card, i) in statCards"
        :key="i"
        class="admin-stat-card group"
      >
        <h3
          class="admin-stat-label"
        >
          {{ card.label }}
        </h3>
        <p class="admin-stat-value transition-colors" :class="card.colorClass">
          {{ card.value }}
        </p>
      </div>
    </div>

    <!-- Loading State for Stats -->
    <div
      v-else-if="adminStore.isLoading"
      class="admin-dashboard-stats"
    >
      <div
        v-for="n in 4"
        :key="n"
        class="admin-stat-card"
      >
        <SkeletonLoader width="50%" height="0.875rem" />
        <div class="mt-2">
          <SkeletonLoader width="30%" height="2.25rem" />
        </div>
      </div>
    </div>

    <div ref="chartsMountRef">
      <AdminDashboardCharts v-if="shouldRenderCharts" />
      <div v-else class="admin-dashboard-chart-shell" aria-hidden="true">
        <div class="admin-dashboard-chart-shell-card"></div>
        <div class="admin-dashboard-chart-shell-card"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, defineAsyncComponent, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAdminStore } from '@/store/adminStore';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
const AdminDashboardCharts = defineAsyncComponent(() => import('@/components/admin/AdminDashboardCharts.vue'));

const { t } = useI18n();
const adminStore = useAdminStore();
const chartsMountRef = ref<HTMLElement | null>(null);
const shouldRenderCharts = ref(false);
let chartsObserver: IntersectionObserver | null = null;

onMounted(async () => {
  // Use consolidated fetch for speed
  await adminStore.fetchSummary();

  if (chartsMountRef.value && 'IntersectionObserver' in window) {
    chartsObserver = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          shouldRenderCharts.value = true;
          chartsObserver?.disconnect();
          chartsObserver = null;
        }
      },
      {
        rootMargin: '200px 0px',
        threshold: 0.01,
      }
    );
    chartsObserver.observe(chartsMountRef.value);
  } else {
    shouldRenderCharts.value = true;
  }
});

onUnmounted(() => {
  chartsObserver?.disconnect();
  chartsObserver = null;
});

const statCards = computed(() => [
  {
    label: t('admin.dashboard.stats.totalUsers'),
    value: adminStore.stats.total_users,
    colorClass: 'text-brown-900',
  },
  {
    label: t('admin.dashboard.stats.totalPhotos'),
    value: adminStore.stats.total_photos,
    colorClass: 'text-terracotta-600',
  },
  {
    label: t('admin.dashboard.stats.totalReports'),
    value: adminStore.stats.total_reports,
    colorClass: 'text-terracotta-600',
  },
  {
    label: t('admin.dashboard.stats.pendingReports'),
    value: adminStore.stats.pending_reports,
    colorClass: 'text-red-600',
  },
]);
</script>

<style scoped>
.font-display {
  font-family: 'Outfit', sans-serif;
}

.admin-dashboard-stats {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.admin-stat-card {
  padding: 1rem;
  background: white;
  border: 1px solid rgba(231, 229, 228, 0.9);
  border-radius: 0.75rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.admin-stat-card:hover {
  border-color: rgba(238, 207, 185, 0.9);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
}

.admin-stat-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-brown-500, #8c7e7a);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  transition: color 0.2s ease;
}

.group:hover .admin-stat-label {
  color: var(--color-brown-700, #44403c);
}

.admin-stat-value {
  margin-top: 0.5rem;
  font-size: 1.875rem;
  font-weight: 700;
}

.admin-dashboard-chart-shell {
  margin-top: 1rem;
  display: grid;
  gap: 1rem;
}

.admin-dashboard-chart-shell-card {
  min-height: 20rem;
  border-radius: 1rem;
  background: linear-gradient(90deg, rgba(245, 245, 244, 0.8) 0%, rgba(255, 255, 255, 0.96) 50%, rgba(245, 245, 244, 0.8) 100%);
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}

@media (min-width: 640px) {
  .admin-dashboard-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .admin-dashboard-stats {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
