<template>
  <div>
    <h1 class="text-2xl font-bold text-brown-900 font-display transition-all duration-300">
      {{ t('admin.dashboard.title') }}
    </h1>
    <p class="mt-0.5 text-sm text-brown-600">{{ t('admin.dashboard.subtitle') }}</p>

    <!-- Stats Cards -->
    <div
      v-if="!adminStore.isLoading && adminStore.stats.total_users > 0"
      class="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"
    >
      <div
        v-for="(card, i) in statCards"
        :key="i"
        class="bg-white p-4 rounded-xl shadow-sm border border-sand-100 transition-all hover:shadow-md hover:border-terracotta-100 group"
      >
        <h3
          class="text-sm font-medium text-brown-500 uppercase tracking-wider group-hover:text-brown-700 transition-colors"
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
      class="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"
    >
      <div
        v-for="n in 4"
        :key="n"
        class="bg-white p-4 rounded-xl shadow-sm border border-sand-100"
      >
        <SkeletonLoader width="50%" height="0.875rem" />
        <div class="mt-2">
          <SkeletonLoader width="30%" height="2.25rem" />
        </div>
      </div>
    </div>

    <!-- Trends Visualization -->
    <div class="mt-4 bg-white p-5 rounded-2xl shadow-sm border border-sand-200 transition-all">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-4">
        <div>
          <h3 class="text-xl font-bold text-brown-900 font-display">
            {{ t('admin.dashboard.trends.title') }}
          </h3>
          <p class="text-sm text-brown-500">{{ t('admin.dashboard.trends.subtitle') }}</p>
        </div>
        <div class="flex flex-col items-end gap-3">
          <button
            class="px-5 py-2.5 text-[10px] font-bold text-terracotta-600 bg-white border-2 border-terracotta-100 rounded-xl shadow-sm uppercase tracking-[0.1em] flex items-center gap-2"
            :disabled="adminStore.isTrendsLoading"
            @click="adminStore.fetchTrends(true)"
          >
            <span
              v-if="adminStore.isTrendsLoading"
              class="w-3.5 h-3.5 border-2 border-terracotta-400 border-t-transparent rounded-full animate-spin"
            ></span>
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              class="w-3.5 h-3.5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
              <path d="M16 16h5v5" />
            </svg>
            {{
              adminStore.isTrendsLoading
                ? t('admin.dashboard.trends.updating')
                : t('admin.dashboard.trends.refresh')
            }}
          </button>

          <!-- Custom Premium Legend -->
          <div class="flex flex-wrap items-center justify-end gap-x-5 gap-y-2 pr-2 mt-1">
            <div
              v-for="s in chartSeries"
              :key="s.name"
              class="flex items-center gap-2 cursor-pointer"
              :class="{ 'opacity-40 grayscale-[0.5]': isHidden(s.name) }"
              @click="toggleSeries(s.name)"
            >
              <div
                class="w-3.5 h-1.5 rounded-full"
                :style="{ backgroundColor: getSeriesColor(s.name) }"
              ></div>
              <span
                class="text-[11px] font-bold text-brown-600 font-display uppercase tracking-widest"
              >
                {{ s.name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="adminStore.isTrendsLoading && !hasTrendsData"
        class="h-80 flex items-center justify-center bg-sand-50 rounded-2xl border border-dashed border-sand-300"
      >
        <div class="flex flex-col items-center gap-4 text-brown-400">
          <div
            class="w-8 h-8 border-4 border-terracotta-100 border-t-terracotta-600 rounded-full animate-spin"
          ></div>
          <span class="text-sm font-medium">{{ t('admin.dashboard.trends.fetching') }}</span>
        </div>
      </div>

      <!-- Chart Container -->
      <div
        v-show="hasTrendsData"
        class="transition-all duration-700 overflow-hidden min-h-[350px]"
        :class="{ 'opacity-60 grayscale-[0.4] pointer-events-none blur-[1px]': adminStore.isTrendsLoading }"
      >
        <ApexChart
          id="admin-trends-chart"
          ref="chartRef"
          :key="`trends-${adminStore.lastFetched}`"
          height="350"
          type="area"
          :options="chartOptions"
          :series="chartSeries"
        />
      </div>

      <!-- Empty State -->
      <div 
        v-if="!hasTrendsData && !adminStore.isTrendsLoading" 
        class="h-80 flex items-center justify-center text-brown-400 italic bg-sand-50/30 rounded-2xl border border-dashed border-sand-200"
      >
        {{ t('admin.dashboard.trends.noData') }}
      </div>

      <!-- Progress Indicator when refreshing existing data -->
      <div 
        v-if="hasTrendsData && adminStore.isTrendsLoading" 
        class="text-center py-4 text-[10px] text-brown-400 font-bold uppercase tracking-[0.2em] animate-pulse"
      >
        {{ t('admin.dashboard.trends.refreshing') }}
      </div>
    </div>

    <!-- Monthly Performance Deep-dive -->
    <div class="mt-4 bg-white p-5 rounded-2xl shadow-sm border border-sand-200 transition-all">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-4">
        <div>
          <h3 class="text-xl font-bold text-brown-900 font-display">
            {{ t('admin.dashboard.monthly.title') }}
          </h3>
          <p class="text-sm text-brown-500">{{ t('admin.dashboard.monthly.subtitle') }}</p>
        </div>
      </div>

      <div
        v-if="adminStore.isMonthlyLoading && adminStore.monthlyData.length === 0"
        class="grid grid-cols-1 lg:grid-cols-3 gap-8"
      >
        <div class="lg:col-span-2 h-[300px] bg-sand-50 rounded-2xl animate-pulse"></div>
        <div class="bg-sand-50 rounded-2xl p-4 h-[300px] animate-pulse"></div>
      </div>

      <!-- Monthly Performance Container -->
      <div
        v-show="adminStore.monthlyData.length > 0"
        key="monthly-stats-container"
        class="grid grid-cols-1 lg:grid-cols-3 gap-8 transition-all duration-500"
        :class="{ 'opacity-60 pointer-events-none grayscale-[0.2]': adminStore.isMonthlyLoading }"
      >
        <!-- Monthly Chart -->
        <div class="lg:col-span-2 min-h-[300px]">
          <ApexChart
            id="admin-monthly-chart"
            :key="`monthly-${adminStore.lastFetched}`"
            height="300"
            type="bar"
            :options="monthlyChartOptions"
            :series="monthlyChartSeries"
          />
        </div>

        <!-- Monthly Table -->
        <div class="bg-sand-50/50 rounded-2xl p-4 overflow-hidden border border-sand-100">
          <table class="min-w-full text-xs font-medium text-brown-700">
            <thead>
              <tr class="text-brown-400 text-[10px] uppercase tracking-wider">
                <th class="text-left pb-3">{{ t('admin.dashboard.monthly.table.month') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.users') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.photos') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.resolved') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-sand-200/50">
              <tr
                v-for="row in adminStore.monthlyData.filter(
                  (m) => m.new_users > 0 || m.new_photos > 0
                )"
                :key="row.month_timestamp"
                class="hover:bg-white/50 transition-colors"
              >
                <td class="py-2 text-brown-900 font-bold capitalize">
                  {{ new Date(row.month_timestamp).toLocaleDateString(locale, { month: 'long' }) }}
                </td>
                <td class="py-2 text-right">{{ row.new_users }}</td>
                <td class="py-2 text-right">{{ row.new_photos }}</td>
                <td class="py-2 text-right text-green-600">{{ row.resolved_reports }}</td>
              </tr>
            </tbody>
          </table>
          <div
            v-if="adminStore.monthlyData.every((m) => m.new_users === 0 && m.new_photos === 0)"
            class="py-12 text-center text-brown-400 italic"
          >
            {{ t('admin.dashboard.monthly.noActivity') }}
          </div>
        </div>
      </div>

      <div 
        v-if="!adminStore.isMonthlyLoading && adminStore.monthlyData.length === 0" 
        class="h-64 flex items-center justify-center text-brown-400 italic bg-sand-50/20 rounded-2xl border border-dashed border-sand-200"
      >
        {{ t('admin.dashboard.monthly.error') }}
      </div>

      <div 
        v-if="adminStore.monthlyData.length > 0 && adminStore.isMonthlyLoading" 
        class="text-center py-4 text-[10px] text-brown-400 font-bold uppercase tracking-[0.2em] animate-pulse"
      >
        {{ t('admin.dashboard.performance.updating') || 'Updating performance metrics...' }}
      </div>
    </div>
  </div>

  <!-- Performance Benchmark Overlay (Optional/Toggleable) -->
  <div
    v-if="adminStore.showPerformanceStats"
    class="fixed bottom-4 right-4 bg-brown-950/95 text-brown-200 px-5 py-3 rounded-2xl text-[11px] font-mono backdrop-blur-xl shadow-2xl border border-white/20 z-50 animate-fade-in ring-1 ring-black/50"
  >
    <div class="flex items-center gap-4">
      <div class="flex flex-col">
        <span class="text-brown-200 uppercase tracking-tighter font-bold text-[9px]">{{
          t('admin.dashboard.performance.statsLoad')
        }}</span>
        <span class="font-bold text-brown-200 text-sm"
          >{{ adminStore.statsLoadTime }}<span class="text-[10px] ml-0.5 opacity-60">ms</span></span
        >
      </div>
      <div class="w-px h-8 bg-white/20"></div>
      <div class="flex flex-col">
        <span class="text-brown-200 uppercase tracking-tighter font-bold text-[9px]">{{
          t('admin.dashboard.performance.trendsLoad')
        }}</span>
        <span class="font-bold text-brown-200 text-sm"
          >{{ adminStore.trendsLoadTime
          }}<span class="text-[10px] ml-0.5 opacity-60">ms</span></span
        >
      </div>
      <div class="w-px h-8 bg-white/20"></div>
      <div class="flex flex-col items-center">
        <span class="text-brown-200 uppercase tracking-tighter font-bold text-[9px]">{{
          t('admin.dashboard.performance.status')
        }}</span>
        <span
          class="font-bold text-green-400 bg-green-400/10 px-2 py-0.5 rounded-md border border-green-400/20"
          >{{ t('admin.dashboard.performance.optimized') }}</span
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, defineAsyncComponent } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAdminStore } from '@/store/adminStore';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
import { format, parseISO } from 'date-fns';

const { t, locale } = useI18n();
const adminStore = useAdminStore();
const ApexChart = defineAsyncComponent(() => import('vue3-apexcharts'));

onMounted(async () => {
  // Use consolidated fetch for speed
  await adminStore.fetchSummary();
});

const chartRef = ref(null);
const hiddenSeries = ref<string[]>([]);

const isHidden = (name: string): boolean => hiddenSeries.value.includes(name);

const getSeriesColor = (name: string): string => {
  const colors: Record<string, string> = {
    [t('admin.dashboard.trends.series.newUsers')]: '#4A3728',
    [t('admin.dashboard.trends.series.newPhotos')]: '#E67E22',
    [t('admin.dashboard.trends.series.newReports')]: '#E74C3C',
    [t('admin.dashboard.trends.series.pointsEarned')]: '#FFD700',
  };
  return colors[name] || '#ccc';
};

const toggleSeries = (name: string): void => {
  if (!chartRef.value) return;

  // ApexCharts built-in toggle
  (chartRef.value as { toggleSeries: (n: string) => void }).toggleSeries(name);

  // Update local state for UI
  if (hiddenSeries.value.includes(name)) {
    hiddenSeries.value = hiddenSeries.value.filter((n) => n !== name);
  } else {
    hiddenSeries.value.push(name);
  }
};

const hasTrendsData = computed(
  () =>
    adminStore.trends.users.length > 0 ||
    adminStore.trends.photos.length > 0 ||
    adminStore.trends.reports.length > 0
);

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

// Activity Trends Configuration
const chartSeries = computed(() => [
  {
    name: t('admin.dashboard.trends.series.newUsers'),
    data: adminStore.trends.users.map((d) => d.count),
  },
  {
    name: t('admin.dashboard.trends.series.newPhotos'),
    data: adminStore.trends.photos.map((d) => d.count),
  },
  {
    name: t('admin.dashboard.trends.series.newReports'),
    data: adminStore.trends.reports.map((d) => d.count),
  },
]);

const chartOptions = computed(() => ({
  chart: {
    id: 'admin-trends-chart',
    type: 'area',
    toolbar: { show: false },
    zoom: { enabled: false },
    animations: {
      enabled: true,
      easing: 'easeinout',
      speed: 800,
    },
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  dataLabels: { enabled: false },
  stroke: {
    curve: 'smooth',
    width: 3,
  },
  colors: ['#4A3728', '#E67E22', '#E74C3C'], // Brown, Terracotta, Red
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.45,
      opacityTo: 0.05,
      stops: [20, 100, 100, 100],
    },
  },
  grid: {
    borderColor: '#F1E9E4',
    strokeDashArray: 4,
  },
  xaxis: {
    categories: adminStore.trends.users.map((d) => format(parseISO(d.date), 'MMM dd')),
    labels: {
      style: { colors: '#8C7B70', fontSize: '11px' },
      rotate: -45,
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: { colors: '#8C7B70', fontSize: '11px' },
    },
  },
  tooltip: {
    theme: 'light',
    x: { show: true },
    marker: { show: true },
  },
  legend: {
    show: false, // Hidden to use custom legend
  },
}));

// Monthly Chart Configuration
const monthlyChartSeries = computed(() => [
  {
    name: t('admin.dashboard.monthly.table.users'),
    data: adminStore.monthlyData.map((d) => d.new_users),
  },
  {
    name: t('admin.dashboard.monthly.table.photos'),
    data: adminStore.monthlyData.map((d) => d.new_photos),
  },
  {
    name: t('admin.dashboard.monthly.table.resolved'),
    data: adminStore.monthlyData.map((d) => d.resolved_reports),
  },
]);

const monthlyChartOptions = computed(() => ({
  chart: {
    id: 'admin-monthly-chart',
    type: 'bar',
    stacked: false,
    toolbar: { show: false },
    fontFamily: 'Inter, system-ui, sans-serif',
    dropShadow: {
      enabled: true,
      top: 2,
      left: 1,
      blur: 4,
      opacity: 0.1,
    },
  },
  stroke: {
    width: 1,
    colors: ['#fff'],
  },
  plotOptions: {
    bar: {
      horizontal: false,
      columnWidth: '55%',
      borderRadius: 10,
      dataLabels: { position: 'top' },
    },
  },
  dataLabels: {
    enabled: false,
    offsetY: -20,
    style: { fontSize: '12px', colors: ['#304758'] },
  },
  colors: ['#5D4037', '#8D6E63', '#4CAF50'], // Earth Tones and Success Green
  xaxis: {
    categories: adminStore.monthlyData.map((d) => format(parseISO(d.month_timestamp), 'MMM')),
    position: 'bottom',
    axisBorder: { show: false },
    axisTicks: { show: false },
    labels: {
      style: { colors: '#8C7B70', fontSize: '12px', fontWeight: 600 },
    },
  },
  yaxis: {
    axisBorder: { show: false },
    axisTicks: { show: false },
    labels: {
      show: true,
      style: { colors: '#8C7B70', fontSize: '12px' },
    },
  },
  grid: {
    borderColor: '#F1E9E4',
    strokeDashArray: 2,
  },
  tooltip: {
    theme: 'light',
    y: {
      formatter: (val: number): string => val.toLocaleString(),
    },
  },
  legend: {
    position: 'top',
    horizontalAlign: 'right',
    offsetY: -10,
    fontWeight: 700,
    itemMargin: { horizontal: 15, vertical: 0 },
  },
}));
</script>

<style scoped>
.font-display {
  font-family: 'Outfit', sans-serif;
}
</style>
