import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import AdminDashboard from '@/views/admin/AdminDashboard.vue';
import { apiV1 } from '@/utils/api';
import { nextTick, defineComponent } from 'vue';
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
    (apiV1.get as ReturnType<typeof vi.fn>).mockImplementation(async (url: string): Promise<unknown> => {
       if (url === '/admin/summary') {
         return {
           stats: mockStats,
           trends: {
             users: [{ date: '2023-01-01', count: 5 }],
             photos: [{ date: '2023-01-01', count: 2 }],
             reports: [{ date: '2023-01-01', count: 1 }],
           },
           monthly: [],
           generated_at: new Date().toISOString()
         };
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

    const wrapper = shallowMount(AdminDashboard, {
      global: {
        plugins: [pinia],
        stubs: {
          apexchart: defineComponent({ template: '<div></div>' }),
          'router-link': true,
        },
      },
    });

    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();
    await nextTick();

    expect(apiV1.get).toHaveBeenCalledWith('/admin/summary');
    expect(wrapper.text()).toContain('100');
    expect(wrapper.text()).toContain('50');
    expect(wrapper.text()).toContain('5');
    expect(wrapper.text()).toContain('10');
  });

  it('handles loading state', async (): Promise<void> => {
    (apiV1.get as ReturnType<typeof vi.fn>).mockImplementation((): Promise<void> => new Promise((): void => {}));
    
    const wrapper = shallowMount(AdminDashboard, {
      global: {
        plugins: [pinia],
        stubs: {
          apexchart: defineComponent({ template: '<div></div>' }),
          'router-link': true,
        },
      },
    });
    await nextTick();
    expect(wrapper.html()).toContain('animate-pulse');
  });

  it('handles error state', async (): Promise<void> => {
    (apiV1.get as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Failed'));

    const wrapper = shallowMount(AdminDashboard, {
      global: {
        plugins: [pinia],
        stubs: {
          apexchart: defineComponent({ template: '<div></div>' }),
          'router-link': true,
        },
      },
    });
    
    await new Promise((resolve): void => { setTimeout(resolve, 0); });
    await nextTick();

    expect(wrapper.text()).toContain('admin.dashboard.monthly.error');
  });
});
