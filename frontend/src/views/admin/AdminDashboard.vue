<template>
  <div>
    <AdminPageHeader
      :title="t('admin.dashboard.title')"
      :subtitle="t('admin.dashboard.subtitle')"
    />

    <!-- Stats Cards -->
    <div
      v-if="!adminStore.isLoading && adminStore.stats.total_users > 0"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4"
    >
      <div
        v-for="(card, i) in statCards"
        :key="i"
        class="group p-4 bg-white border border-sand-200/90 rounded-xl shadow-sm transition-all hover:border-terracotta-200/90 hover:shadow-[0_6px_16px_rgba(0,0,0,0.06)]"
      >
        <h3
          class="text-sm font-medium text-brown-500 uppercase tracking-[0.08em] transition-colors group-hover:text-brown-700"
        >
          {{ card.label }}
        </h3>
        <p class="mt-2 text-3xl font-bold transition-colors" :class="card.colorClass">
          {{ card.value }}
        </p>
      </div>
    </div>

    <!-- Loading State for Stats -->
    <div
      v-else-if="adminStore.isLoading"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4"
    >
      <div
        v-for="n in 4"
        :key="n"
        class="p-4 bg-white border border-sand-200/90 rounded-xl shadow-sm"
      >
        <SkeletonLoader width="50%" height="0.875rem" />
        <div class="mt-2">
          <SkeletonLoader width="30%" height="2.25rem" />
        </div>
      </div>
    </div>

    <div ref="chartsMountRef">
      <AdminDashboardCharts v-if="shouldRenderCharts" />
      <div v-else-if="!adminStore.error" class="mt-4 grid gap-4" aria-hidden="true">
        <div class="min-h-[20rem] rounded-2xl bg-gradient-to-r from-sand-100/80 via-white/95 to-sand-100/80 bg-[length:200%_100%] animate-[shimmer_2s_linear_infinite]"></div>
        <div class="min-h-[20rem] rounded-2xl bg-gradient-to-r from-sand-100/80 via-white/95 to-sand-100/80 bg-[length:200%_100%] animate-[shimmer_2s_linear_infinite]"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, defineAsyncComponent, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue';
import { useAdminStore } from '@/stores/adminStore';
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
