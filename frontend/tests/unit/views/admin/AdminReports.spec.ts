import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AdminReports from '@/views/admin/AdminReports.vue';
import { apiV1 } from '@/utils/api';
import { nextTick } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '@/store/authStore';

vi.mock('@/utils/api', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    apiV1: {
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
  };
});

vi.mock('@/constants/moderation', async (importOriginal) => {
  const actual: any = await importOriginal();
  return {
    ...actual,
    RESOLUTION_REASONS: [{ value: 'spam', label: 'Violation: Spam or Misleading', type: 'resolved' }]
  };
});

describe('AdminReports.vue', () => {
  let pinia: any;

  beforeEach(() => {
    vi.clearAllMocks();
    pinia = createPinia();
    setActivePinia(pinia);
    const authStore = useAuthStore();
    authStore.user = { id: 'admin1', email: 'admin@test.com', permissions: ['content:delete'] } as any;
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
    (apiV1.get as any).mockResolvedValue({ data: mockReports, total: 1 });

    const wrapper = mount(AdminReports, {
      global: { plugins: [pinia] }
    });
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(apiV1.get).toHaveBeenCalledWith(expect.stringContaining('/admin/reports'));
    expect(wrapper.text()).toContain('user@example.com');
    expect(wrapper.text()).toContain('spam');
  });

  it('opens modal on action click', async () => {
    (apiV1.get as any).mockResolvedValue({ data: mockReports, total: 1 });
    const wrapper = mount(AdminReports, {
      global: { plugins: [pinia] }
    });
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
    (apiV1.get as any).mockResolvedValue({ data: mockReports, total: 1 });
    const wrapper = mount(AdminReports, {
      global: { plugins: [pinia] }
    });
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    // Open Modal
    const resolveBtn = wrapper.findAll('button').find((b) => b.attributes('title') === 'Mark as Resolved');
    await resolveBtn?.trigger('click');

    // Verify options exist - we need to find the modal select, which is the third one now
    const selects = wrapper.findAll('select');
    expect(selects.length).toBe(3);
    const reasonSelect = selects[2];
    
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
