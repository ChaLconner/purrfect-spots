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
  }),
  actions: {
    async fetchMonthlyStats(force: boolean = false, year?: number) {
      const now = Date.now();
      if (!force && this.monthlyData.length > 0 && now - this.lastMonthlyFetched < 600000) {
        return;
      }

      this.isMonthlyLoading = true;
      try {
        const response = await apiV1.get<{ data: MonthlyStat[]; year: number }>(
          `/admin/stats/monthly${year ? `?year=${year}` : ''}`
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
        const response = await apiV1.get<AdminStats>('/admin/stats');
        this.stats = response;
        this.lastFetched = now;
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
        const response = await apiV1.get<AdminTrends>('/admin/stats/trends');
        this.trends = response;
        this.lastTrendsFetched = now;
        this.trendsLoadTime = Math.round(performance.now() - start);
      } catch (error) {
        console.error('Failed to fetch admin trends:', error);
      } finally {
        this.isTrendsLoading = false;
      }
    },

    subscribeToReports() {
      if (this.reportChannel) return;

      this.reportChannel = supabase
        .channel('admin-reports')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'reports' }, () => {
          // Re-fetch stats when reports change for accurate counts
          // Using force=true ensures we bypass cache
          this.fetchStats(true);
        })
        .subscribe();
    },

    unsubscribeReports() {
      if (this.reportChannel) {
        this.reportChannel.unsubscribe();
        this.reportChannel = null;
      }
    },
  },
});
