import { defineStore } from 'pinia';
import { apiV1 } from '@/utils/api';
import { supabase } from '@/lib/supabase';
import type { RealtimeChannel } from '@supabase/supabase-js';

interface AdminStats {
  total_users: number;
  total_photos: number;
  pending_reports: number;
  total_reports: number;
}

interface AdminTrends {
  users: { date: string; count: number }[];
  photos: { date: string; count: number }[];
  reports: { date: string; count: number }[];
}

interface MonthlyStat {
  month_timestamp: string;
  new_users: number;
  new_photos: number;
  resolved_reports: number;
  points_earned: number;
}

export const useAdminStore = defineStore('admin', {
  state: () => ({
    stats: {
      total_users: 0,
      total_photos: 0,
      pending_reports: 0,
      total_reports: 0,
    } as AdminStats,
    trends: {
      users: [],
      photos: [],
      reports: [],
    } as AdminTrends,
    monthlyData: [] as MonthlyStat[],
    isLoading: false,
    isTrendsLoading: false,
    isMonthlyLoading: false,
    lastFetched: 0,
    lastTrendsFetched: 0,
    lastMonthlyFetched: 0,
    // Performance benchmarking
    statsLoadTime: 0,
    trendsLoadTime: 0,
    showPerformanceStats: true,
    reportChannel: null as RealtimeChannel | null,
    _realtimeDebounceTimer: null as ReturnType<typeof setTimeout> | null,
  }),
  actions: {
    async fetchSummary(force: boolean = false) {
      const now = Date.now();
      // Cache for 30 seconds unless forced
      if (!force && this.lastFetched > 0 && now - this.lastFetched < 30000) {
        return;
      }

      this.isLoading = true;
      this.isTrendsLoading = true;
      this.isMonthlyLoading = true;
      const start = performance.now();
      try {
        const response = await apiV1.get<{
          stats: AdminStats;
          trends: AdminTrends;
          monthly: MonthlyStat[];
          generated_at: string;
        }>('/admin/summary');

        // Bulk update all dashboard metrics
        this.stats = response.stats;
        this.trends = response.trends;
        this.monthlyData = response.monthly;

        this.lastFetched = now;
        this.lastTrendsFetched = now;
        this.lastMonthlyFetched = now;

        const time = Math.round(performance.now() - start);
        this.statsLoadTime = time;
        this.trendsLoadTime = time;
      } catch (error) {
        console.error('Failed to fetch admin dashboard summary:', error);
      } finally {
        this.isLoading = false;
        this.isTrendsLoading = false;
        this.isMonthlyLoading = false;
      }
    },

    async fetchMonthlyStats(force: boolean = false, year?: number) {
      const now = Date.now();
      if (!force && this.monthlyData.length > 0 && now - this.lastMonthlyFetched < 600000) {
        return;
      }

      this.isMonthlyLoading = true;
      try {
        const response = await apiV1.get<{ data: MonthlyStat[]; year: number }>(
          `/admin/monthly${year ? `?year=${year}` : ''}`
        );
        this.monthlyData = response.data;
        this.lastMonthlyFetched = now;
      } catch (error) {
        console.error('Failed to fetch monthly stats:', error);
      } finally {
        this.isMonthlyLoading = false;
      }
    },

    async fetchStats(force: boolean = false) {
      const now = Date.now();
      // Cache for 30 seconds unless forced
      if (!force && this.stats.total_users > 0 && now - this.lastFetched < 30000) {
        return;
      }

      this.isLoading = true;
      const start = performance.now();
      try {
        // Redirection: /admin/stats was removed in backend cleanup.
        // We now use /admin/summary which returns the full dashboard dataset.
        const response = await apiV1.get<{
          stats: AdminStats;
          trends: AdminTrends;
          monthly: MonthlyStat[];
        }>('/admin/summary');

        // Populate everything since we have it
        this.stats = response.stats;
        this.trends = response.trends;
        this.monthlyData = response.monthly;

        this.lastFetched = now;
        this.lastTrendsFetched = now;
        this.lastMonthlyFetched = now;

        this.statsLoadTime = Math.round(performance.now() - start);
      } catch (error) {
        console.error('Failed to fetch admin stats:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async fetchTrends(force: boolean = false) {
      const now = Date.now();
      // Cache for 5 minutes for trends
      if (!force && this.trends.users.length > 0 && now - this.lastTrendsFetched < 300000) {
        return;
      }

      this.isTrendsLoading = true;
      const start = performance.now();
      try {
        const response = await apiV1.get<AdminTrends>('/admin/trends');
        this.trends = response;
        this.lastTrendsFetched = now;
        this.trendsLoadTime = Math.round(performance.now() - start);
      } catch (error) {
        console.error('Failed to fetch admin trends:', error);
      } finally {
        this.isTrendsLoading = false;
      }
    },

    subscribeToReports(enabled: boolean = true) {
      if (!enabled || this.reportChannel) return;

      this.reportChannel = supabase
        .channel('admin-reports')
        // FIX: Listen only to INSERT (new reports), not UPDATE/DELETE
        // to avoid unnecessary refreshes on resolution/dismissal actions.
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'reports' }, () => {
          // FIX: Debounce to avoid backend hammering when multiple reports arrive quickly.
          // Reflect new pending work immediately in the sidebar badge, then
          // force a refresh so server truth reconciles counts and related stats.
          this.stats.pending_reports += 1;
          if (this._realtimeDebounceTimer) clearTimeout(this._realtimeDebounceTimer);
          this._realtimeDebounceTimer = setTimeout(() => {
            void this.fetchStats(true);
          }, 5000);
        })
        .subscribe();
    },

    unsubscribeReports() {
      if (this._realtimeDebounceTimer) {
        clearTimeout(this._realtimeDebounceTimer);
        this._realtimeDebounceTimer = null;
      }
      if (this.reportChannel) {
        this.reportChannel.unsubscribe();
        this.reportChannel = null;
      }
    },
  },
});
