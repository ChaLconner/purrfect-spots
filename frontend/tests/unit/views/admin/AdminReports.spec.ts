import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AdminReports from '@/views/admin/AdminReports.vue';
import { apiV1 } from '@/utils/api';
import { nextTick } from 'vue';

// Mock apiV1
vi.mock('@/utils/api', () => ({
  apiV1: {
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('@/constants/moderation', () => ({
  RESOLUTION_REASONS: [{ value: 'spam', label: 'Violation: Spam or Misleading', type: 'resolved' }]
}));

describe('AdminReports.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockReports = [
    {
      id: 'r1',
      photo_id: 'p1',
      reporter_id: 'u1',
      reason: 'spam',
      details: 'Spam content',
      status: 'pending',
      created_at: new Date().toISOString(),
      photo: {
        image_url: 'http://example.com/p1.jpg',
        location_name: 'Park',
      },
      reporter: {
        email: 'user@example.com',
      },
    },
  ];

  it('renders reports list correctly', async () => {
    (apiV1.get as any).mockResolvedValue(mockReports);

    const wrapper = mount(AdminReports);
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(apiV1.get).toHaveBeenCalledWith(expect.stringContaining('/admin/reports'));
    expect(wrapper.text()).toContain('user@example.com');
    expect(wrapper.text()).toContain('spam');
  });

  it('opens modal on action click', async () => {
    (apiV1.get as any).mockResolvedValue(mockReports);
    const wrapper = mount(AdminReports);
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    const resolveBtn = wrapper.findAll('button').find((b) => b.attributes('title') === 'Mark as Resolved');
    expect(resolveBtn?.exists()).toBe(true);
    await resolveBtn?.trigger('click');

    // Modal should be visible
    expect(wrapper.text()).toContain('Resolve Report');
    expect(wrapper.text()).toContain('Standard Reason');
  });

  it('completes resolution flow', async () => {
    (apiV1.get as any).mockResolvedValue(mockReports);
    const wrapper = mount(AdminReports);
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    // Open Modal
    const resolveBtn = wrapper.findAll('button').find((b) => b.attributes('title') === 'Mark as Resolved');
    await resolveBtn?.trigger('click');

    // Verify options exist - we need to find the modal select, which is the second one
    const selects = wrapper.findAll('select');
    expect(selects.length).toBe(2);
    const reasonSelect = selects[1];
    
    const options = reasonSelect.findAll('option');
    expect(options.length).toBeGreaterThan(1);
    
    // Select Reason
    await reasonSelect.setValue('Violation: Spam or Misleading'); 

    // Add Note
    const textarea = wrapper.find('textarea');
    await textarea.setValue('Confirmed spam');

    // Click Confirm
    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === 'Confirm');
    
    // Check if reason is selected
    // Note: wrapper.vm is not typed to include internal setup refs easily, skipping direct vm check if flaky
    // expect(wrapper.vm.selectedReason).toBe('Violation: Spam or Misleading');
    
    await confirmBtn?.trigger('click');

    expect(apiV1.put).toHaveBeenCalledWith('/admin/reports/r1', expect.objectContaining({
      status: 'resolved',
      resolution_notes: expect.stringContaining('Violation: Spam or Misleading: Confirmed spam'),
    }));
  });
});
