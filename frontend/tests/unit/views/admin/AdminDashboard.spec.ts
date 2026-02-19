import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AdminDashboard from '@/views/admin/AdminDashboard.vue';
import { apiV1 } from '@/utils/api';
import { nextTick } from 'vue';

// Manually mock apiV1
vi.mock('@/utils/api', () => ({
  apiV1: {
    get: vi.fn(),
  },
}));

describe('AdminDashboard.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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

    const wrapper = mount(AdminDashboard);

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
    // But simplified test: initially isLoading becomes true
    (apiV1.get as any).mockImplementation(() => new Promise(() => {}));
    
    const wrapper = mount(AdminDashboard);
    await nextTick();
    expect(wrapper.text()).toContain('Loading stats...');
  });

  it('handles error state', async () => {
    (apiV1.get as any).mockRejectedValue(new Error('Failed'));

    const wrapper = mount(AdminDashboard);
    
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(wrapper.text()).toContain('Failed to load stats');
  });
});
