<template>
  <div>
    <div ref="trendsSectionRef" class="mt-4 bg-white p-5 rounded-2xl shadow-sm border border-sand-200 transition-all">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
        <div>
          <h3 class="m-0 text-xl font-bold text-brown-900 font-heading">
            {{ t('admin.dashboard.trends.title') }}
          </h3>
          <p class="m-0 text-sm text-brown-500">{{ t('admin.dashboard.trends.subtitle') }}</p>
        </div>
        <div class="flex flex-col items-end gap-3">
          <button
            class="flex items-center gap-2 px-5 py-2.5 text-[10px] font-bold text-terracotta-600 bg-white border-2 border-terracotta-100 rounded-xl shadow-sm uppercase tracking-widest"
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

          <div class="flex flex-wrap items-center justify-end gap-x-5 gap-y-2 pr-2 mt-1">
            <div
              v-for="series in chartSeries"
              :key="series.name"
              class="flex items-center gap-2 cursor-pointer"
              :class="{ 'opacity-40 grayscale-[0.5]': isHidden(series.name) }"
              @click="toggleSeries(series.name)"
            >
              <div
                class="w-3.5 h-1.5 rounded-full bg-[var(--series-color)]"
                :style="{ '--series-color': getSeriesColor(series.name) }"
              ></div>
              <span class="text-[11px] font-bold text-brown-600 uppercase tracking-widest font-heading">
                {{ series.name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="adminStore.isTrendsLoading && !hasTrendsData"
        class="min-h-80 flex items-center justify-center rounded-2xl border border-dashed border-sand-300 bg-sand-50"
      >
        <div class="flex flex-col items-center gap-4 text-brown-400">
          <div
            class="w-8 h-8 border-4 border-terracotta-100 border-t-terracotta-600 rounded-full animate-spin"
          ></div>
          <span class="text-sm font-medium">{{ t('admin.dashboard.trends.fetching') }}</span>
        </div>
      </div>

      <div
        v-show="hasTrendsData"
        class="min-h-[350px] overflow-hidden transition-all duration-700"
        :class="{ 'opacity-60 grayscale-[0.4] pointer-events-none blur-[1px]': adminStore.isTrendsLoading }"
      >
        <svg
          v-if="shouldRenderTrendsChart"
          id="admin-trends-chart"
          class="w-full min-h-[350px] text-brown-500"
          viewBox="0 0 640 320"
          role="img"
          :aria-label="t('admin.dashboard.trends.title')"
        >
          <g>
            <line v-for="line in 5" :key="line" x1="40" x2="620" :y1="gridY(line)" :y2="gridY(line)" class="[stroke:#f1e9e4] [stroke-dasharray:4]" />
          </g>
          <g class="[fill:var(--color-brown-400)] [font-size:11px] [font-weight:600]">
            <text
              v-for="label in trendAxisLabels"
              :key="label.key"
              :x="label.x"
              y="302"
              text-anchor="middle"
            >
              {{ label.text }}
            </text>
          </g>
          <polyline
            v-for="series in visibleTrendSeries"
            :key="series.name"
            class="fill-none [stroke-width:3] [stroke-linecap:round] [stroke-linejoin:round]"
            :points="series.points"
            :stroke="series.color"
          />
          <circle
            v-for="point in visibleTrendPoints"
            :key="point.key"
            class="[r:4] [stroke:white] [stroke-width:2]"
            :cx="point.x"
            :cy="point.y"
            :fill="point.color"
          >
            <title>{{ point.label }}</title>
          </circle>
        </svg>
        <div v-else class="min-h-[300px] rounded-2xl bg-gradient-to-r from-sand-100/80 via-white/95 to-sand-100/80 bg-[length:200%_100%] animate-[shimmer_2s_linear_infinite]" aria-hidden="true"></div>
      </div>

      <div
        v-if="!hasTrendsData && !adminStore.isTrendsLoading"
        class="min-h-80 flex items-center justify-center rounded-2xl border border-dashed border-sand-300 text-brown-400 italic bg-sand-100/35"
      >
        {{ t('admin.dashboard.trends.noData') }}
      </div>

      <div
        v-if="hasTrendsData && adminStore.isTrendsLoading"
        class="py-4 text-center text-[10px] text-brown-400 font-bold uppercase tracking-[0.2em] animate-pulse"
      >
        {{ t('admin.dashboard.trends.refreshing') }}
      </div>
    </div>

    <div ref="monthlySectionRef" class="mt-4 bg-white p-5 rounded-2xl shadow-sm border border-sand-200 transition-all">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
        <div>
          <h3 class="m-0 text-xl font-bold text-brown-900 font-heading">
            {{ t('admin.dashboard.monthly.title') }}
          </h3>
          <p class="m-0 text-sm text-brown-500">{{ t('admin.dashboard.monthly.subtitle') }}</p>
        </div>
      </div>

      <div
        v-if="adminStore.isMonthlyLoading && adminStore.monthlyData.length === 0"
        class="grid grid-cols-1 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] gap-8"
      >
        <div class="min-h-[300px] rounded-2xl bg-sand-50 animate-pulse"></div>
        <div class="min-h-[300px] rounded-2xl bg-sand-50 animate-pulse"></div>
      </div>

      <div
        v-show="adminStore.monthlyData.length > 0"
        key="monthly-stats-container"
        class="grid grid-cols-1 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] gap-8"
        :class="{ 'opacity-60 pointer-events-none grayscale-[0.2]': adminStore.isMonthlyLoading }"
      >
        <div class="min-h-[300px]">
          <svg
            v-if="shouldRenderMonthlyChart"
            id="admin-monthly-chart"
            class="w-full min-h-[300px] text-brown-500"
            viewBox="0 0 640 300"
            role="img"
            :aria-label="t('admin.dashboard.monthly.title')"
          >
            <g>
              <line v-for="line in 5" :key="line" x1="40" x2="620" :y1="monthlyGridY(line)" :y2="monthlyGridY(line)" class="[stroke:#f1e9e4] [stroke-dasharray:4]" />
            </g>
            <g v-for="group in monthlyBarGroups" :key="group.key">
              <rect
                v-for="bar in group.bars"
                :key="bar.key"
                class="[filter:drop-shadow(0_4px_8px_rgba(45,36,32,0.08))]"
                :x="bar.x"
                :y="bar.y"
                :width="bar.width"
                :height="bar.height"
                :fill="bar.color"
                rx="4"
              >
                <title>{{ bar.label }}</title>
              </rect>
              <text class="[fill:var(--color-brown-400)] [font-size:11px] [font-weight:600]" :x="group.labelX" y="282" text-anchor="middle">
                {{ group.label }}
              </text>
            </g>
          </svg>
          <div v-else class="min-h-[300px] rounded-2xl bg-gradient-to-r from-sand-100/80 via-white/95 to-sand-100/80 bg-[length:200%_100%] animate-[shimmer_2s_linear_infinite]" aria-hidden="true"></div>
        </div>

        <div class="overflow-hidden p-4 rounded-2xl border border-sand-200/80 bg-sand-50/60">
          <table class="w-full min-w-full text-xs font-medium text-brown-700 border-collapse">
            <thead>
              <tr class="text-brown-400 text-[10px] uppercase tracking-wider">
                <th class="text-left pb-3">{{ t('admin.dashboard.monthly.table.month') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.users') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.photos') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.resolved') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in activeMonthlyRows"
                :key="row.month_timestamp"
                class="transition-colors hover:bg-white/50 border-t border-sand-200/50"
              >
                <td class="py-2 font-bold text-brown-900 capitalize">
                  {{ formatDate(row.month_timestamp, { month: 'long' }, locale) }}
                </td>
                <td class="py-2 text-right">{{ row.new_users }}</td>
                <td class="py-2 text-right">{{ row.new_photos }}</td>
                <td class="py-2 text-right text-green-600">{{ row.resolved_reports }}</td>
              </tr>
            </tbody>
          </table>
          <div
            v-if="activeMonthlyRows.length === 0"
            class="py-12 text-center text-brown-400 italic"
          >
            {{ t('admin.dashboard.monthly.noActivity') }}
          </div>
        </div>
      </div>

      <div
        v-if="!adminStore.isMonthlyLoading && adminStore.monthlyData.length === 0"
        class="min-h-64 flex items-center justify-center rounded-2xl border border-dashed border-sand-300 text-brown-400 italic bg-sand-100/35"
      >
        {{ t('admin.dashboard.monthly.error') }}
      </div>

      <div
        v-if="adminStore.monthlyData.length > 0 && adminStore.isMonthlyLoading"
        class="py-4 text-center text-[10px] text-brown-400 font-bold uppercase tracking-[0.2em] animate-pulse"
      >
        {{ t('admin.dashboard.performance.updating') || 'Updating performance metrics...' }}
      </div>
    </div>

    <div
      v-if="adminStore.showPerformanceStats"
      class="fixed right-4 bottom-4 z-50 px-5 py-3 border border-white/20 rounded-2xl bg-stone-900/95 text-stone-200 backdrop-blur-xl shadow-2xl font-mono text-[11px] animate-fadeIn"
    >
      <div class="flex items-center gap-4">
        <div class="flex flex-col">
          <span class="text-[9px] font-bold text-stone-200 uppercase tracking-tight">{{
            t('admin.dashboard.performance.statsLoad')
          }}</span>
          <span class="text-sm font-bold text-stone-200"
            >{{ adminStore.statsLoadTime
            }}<span class="text-[10px] ml-0.5 opacity-60">ms</span></span
          >
        </div>
        <div class="w-px h-8 bg-white/20"></div>
        <div class="flex flex-col">
          <span class="text-[9px] font-bold text-stone-200 uppercase tracking-tight">{{
            t('admin.dashboard.performance.trendsLoad')
          }}</span>
          <span class="text-sm font-bold text-stone-200"
            >{{ adminStore.trendsLoadTime
            }}<span class="text-[10px] ml-0.5 opacity-60">ms</span></span
          >
        </div>
        <div class="w-px h-8 bg-white/20"></div>
        <div class="flex flex-col items-center">
          <span class="text-[9px] font-bold text-stone-200 uppercase tracking-tight">{{
            t('admin.dashboard.performance.status')
          }}</span>
          <span class="px-2 py-0.5 border border-green-400/20 rounded-md bg-green-400/10 text-green-400 font-bold">{{ t('admin.dashboard.performance.optimized') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAdminStore } from '@/stores/adminStore';
import { format, parseISO } from 'date-fns';
import { formatDate } from '@/utils/date';

const { t, locale } = useI18n();
const adminStore = useAdminStore();

const trendsSectionRef = ref<HTMLElement | null>(null);
const monthlySectionRef = ref<HTMLElement | null>(null);
const hiddenSeries = ref<string[]>([]);
const shouldRenderTrendsChart = ref(false);
const shouldRenderMonthlyChart = ref(false);
let trendsObserver: IntersectionObserver | null = null;
let monthlyObserver: IntersectionObserver | null = null;

const isHidden = (name: string): boolean => hiddenSeries.value.includes(name);

const getSeriesColor = (name: string): string => {
  const colors: Record<string, string> = {
    [t('admin.dashboard.trends.series.newUsers')]: '#8B4D2D',
    [t('admin.dashboard.trends.series.newPhotos')]: '#D67A4F',
    [t('admin.dashboard.trends.series.newReports')]: '#C75B5B',
    [t('admin.dashboard.trends.series.pointsEarned')]: '#E59976',
  };
  return colors[name] || '#ccc';
};

const toggleSeries = (name: string): void => {
  if (hiddenSeries.value.includes(name)) {
    hiddenSeries.value = hiddenSeries.value.filter((entry) => entry !== name);
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

const chartSeries = computed(() => [
  {
    name: t('admin.dashboard.trends.series.newUsers'),
    data: adminStore.trends.users.map((item) => item.count),
  },
  {
    name: t('admin.dashboard.trends.series.newPhotos'),
    data: adminStore.trends.photos.map((item) => item.count),
  },
  {
    name: t('admin.dashboard.trends.series.newReports'),
    data: adminStore.trends.reports.map((item) => item.count),
  },
]);

const monthlyChartSeries = computed(() => [
  {
    name: t('admin.dashboard.monthly.table.users'),
    data: adminStore.monthlyData.map((item) => item.new_users),
  },
  {
    name: t('admin.dashboard.monthly.table.photos'),
    data: adminStore.monthlyData.map((item) => item.new_photos),
  },
  {
    name: t('admin.dashboard.monthly.table.resolved'),
    data: adminStore.monthlyData.map((item) => item.resolved_reports),
  },
]);

const activeMonthlyRows = computed(() =>
  adminStore.monthlyData.filter((item) => item.new_users > 0 || item.new_photos > 0)
);

const trendColors = ['#8B4D2D', '#D67A4F', '#C75B5B'];
const monthlyColors = ['#8B4D2D', '#A65D37', '#7A9B76'];
const chartLeft = 40;
const chartRight = 620;
const trendTop = 24;
const trendBottom = 272;
const monthlyTop = 24;
const monthlyBottom = 250;

const trendMaxValue = computed(() =>
  Math.max(1, ...chartSeries.value.flatMap((series) => series.data))
);

const monthlyMaxValue = computed(() =>
  Math.max(1, ...monthlyChartSeries.value.flatMap((series) => series.data))
);

const scaleX = (index: number, total: number): number => {
  if (total <= 1) {
    return (chartLeft + chartRight) / 2;
  }
  return chartLeft + (index / (total - 1)) * (chartRight - chartLeft);
};

const scaleY = (value: number, maxValue: number, top: number, bottom: number): number =>
  bottom - (value / maxValue) * (bottom - top);

const gridY = (line: number): number => trendTop + ((line - 1) / 4) * (trendBottom - trendTop);
const monthlyGridY = (line: number): number => monthlyTop + ((line - 1) / 4) * (monthlyBottom - monthlyTop);

const visibleTrendSeries = computed(() =>
  chartSeries.value
    .map((series, seriesIndex) => ({
      name: series.name,
      color: trendColors[seriesIndex] || '#8C7B70',
      points: series.data
        .map((value, index) => `${scaleX(index, series.data.length)},${scaleY(value, trendMaxValue.value, trendTop, trendBottom)}`)
        .join(' '),
    }))
    .filter((series) => !isHidden(series.name))
);

const visibleTrendPoints = computed(() =>
  chartSeries.value.flatMap((series, seriesIndex) =>
    isHidden(series.name)
      ? []
      : series.data.map((value, index) => ({
          key: `${series.name}-${index}`,
          x: scaleX(index, series.data.length),
          y: scaleY(value, trendMaxValue.value, trendTop, trendBottom),
          color: trendColors[seriesIndex] || '#8C7B70',
          label: `${series.name}: ${value.toLocaleString()}`,
        }))
  )
);

const trendAxisLabels = computed(() => {
  const labels = adminStore.trends.users.map((item) => format(parseISO(item.date), 'MMM dd'));
  if (labels.length <= 6) {
    return labels.map((text, index) => ({ key: `${text}-${index}`, text, x: scaleX(index, labels.length) }));
  }
  const step = Math.ceil(labels.length / 6);
  return labels
    .map((text, index) => ({ key: `${text}-${index}`, text, x: scaleX(index, labels.length), visible: index % step === 0 }))
    .filter((item) => item.visible);
});

const monthlyBarGroups = computed(() => {
  const rows = adminStore.monthlyData;
  const groupWidth = (chartRight - chartLeft) / Math.max(1, rows.length);
  const barWidth = Math.max(8, Math.min(24, groupWidth / 5));

  return rows.map((row, rowIndex) => {
    const baseX = chartLeft + rowIndex * groupWidth + groupWidth / 2;
    const values = [row.new_users, row.new_photos, row.resolved_reports];
    return {
      key: row.month_timestamp,
      label: format(parseISO(row.month_timestamp), 'MMM'),
      labelX: baseX,
      bars: values.map((value, valueIndex) => {
        const height = monthlyBottom - scaleY(value, monthlyMaxValue.value, monthlyTop, monthlyBottom);
        return {
          key: `${row.month_timestamp}-${valueIndex}`,
          x: baseX + (valueIndex - 1) * (barWidth + 3) - barWidth / 2,
          y: monthlyBottom - height,
          width: barWidth,
          height: Math.max(1, height),
          color: monthlyColors[valueIndex] || '#8C7B70',
          label: `${monthlyChartSeries.value[valueIndex].name}: ${value.toLocaleString()}`,
        };
      }),
    };
  });
});

onMounted(() => {
  const setupDeferredObserver = (
    element: HTMLElement | null,
    onVisible: () => void
  ): IntersectionObserver | null => {
    if (!element || !('IntersectionObserver' in window)) {
      onVisible();
      return null;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          onVisible();
          observer.disconnect();
        }
      },
      {
        rootMargin: '200px 0px',
        threshold: 0.01,
      }
    );

    observer.observe(element);
    return observer;
  };

  trendsObserver = setupDeferredObserver(trendsSectionRef.value, () => {
    shouldRenderTrendsChart.value = true;
  });

  monthlyObserver = setupDeferredObserver(monthlySectionRef.value, () => {
    shouldRenderMonthlyChart.value = true;
  });
});

onUnmounted(() => {
  trendsObserver?.disconnect();
  monthlyObserver?.disconnect();
  trendsObserver = null;
  monthlyObserver = null;
});
</script>
