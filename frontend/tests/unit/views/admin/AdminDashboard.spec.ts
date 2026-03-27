import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AdminDashboard from '@/views/admin/AdminDashboard.vue';
import { apiV1 } from '@/utils/api';
import { nextTick } from 'vue';
import { createPinia, setActivePinia } from 'pinia';


vi.mock('@/utils/api', async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    apiV1: {
      get: vi.fn(),
    },
  };
});

describe('AdminDashboard.vue', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach((): void => {
    vi.clearAllMocks();
    pinia = createPinia();
    setActivePinia(pinia);
  });

  const mockStats = {
    total_users: 100,
    total_photos: 50,
    pending_reports: 5,
    total_reports: 10,
    generated_at: new Date().toISOString(),
  };

  it('renders stats correctly', async (): Promise<void> => {
    // Mock api implementation
    (apiV1.get as ReturnType<typeof vi.fn>).mockImplementation(async (url: string): Promise<unknown> => {
       if (url === '/admin/stats') {
         return mockStats;
       }
       if (url === '/admin/stats/trends') {
         return {
           users: [{ date: '2023-01-01', count: 5 }],
           photos: [{ date: '2023-01-01', count: 2 }],
           reports: [{ date: '2023-01-01', count: 1 }],
         };
       }
       if (url.startsWith('/admin/stats/monthly')) {
         return { data: [] };
       }
       return {};
     });

    const wrapper = mount(AdminDashboard, {
      global: { plugins: [pinia] }
    });

    // Wait for mounted hook
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(apiV1.get).toHaveBeenCalledWith('/admin/stats');
    
    // Check if new stats are displayed
    expect(wrapper.text()).toContain('admin.dashboard.stats.totalUsers');
    expect(wrapper.text()).toContain('100');
    
    expect(wrapper.text()).toContain('admin.dashboard.stats.totalPhotos');
    expect(wrapper.text()).toContain('50');

    expect(wrapper.text()).toContain('admin.dashboard.stats.pendingReports');
    expect(wrapper.text()).toContain('5');

    expect(wrapper.text()).toContain('admin.dashboard.stats.totalReports');
    expect(wrapper.text()).toContain('10');
  });

  it('handles loading state', async (): Promise<void> => {
     // Return a promise that never resolves (or delays) to test loading state if needed
     (apiV1.get as ReturnType<typeof vi.fn>).mockImplementation((): Promise<void> => new Promise((): void => {}));
     
     const wrapper = mount(AdminDashboard, {
       global: { plugins: [pinia] }
     });
     await nextTick();
     expect(wrapper.html()).toContain('animate-shimmer');
   });
 
   it('handles error state', async (): Promise<void> => {
     (apiV1.get as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Failed'));
 
     const wrapper = mount(AdminDashboard, {
       global: { plugins: [pinia] }
     });
     
     await new Promise((resolve): void => { setTimeout(resolve, 0); });
     await nextTick();
 
     expect(wrapper.text()).toContain('admin.dashboard.monthly.error');
   });
 });
