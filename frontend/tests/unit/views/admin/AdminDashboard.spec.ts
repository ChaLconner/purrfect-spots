import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AdminDashboard from '@/views/admin/AdminDashboard.vue';
import { apiV1 } from '@/utils/api';
import { nextTick } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { useAdminStore } from '@/store/adminStore';

vi.mock('@/utils/api', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    apiV1: {
      get: vi.fn(),
    },
  };
});

describe('AdminDashboard.vue', () => {
  let pinia: any;

  beforeEach(() => {
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

  it('renders stats correctly', async () => {
    // Mock api implementation
    (apiV1.get as any).mockResolvedValue(mockStats);

    const wrapper = mount(AdminDashboard, {
      global: { plugins: [pinia] }
    });

    // Wait for mounted hook
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(apiV1.get).toHaveBeenCalledWith('/admin/stats');
    
    // Check if new stats are displayed
    expect(wrapper.text()).toContain('Total Users');
    expect(wrapper.text()).toContain('100');
    
    expect(wrapper.text()).toContain('Total Photos');
    expect(wrapper.text()).toContain('50');

    expect(wrapper.text()).toContain('Pending Reports');
    expect(wrapper.text()).toContain('5');

    expect(wrapper.text()).toContain('Total Reports');
    expect(wrapper.text()).toContain('10');
  });

  it('handles loading state', async () => {
    // Return a promise that never resolves (or delays) to test loading state if needed
    (apiV1.get as any).mockImplementation(() => new Promise(() => {}));
    
    const wrapper = mount(AdminDashboard, {
      global: { plugins: [pinia] }
    });
    await nextTick();
    expect(wrapper.html()).toContain('animate-shimmer');
  });

  it('handles error state', async () => {
    (apiV1.get as any).mockRejectedValue(new Error('Failed'));

    const wrapper = mount(AdminDashboard, {
      global: { plugins: [pinia] }
    });
    
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(wrapper.text()).toContain('No stats available or failed to load.');
  });
});
