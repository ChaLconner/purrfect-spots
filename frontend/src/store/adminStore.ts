import { defineStore } from 'pinia';
import { apiV1 } from '@/utils/api';

interface AdminStats {
  total_users: number;
  total_photos: number;
  pending_reports: number;
  total_reports: number;
}

export const useAdminStore = defineStore('admin', {
  state: () => ({
    stats: {
      total_users: 0,
      total_photos: 0,
      pending_reports: 0,
      total_reports: 0,
    } as AdminStats,
    isLoading: false,
    lastFetched: 0,
  }),
  actions: {
    async fetchStats(force: boolean = false) {
      const now = Date.now();
      // Cache for 30 seconds unless forced
      if (!force && this.stats.total_users > 0 && now - this.lastFetched < 30000) {
        return;
      }

      this.isLoading = true;
      try {
        const response = await apiV1.get<AdminStats>('/admin/stats');
        this.stats = response;
        this.lastFetched = now;
      } catch (error) {
        console.error('Failed to fetch admin stats:', error);
      } finally {
        this.isLoading = false;
      }
    },
  },
});
