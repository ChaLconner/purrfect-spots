<template>
  <div>
    <div ref="trendsSectionRef" class="admin-chart-card">
      <div class="admin-chart-header">
        <div>
          <h3 class="admin-chart-title font-display">
            {{ t('admin.dashboard.trends.title') }}
          </h3>
          <p class="admin-chart-subtitle">{{ t('admin.dashboard.trends.subtitle') }}</p>
        </div>
        <div class="admin-chart-actions">
          <button
            class="admin-chart-refresh"
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

          <div class="admin-chart-legend">
            <div
              v-for="series in chartSeries"
              :key="series.name"
              class="admin-chart-legend-item"
              :class="{ 'opacity-40 grayscale-[0.5]': isHidden(series.name) }"
              @click="toggleSeries(series.name)"
            >
              <div
                class="w-3.5 h-1.5 rounded-full"
                :style="{ backgroundColor: getSeriesColor(series.name) }"
              ></div>
              <span class="admin-chart-legend-label font-display">
                {{ series.name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="adminStore.isTrendsLoading && !hasTrendsData"
        class="admin-chart-loading-state"
      >
        <div class="admin-chart-loading-content">
          <div
            class="w-8 h-8 border-4 border-terracotta-100 border-t-terracotta-600 rounded-full animate-spin"
          ></div>
          <span class="text-sm font-medium">{{ t('admin.dashboard.trends.fetching') }}</span>
        </div>
      </div>

      <div
        v-show="hasTrendsData"
        class="admin-chart-host"
        :class="{ 'opacity-60 grayscale-[0.4] pointer-events-none blur-[1px]': adminStore.isTrendsLoading }"
      >
        <svg
          v-if="shouldRenderTrendsChart"
          id="admin-trends-chart"
          class="admin-native-chart"
          viewBox="0 0 640 320"
          role="img"
          :aria-label="t('admin.dashboard.trends.title')"
        >
          <g class="admin-chart-grid">
            <line v-for="line in 5" :key="line" x1="40" x2="620" :y1="gridY(line)" :y2="gridY(line)" />
          </g>
          <g class="admin-chart-axis-labels">
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
            class="admin-chart-line"
            :points="series.points"
            :stroke="series.color"
          />
          <circle
            v-for="point in visibleTrendPoints"
            :key="point.key"
            class="admin-chart-point"
            :cx="point.x"
            :cy="point.y"
            :fill="point.color"
          >
            <title>{{ point.label }}</title>
          </circle>
        </svg>
        <div v-else class="admin-chart-library-skeleton" aria-hidden="true"></div>
      </div>

      <div
        v-if="!hasTrendsData && !adminStore.isTrendsLoading"
        class="admin-chart-empty-state"
      >
        {{ t('admin.dashboard.trends.noData') }}
      </div>

      <div
        v-if="hasTrendsData && adminStore.isTrendsLoading"
        class="admin-chart-status"
      >
        {{ t('admin.dashboard.trends.refreshing') }}
      </div>
    </div>

    <div ref="monthlySectionRef" class="admin-chart-card">
      <div class="admin-chart-header">
        <div>
          <h3 class="admin-chart-title font-display">
            {{ t('admin.dashboard.monthly.title') }}
          </h3>
          <p class="admin-chart-subtitle">{{ t('admin.dashboard.monthly.subtitle') }}</p>
        </div>
      </div>

      <div
        v-if="adminStore.isMonthlyLoading && adminStore.monthlyData.length === 0"
        class="admin-monthly-grid"
      >
        <div class="admin-monthly-chart-skeleton"></div>
        <div class="admin-monthly-table-skeleton"></div>
      </div>

      <div
        v-show="adminStore.monthlyData.length > 0"
        key="monthly-stats-container"
        class="admin-monthly-grid admin-monthly-grid-live"
        :class="{ 'opacity-60 pointer-events-none grayscale-[0.2]': adminStore.isMonthlyLoading }"
      >
        <div class="admin-monthly-chart-panel">
          <svg
            v-if="shouldRenderMonthlyChart"
            id="admin-monthly-chart"
            class="admin-native-chart admin-native-chart-short"
            viewBox="0 0 640 300"
            role="img"
            :aria-label="t('admin.dashboard.monthly.title')"
          >
            <g class="admin-chart-grid">
              <line v-for="line in 5" :key="line" x1="40" x2="620" :y1="monthlyGridY(line)" :y2="monthlyGridY(line)" />
            </g>
            <g v-for="group in monthlyBarGroups" :key="group.key">
              <rect
                v-for="bar in group.bars"
                :key="bar.key"
                class="admin-chart-bar"
                :x="bar.x"
                :y="bar.y"
                :width="bar.width"
                :height="bar.height"
                :fill="bar.color"
                rx="4"
              >
                <title>{{ bar.label }}</title>
              </rect>
              <text class="admin-chart-axis-label" :x="group.labelX" y="282" text-anchor="middle">
                {{ group.label }}
              </text>
            </g>
          </svg>
          <div v-else class="admin-chart-library-skeleton" aria-hidden="true"></div>
        </div>

        <div class="admin-monthly-table-panel">
          <table class="admin-monthly-table">
            <thead>
              <tr class="admin-monthly-table-head">
                <th class="text-left pb-3">{{ t('admin.dashboard.monthly.table.month') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.users') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.photos') }}</th>
                <th class="text-right pb-3">{{ t('admin.dashboard.monthly.table.resolved') }}</th>
              </tr>
            </thead>
            <tbody class="admin-monthly-table-body">
              <tr
                v-for="row in activeMonthlyRows"
                :key="row.month_timestamp"
                class="admin-monthly-table-row"
              >
                <td class="admin-monthly-table-month">
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
            class="admin-monthly-empty-state"
          >
            {{ t('admin.dashboard.monthly.noActivity') }}
          </div>
        </div>
      </div>

      <div
        v-if="!adminStore.isMonthlyLoading && adminStore.monthlyData.length === 0"
        class="admin-chart-empty-state admin-chart-empty-state-short"
      >
        {{ t('admin.dashboard.monthly.error') }}
      </div>

      <div
        v-if="adminStore.monthlyData.length > 0 && adminStore.isMonthlyLoading"
        class="admin-chart-status"
      >
        {{ t('admin.dashboard.performance.updating') || 'Updating performance metrics...' }}
      </div>
    </div>

    <div
      v-if="adminStore.showPerformanceStats"
      class="admin-performance-panel"
    >
      <div class="admin-performance-grid">
        <div class="admin-performance-cell">
          <span class="admin-performance-label">{{
            t('admin.dashboard.performance.statsLoad')
          }}</span>
          <span class="admin-performance-value"
            >{{ adminStore.statsLoadTime
            }}<span class="text-[10px] ml-0.5 opacity-60">ms</span></span
          >
        </div>
        <div class="admin-performance-divider"></div>
        <div class="admin-performance-cell">
          <span class="admin-performance-label">{{
            t('admin.dashboard.performance.trendsLoad')
          }}</span>
          <span class="admin-performance-value"
            >{{ adminStore.trendsLoadTime
            }}<span class="text-[10px] ml-0.5 opacity-60">ms</span></span
          >
        </div>
        <div class="admin-performance-divider"></div>
        <div class="admin-performance-cell admin-performance-cell-status">
          <span class="admin-performance-label">{{
            t('admin.dashboard.performance.status')
          }}</span>
          <span class="admin-performance-status">{{ t('admin.dashboard.performance.optimized') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAdminStore } from '@/store/adminStore';
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
    [t('admin.dashboard.trends.series.newUsers')]: '#4A3728',
    [t('admin.dashboard.trends.series.newPhotos')]: '#E67E22',
    [t('admin.dashboard.trends.series.newReports')]: '#E74C3C',
    [t('admin.dashboard.trends.series.pointsEarned')]: '#FFD700',
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

const trendColors = ['#4A3728', '#E67E22', '#E74C3C'];
const monthlyColors = ['#5D4037', '#8D6E63', '#4CAF50'];
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

<style scoped>
.font-display {
  font-family: 'Outfit', sans-serif;
}

.admin-chart-card {
  margin-top: 1rem;
  background: white;
  padding: 1.25rem;
  border-radius: 1rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--color-sand-200);
  transition: all 0.2s ease;
}

.admin-chart-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.admin-chart-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-brown-900, #2d2420);
}

.admin-chart-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-brown-500, #8c7e7a);
}

.admin-chart-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.75rem;
}

.admin-chart-refresh {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  font-size: 0.625rem;
  font-weight: 700;
  color: var(--color-terracotta-600, #c05f35);
  background: white;
  border: 2px solid var(--color-terracotta-100, #f7ebe6);
  border-radius: 0.75rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.admin-chart-legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem 1.25rem;
  padding-right: 0.5rem;
  margin-top: 0.25rem;
}

.admin-chart-legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.admin-chart-legend-label {
  font-size: 0.6875rem;
  font-weight: 700;
  color: var(--color-brown-600, #57534e);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.admin-chart-loading-state,
.admin-chart-empty-state {
  min-height: 20rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 1rem;
  border: 1px dashed var(--color-sand-300);
}

.admin-chart-loading-state {
  background: var(--color-sand-50);
}

.admin-chart-loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: var(--color-brown-400, #a8a29e);
}

.admin-chart-empty-state {
  color: var(--color-brown-400, #a8a29e);
  font-style: italic;
  background: rgba(245, 245, 244, 0.35);
}

.admin-chart-empty-state-short {
  min-height: 16rem;
}

.admin-chart-host {
  min-height: 350px;
  overflow: hidden;
  transition: all 0.7s ease;
}

.admin-native-chart {
  width: 100%;
  min-height: 350px;
  color: var(--color-brown-500, #8c7e7a);
}

.admin-native-chart-short {
  min-height: 300px;
}

.admin-chart-grid line {
  stroke: #f1e9e4;
  stroke-dasharray: 4;
}

.admin-chart-line {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.admin-chart-point {
  r: 4;
  stroke: white;
  stroke-width: 2;
}

.admin-chart-bar {
  filter: drop-shadow(0 4px 8px rgba(45, 36, 32, 0.08));
}

.admin-chart-axis-labels text,
.admin-chart-axis-label {
  fill: var(--color-brown-400, #a8a29e);
  font-size: 11px;
  font-weight: 600;
}

.admin-chart-library-skeleton {
  min-height: 300px;
  border-radius: 1rem;
  background: linear-gradient(90deg, rgba(245, 245, 244, 0.8) 0%, rgba(255, 255, 255, 0.95) 50%, rgba(245, 245, 244, 0.8) 100%);
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}

.admin-chart-status {
  padding: 1rem 0;
  text-align: center;
  font-size: 0.625rem;
  color: var(--color-brown-400, #a8a29e);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  animation: pulse 1.5s infinite;
}

.admin-monthly-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

.admin-monthly-chart-skeleton,
.admin-monthly-table-skeleton {
  min-height: 300px;
  border-radius: 1rem;
  background: var(--color-sand-50);
  animation: pulse 1.5s infinite;
}

.admin-monthly-chart-panel {
  min-height: 300px;
}

.admin-monthly-table-panel {
  overflow: hidden;
  padding: 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(231, 229, 228, 0.8);
  background: rgba(250, 250, 249, 0.6);
}

.admin-monthly-table {
  width: 100%;
  min-width: 100%;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-brown-700, #44403c);
  border-collapse: collapse;
}

.admin-monthly-table-head {
  color: var(--color-brown-400, #a8a29e);
  font-size: 0.625rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.admin-monthly-table-body tr + tr {
  border-top: 1px solid rgba(231, 229, 228, 0.5);
}

.admin-monthly-table-row {
  transition: background-color 0.2s ease;
}

.admin-monthly-table-row:hover {
  background: rgba(255, 255, 255, 0.5);
}

.admin-monthly-table-month {
  padding: 0.5rem 0;
  font-weight: 700;
  color: var(--color-brown-900, #2d2420);
  text-transform: capitalize;
}

.admin-monthly-empty-state {
  padding: 3rem 0;
  text-align: center;
  color: var(--color-brown-400, #a8a29e);
  font-style: italic;
}

.admin-performance-panel {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 50;
  padding: 0.75rem 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 1rem;
  background: rgba(28, 25, 23, 0.95);
  color: #e7e5e4;
  backdrop-filter: blur(16px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.35);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  font-size: 0.6875rem;
  animation: fadeIn 0.3s ease;
}

.admin-performance-grid {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.admin-performance-cell {
  display: flex;
  flex-direction: column;
}

.admin-performance-cell-status {
  align-items: center;
}

.admin-performance-divider {
  width: 1px;
  height: 2rem;
  background: rgba(255, 255, 255, 0.2);
}

.admin-performance-label {
  font-size: 0.5625rem;
  font-weight: 700;
  color: #e7e5e4;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.admin-performance-value {
  font-size: 0.875rem;
  font-weight: 700;
  color: #e7e5e4;
}

.admin-performance-status {
  padding: 0.125rem 0.5rem;
  border: 1px solid rgba(74, 222, 128, 0.2);
  border-radius: 0.375rem;
  background: rgba(74, 222, 128, 0.1);
  color: #4ade80;
  font-weight: 700;
}

@media (min-width: 640px) {
  .admin-chart-header {
    flex-direction: row;
    align-items: center;
  }
}

@media (min-width: 1024px) {
  .admin-monthly-grid {
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  }
}
</style>
