import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAdminStore } from '@/store/adminStore';

// Mock apiV1
const mockApiGet = vi.fn();
const mockSubscribe = vi.fn();
const mockChannelOn = vi.fn();
const mockUnsubscribe = vi.fn();
let reportInsertHandler: (() => void) | null = null;

vi.mock('@/utils/api', () => ({
  apiV1: {
    get: (...args: any[]) => mockApiGet(...args)
  }
}));

vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn(() => ({
      on: mockChannelOn,
      subscribe: mockSubscribe,
      unsubscribe: mockUnsubscribe,
    })),
  },
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
    vi.useFakeTimers();
    reportInsertHandler = null;
    mockChannelOn.mockImplementation((_event, _filter, handler) => {
      reportInsertHandler = handler;
      return { subscribe: mockSubscribe };
    });
    mockSubscribe.mockImplementation(() => ({
      unsubscribe: mockUnsubscribe,
    }));
  });

  afterEach(() => {
    vi.useRealTimers();
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

  it('fetchSummary updates all metrics', async () => {
    const store = useAdminStore();
    const mockResponse = {
      stats: { total_users: 10, total_photos: 20, pending_reports: 1, total_reports: 5 },
      trends: { users: [{ date: '2024-01-01', count: 1 }], photos: [], reports: [] },
      monthly: [{ month_timestamp: '2024-01-01', new_users: 5, new_photos: 10, resolved_reports: 2, points_earned: 100 }],
      generated_at: new Date().toISOString()
    };

    mockApiGet.mockResolvedValueOnce(mockResponse);

    await store.fetchSummary();

    expect(store.stats).toEqual(mockResponse.stats);
    expect(store.trends).toEqual(mockResponse.trends);
    expect(store.monthlyData).toEqual(mockResponse.monthly);
    expect(store.lastFetched).toBeGreaterThan(0);
    expect(store.isLoading).toBe(false);
  });

  it('fetchTrends respects cache', async () => {
    const store = useAdminStore();
    store.trends = { users: [{ date: '2024-01-01', count: 1 }], photos: [], reports: [] };
    store.lastTrendsFetched = Date.now();

    await store.fetchTrends();
    expect(mockApiGet).not.toHaveBeenCalled();

    mockApiGet.mockResolvedValueOnce({ users: [], photos: [], reports: [] });
    await store.fetchTrends(true);
    expect(mockApiGet).toHaveBeenCalled();
  });

  it('fetchMonthlyStats respects cache and params', async () => {
    const store = useAdminStore();
    store.monthlyData = [{ month_timestamp: '2024-01-01' } as any];
    store.lastMonthlyFetched = Date.now();

    await store.fetchMonthlyStats();
    expect(mockApiGet).not.toHaveBeenCalled();

    mockApiGet.mockResolvedValueOnce({ data: [], year: 2024 });
    await store.fetchMonthlyStats(true, 2024);
    expect(mockApiGet).toHaveBeenCalledWith(expect.stringContaining('year=2024'));
  });

  it('manages realtime subscriptions', () => {
    const store = useAdminStore();
    
    // Test subscription starts
    store.subscribeToReports();
    expect(store.reportChannel).not.toBeNull();
    
    // Test unsubscription cleans up
    store.unsubscribeReports();
    expect(store.reportChannel).toBeNull();
  });

  it('increments pending reports immediately and forces a debounced refresh on realtime insert', async () => {
    const store = useAdminStore();
    store.stats.pending_reports = 2;
    const fetchStatsSpy = vi.spyOn(store, 'fetchStats').mockResolvedValue(undefined as never);

    store.subscribeToReports();
    reportInsertHandler?.();

    expect(store.stats.pending_reports).toBe(3);
    expect(fetchStatsSpy).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(5000);

    expect(fetchStatsSpy).toHaveBeenCalledWith(true);
  });

  it('skips realtime subscriptions when disabled', () => {
    const store = useAdminStore();

    store.subscribeToReports(false);

    expect(store.reportChannel).toBeNull();
  });
});

