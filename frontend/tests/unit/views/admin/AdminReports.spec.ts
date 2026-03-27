import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AdminReports from '@/views/admin/AdminReports.vue';
import { apiV1 } from '@/utils/api';
import { nextTick } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '@/store/authStore';

vi.mock('@/utils/api', async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
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
  const actual: Record<string, unknown> = await importOriginal();
  return {
    ...actual,
    RESOLUTION_REASONS: [
      { value: 'violation_spam', label: 'Violation: Spam', type: 'resolved' },
      { value: 'invalid', label: 'Invalid report', type: 'dismissed' }
    ]
  };
});

describe('AdminReports.vue', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach((): void => {
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

  it('renders reports list correctly', async (): Promise<void> => {
    (apiV1.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockReports, total: 1 });
 
     const wrapper = mount(AdminReports, {
       global: { plugins: [pinia] }
     });
     await new Promise((resolve): void => { setTimeout(resolve, 0); });
     await nextTick();
 
     expect(apiV1.get).toHaveBeenCalledWith(expect.stringContaining('/admin/reports'));
     expect(wrapper.text()).toContain('user@example.com');
     expect(wrapper.text()).toContain('spam');
   });

  it('opens modal on action click', async (): Promise<void> => {
    (apiV1.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockReports, total: 1 });
     const wrapper = mount(AdminReports, {
       global: { plugins: [pinia] }
     });
     await new Promise((resolve): void => { setTimeout(resolve, 0); });
     await nextTick();
 
     const resolveBtn = wrapper.findAll('button').find((b) => b.attributes('title') === 'admin.reports.actions.resolve');
     expect(resolveBtn?.exists()).toBe(true);
     await resolveBtn?.trigger('click');
 
     // Modal should be visible
     expect(wrapper.text()).toContain('admin.reports.modal.resolveTitle');
     expect(wrapper.text()).toContain('admin.reports.modal.reasonLabel');
   });

  it('completes resolution flow', async (): Promise<void> => {
    (apiV1.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockReports, total: 1 });
     const wrapper = mount(AdminReports, {
       global: { plugins: [pinia] }
     });
     await new Promise((resolve): void => { setTimeout(resolve, 0); });
     await nextTick();
 
     // Open Modal
     const resolveBtn = wrapper.findAll('button').find((b) => b.attributes('title') === 'admin.reports.actions.resolve');
     await resolveBtn?.trigger('click');
 
     // Verify options exist - we need to find the modal select, which is the last select
     const selects = wrapper.findAll('select');
     expect(selects.length).toBeGreaterThanOrEqual(1);
     const reasonSelect = selects[selects.length - 1];
     
     const options = reasonSelect.findAll('option');
     expect(options.length).toBeGreaterThan(1);
     
     // Select Reason
     await reasonSelect.setValue('violation_spam'); 
 
     // Add Note
     const textarea = wrapper.find('textarea');
     await textarea.setValue('Confirmed spam');
 
     // Click Confirm
     const confirmBtn = wrapper.findAll('button').find((b) => b.text().includes('common.confirm'));
     await confirmBtn?.trigger('click');
 
     expect(apiV1.put).toHaveBeenCalledWith('/admin/reports/r1', expect.objectContaining({
       status: 'resolved',
       resolution_notes: expect.any(String), // The string format uses translation keys now, so any string matching translation outcome works
     }));
   });
 });
