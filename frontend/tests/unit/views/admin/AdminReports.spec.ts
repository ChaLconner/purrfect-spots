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
      post: vi.fn(),
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
    authStore.user = {
      id: 'admin1',
      email: 'admin@test.com',
      permissions: ['reports:update', 'reports:read'],
    } as any;
    
    // Default mock response for apiV1.get
    (apiV1.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [], total: 0 });
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
     
     // Wait for multiple ticks for async loadData to complete
     await nextTick();
     await nextTick();
     await new Promise(r => setTimeout(r, 50));
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
     
     await nextTick();
     await nextTick();
     await new Promise(r => setTimeout(r, 50));
     
     // Finding by text content of the button since titles might be translated
     const buttons = wrapper.findAll('button');
     const resolveBtn = buttons.find(b => b.text().includes('Resolve'));
     
     expect(resolveBtn?.exists()).toBe(true);
     await resolveBtn?.trigger('click');
  
     expect(wrapper.find('#resolution-reason').exists()).toBe(true);
   });

  it('completes resolution flow', async (): Promise<void> => {
    (apiV1.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockReports, total: 1 });
    (apiV1.put as ReturnType<typeof vi.fn>).mockResolvedValue({ success: true });
    
     const wrapper = mount(AdminReports, {
       global: { plugins: [pinia] }
     });
     
     await nextTick();
     await nextTick();
     await new Promise(r => setTimeout(r, 50));
  
     // Open Modal
     const buttons = wrapper.findAll('button');
     const resolveBtn = buttons.find(b => b.text().includes('Resolve'));
     await resolveBtn?.trigger('click');
     await nextTick();
  
     // Select Reason
     const reasonSelect = wrapper.find('#resolution-reason');
     expect(reasonSelect.exists()).toBe(true);
     
     // The options are populated asynchronously or from constants
     await reasonSelect.setValue('violation_spam'); 
  
     // Add Note
     const textarea = wrapper.find('textarea');
     await textarea.setValue('Confirmed spam');
  
     // Click Confirm
     const confirmBtn = wrapper.findAll('button').find((b) => b.text().includes('Confirm'));
     await confirmBtn?.trigger('click');
  
     expect(apiV1.put).toHaveBeenCalledWith('/admin/reports/r1', expect.objectContaining({
       status: 'resolved',
       resolution_notes: expect.stringContaining('Confirmed spam')
     }));
   });
});
