import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import LikeButton from '@/components/social/LikeButton.vue';
import { SocialService } from '@/services/socialService';
import { useAuthStore } from '@/store';

vi.mock('@/services/socialService', () => ({
  SocialService: {
    toggleLike: vi.fn(),
  },
}));

vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn().mockReturnValue({
      on: vi.fn().mockReturnThis(),
      subscribe: vi.fn().mockReturnThis(),
    }),
    removeChannel: vi.fn(),
  },
}));

describe('LikeButton.vue', () => {
  let authStore: any;

  beforeEach(() => {
    setActivePinia(createPinia());
    authStore = useAuthStore();
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  const mountButton = (props = {}) => {
    return mount(LikeButton, {
      props: {
        photoId: 'photo-1',
        initialLiked: false,
        initialCount: 5,
        ...props,
      },
    });
  };

  it('renders initial state', () => {
    const wrapper = mountButton();
    expect(wrapper.text()).toContain('5');
    expect(wrapper.find('svg').classes()).toContain('stroke-current');
  });

  it('shows toast for unauthenticated users', async () => {
    authStore.isAuthenticated = false;
    const wrapper = mountButton();
    
    await wrapper.find('button').trigger('click');
    
    // Check if toast store was called (via mock if we mocked it, but here we just check if SocialService NOT called)
    expect(SocialService.toggleLike).not.toHaveBeenCalled();
  });

  it('updates optimistically when clicked', async () => {
    authStore.isAuthenticated = true;
    const wrapper = mountButton();
    
    await wrapper.find('button').trigger('click');
    
    expect(wrapper.text()).toContain('6');
    expect(wrapper.find('svg').classes()).toContain('fill-current');
    expect(wrapper.emitted('update:liked')?.[0]).toEqual([true]);
    expect(wrapper.emitted('update:count')?.[0]).toEqual([6]);
  });

  it('debounces API call', async () => {
    authStore.isAuthenticated = true;
    const wrapper = mountButton();
    vi.mocked(SocialService.toggleLike).mockResolvedValue({ liked: true, likes_count: 6 });

    await wrapper.find('button').trigger('click');
    expect(SocialService.toggleLike).not.toHaveBeenCalled();

    vi.advanceTimersByTime(300);
    expect(SocialService.toggleLike).toHaveBeenCalledWith('photo-1');
  });

  it('rolls back on API error', async () => {
    authStore.isAuthenticated = true;
    const wrapper = mountButton();
    vi.mocked(SocialService.toggleLike).mockRejectedValue(new Error('API failed'));

    await wrapper.find('button').trigger('click'); // Optimistic change to 6
    expect(wrapper.text()).toContain('6');

    vi.advanceTimersByTime(300);
    // Wait for promise to resolve
    await vi.runAllTimersAsync();
    
    expect(wrapper.text()).toContain('5');
  });

  it('subscribes to realtime updates on mount', async () => {
    // Import from the actual path relative to the test or use vi.mocked reference
    const { supabase } = await import('@/lib/supabase');
    mountButton();
    expect(supabase.channel).toHaveBeenCalledWith('photo_likes_photo-1');
  });
});
