import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAdminStore } from '@/store/adminStore';

// Mock apiV1
const mockApiGet = vi.fn();
vi.mock('@/utils/api', () => ({
  apiV1: {
    get: (...args: any[]) => mockApiGet(...args)
  }
}));

const makeSummaryResponse = (stats: Record<string, unknown>) => ({
  stats,
  trends: { users: [], photos: [], reports: [] },
  monthly: [],
  generated_at: new Date().toISOString()
});

describe('Admin Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('initializes with zero stats', () => {
    const store = useAdminStore();
    expect(store.stats.total_users).toBe(0);
    expect(store.isLoading).toBe(false);
  });

  it('fetchStats updates state and respects cache', async () => {
    const store = useAdminStore();
    const mockStats = {
      total_users: 100,
      total_photos: 500,
      pending_reports: 5,
      total_reports: 50
    };

    mockApiGet.mockResolvedValueOnce(makeSummaryResponse(mockStats));

    await store.fetchStats();

    expect(store.stats).toEqual(mockStats);
    expect(store.isLoading).toBe(false);
    expect(mockApiGet).toHaveBeenCalledTimes(1);

    // Call again - should use cache (stats.total_users > 0)
    await store.fetchStats();
    expect(mockApiGet).toHaveBeenCalledTimes(1);

    // Force fetch
    mockApiGet.mockResolvedValueOnce(makeSummaryResponse(mockStats));
    await store.fetchStats(true);
    expect(mockApiGet).toHaveBeenCalledTimes(2);
  });

  it('handles fetch errors gracefully', async () => {
    const store = useAdminStore();
    mockApiGet.mockRejectedValue(new Error('API Error'));
    
    await store.fetchStats();
    
    expect(store.isLoading).toBe(false);
    expect(store.stats.total_users).toBe(0);
  });
});
