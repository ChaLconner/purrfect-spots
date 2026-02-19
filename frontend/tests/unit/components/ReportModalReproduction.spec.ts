import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import CatDetailModal from '@/components/map/CatDetailModal.vue';
import { createTestingPinia } from '@pinia/testing';
import { useAuthStore } from '@/store/authStore';
import { useSubscriptionStore } from '@/store/subscriptionStore';

// Mock Supabase to avoid initialization errors
vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn(() => ({
      on: vi.fn().mockReturnThis(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    })),
    removeChannel: vi.fn(),
  },
}));

// Mock SocialService
vi.mock('@/services/socialService', () => ({
  SocialService: {
    toggleLike: vi.fn(),
  },
}));

// Mock ReportModal - we want to spy on its props
const ReportModalMock = {
  name: 'ReportModal',
  props: ['isOpen', 'photoId'],
  template: '<div v-if="isOpen" data-test="report-modal">Report Modal</div>',
};



describe('CatDetailModal Report Integration', () => {
  const mockCat = {
    id: 'cat-123',
    user_id: 'user-456', // Different from current user
    image_url: 'http://example.com/cat.jpg',
    location_name: 'Test Spot',
    description: 'A test cat',
    coordinates: { lat: 0, lng: 0 },
    created_at: new Date().toISOString(),
    likes_count: 5,
    liked: false,
  };

  const currentUser = {
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User',
    treat_balance: 10,
  };

  it('renders report button for authenticated user viewing another user\'s cat', async () => {
    const wrapper = mount(CatDetailModal, {
      props: {
        cat: mockCat,
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: {
                user: currentUser,
                isAuthenticated: true,
              },
            },
          }),
        ],
        context: {
          components: {
            ReportModal: ReportModalMock,
          }
        },
        stubs: {
          ReportModal: ReportModalMock,
          LikeButton: true, // Stub LikeButton
        }
      },
    });

    const authStore = useAuthStore();
    // Ensure auth state is correct
    authStore.isAuthenticated = true;
    authStore.user = currentUser;

    // Check if report button exists
    const reportBtn = wrapper.find('.report-btn');
    expect(reportBtn.exists()).toBe(true);
  });

  it('opens report modal when report button is clicked', async () => {
    const wrapper = mount(CatDetailModal, {
      props: {
        cat: mockCat,
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: {
                user: currentUser,
                isAuthenticated: true,
              },
            },
          }),
        ],
        stubs: {
          ReportModal: ReportModalMock,
          LikeButton: true,
        },
      },
    });

    const reportBtn = wrapper.find('.report-btn');
    await reportBtn.trigger('click');

    // Check if ReportModal (stub) is visible/rendered with isOpen=true
    const reportModal = wrapper.findComponent(ReportModalMock);
    expect(reportModal.exists()).toBe(true);
    expect(reportModal.props('isOpen')).toBe(true);
    expect(reportModal.props('photoId')).toBe('cat-123');
  });

  it('does not render report button for own cat', async () => {
    const ownCat = { ...mockCat, user_id: currentUser.id };
    
    const wrapper = mount(CatDetailModal, {
      props: {
        cat: ownCat,
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: {
                user: currentUser,
                isAuthenticated: true,
              },
            },
          }),
        ],
        stubs: {
          ReportModal: ReportModalMock,
          LikeButton: true,
        },
      },
    });

    const reportBtn = wrapper.find('.report-btn');
    expect(reportBtn.exists()).toBe(false);
  });
});
