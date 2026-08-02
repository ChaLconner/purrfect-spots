import { defineStore } from 'pinia';
import { apiV1 } from '@/utils/api';
import { supabase } from '@/lib/supabase';
import { isDev } from '@/utils/env';

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
    error: null as string | null,
    lastFetched: 0,
    lastTrendsFetched: 0,
    lastMonthlyFetched: 0,
    // Performance benchmarking
    statsLoadTime: 0,
    trendsLoadTime: 0,
    showPerformanceStats: localStorage.getItem('admin_show_perf_stats') !== 'false',
    reportChannel: null as ReturnType<typeof supabase.channel> | null,
    _realtimeDebounceTimer: null as ReturnType<typeof setTimeout> | null,
    _lastRealtimeForcedSyncAt: 0,
    _requestSequence: 0,
  }),
  actions: {
    togglePerformanceStats(show?: boolean) {
      this.showPerformanceStats = show !== undefined ? show : !this.showPerformanceStats;
      localStorage.setItem('admin_show_perf_stats', String(this.showPerformanceStats));
    },

    async fetchSummary(force: boolean = false) {
      const now = Date.now();
      if (!force && this.lastFetched > 0 && now - this.lastFetched < 30000) {
        return;
      }

      this.isLoading = true;
      this.isTrendsLoading = true;
      this.isMonthlyLoading = true;
      this.error = null;
      const currentSeq = ++this._requestSequence;
      const start = performance.now();
      try {
        const response = await apiV1.get<{
          stats: AdminStats;
          trends: AdminTrends;
          monthly: MonthlyStat[];
          generated_at: string;
        }>('/admin/summary');

        if (currentSeq !== this._requestSequence) return;

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
        if (currentSeq === this._requestSequence) {
          this.error = error instanceof Error ? error.message : 'Failed to fetch summary';
        }
        if (isDev()) {
          console.error('Failed to fetch admin dashboard summary:', error);
        }
      } finally {
        if (currentSeq === this._requestSequence) {
          this.isLoading = false;
          this.isTrendsLoading = false;
          this.isMonthlyLoading = false;
        }
      }
    },

    async fetchMonthlyStats(force: boolean = false, year?: number) {
      const now = Date.now();
      if (!force && this.monthlyData.length > 0 && now - this.lastMonthlyFetched < 600000) {
        return;
      }

      this.isMonthlyLoading = true;
      this.error = null;
      try {
        const response = await apiV1.get<{ data: MonthlyStat[]; year: number }>(
          `/admin/monthly${year ? `?year=${year}` : ''}`
        );
        this.monthlyData = response.data;
        this.lastMonthlyFetched = now;
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to fetch monthly stats';
        if (isDev()) {
          console.error('Failed to fetch monthly stats:', error);
        }
      } finally {
        this.isMonthlyLoading = false;
      }
    },

    async fetchStats(force: boolean = false) {
      const now = Date.now();
      if (!force && this.stats.total_users > 0 && now - this.lastFetched < 30000) {
        return;
      }

      this.isLoading = true;
      this.error = null;
      const currentSeq = ++this._requestSequence;
      const start = performance.now();
      try {
        const response = await apiV1.get<{
          stats: AdminStats;
          trends: AdminTrends;
          monthly: MonthlyStat[];
        }>('/admin/summary');

        if (currentSeq !== this._requestSequence) return;

        this.stats = response.stats;
        this.trends = response.trends;
        this.monthlyData = response.monthly;

        this.lastFetched = now;
        this.lastTrendsFetched = now;
        this.lastMonthlyFetched = now;

        this.statsLoadTime = Math.round(performance.now() - start);
      } catch (error) {
        if (currentSeq === this._requestSequence) {
          this.error = error instanceof Error ? error.message : 'Failed to fetch stats';
        }
        if (isDev()) {
          console.error('Failed to fetch admin stats:', error);
        }
      } finally {
        if (currentSeq === this._requestSequence) {
          this.isLoading = false;
        }
      }
    },

    async fetchTrends(force: boolean = false) {
      const now = Date.now();
      if (!force && this.trends.users.length > 0 && now - this.lastTrendsFetched < 300000) {
        return;
      }

      this.isTrendsLoading = true;
      this.error = null;
      const start = performance.now();
      try {
        const response = await apiV1.get<AdminTrends>('/admin/trends');
        this.trends = response;
        this.lastTrendsFetched = now;
        this.trendsLoadTime = Math.round(performance.now() - start);
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to fetch trends';
        if (isDev()) {
          console.error('Failed to fetch admin trends:', error);
        }
      } finally {
        this.isTrendsLoading = false;
      }
    },

    subscribeToReports(enabled: boolean = true) {
      if (!enabled || this.reportChannel) return;

      this.reportChannel = supabase
        .channel('admin-reports')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'reports' }, () => {
          this.stats.pending_reports += 1;
          if (this._realtimeDebounceTimer) clearTimeout(this._realtimeDebounceTimer);
          this._realtimeDebounceTimer = setTimeout(() => {
            const now = Date.now();
            if (now - this._lastRealtimeForcedSyncAt < 30000) {
              return;
            }
            this._lastRealtimeForcedSyncAt = now;
            void this.fetchSummary(true);
          }, 5000);
        })
        .subscribe();
    },

    unsubscribeReports() {
      if (this._realtimeDebounceTimer) {
        clearTimeout(this._realtimeDebounceTimer);
        this._realtimeDebounceTimer = null;
      }
      this._lastRealtimeForcedSyncAt = 0;
      if (this.reportChannel) {
        this.reportChannel.unsubscribe();
        if (typeof (supabase as unknown as { removeChannel?: (ch: unknown) => void }).removeChannel === 'function') {
          void (supabase as unknown as { removeChannel: (channel: unknown) => Promise<unknown> }).removeChannel(this.reportChannel);
        }
        this.reportChannel = null;
      }
    },
  },
});
