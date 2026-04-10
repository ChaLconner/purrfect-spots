import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { nextTick } from 'vue';
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
  let authStore: ReturnType<typeof useAuthStore>;
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    authStore = useAuthStore();
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const mountButton = (props = {}) => {
    return mount(LikeButton, {
      props: {
        photoId: 'photo-1',
        initialLiked: false,
        initialCount: 5,
        ...props,
      },
      global: {
        plugins: [pinia]
      }
    });
  };

  it('renders initial state', () => {
    const wrapper = mountButton();
    expect(wrapper.text()).toContain('5');
    expect(wrapper.find('svg').classes()).toContain('stroke-current');
  });

  it('shows toast for unauthenticated users', async () => {
    // isAuthenticated defaults to false
    const wrapper = mountButton();

    await wrapper.find('button').trigger('click');
    await nextTick();

    // Count stays unchanged, API never called
    expect(wrapper.text()).toContain('5');
    expect(SocialService.toggleLike).not.toHaveBeenCalled();
  });

  it('updates optimistically when clicked', async () => {
    // Modify the store BEFORE mounting or ensure reactivity works
    (authStore as any).isAuthenticated = true;
    const wrapper = mountButton();

    await wrapper.find('button').trigger('click');
    // We might need an extra tick or to advance timers if there's any async logic
    await nextTick();

    expect(wrapper.text()).toContain('6');
    expect(wrapper.find('svg').classes()).toContain('fill-current');
    expect(wrapper.emitted('update:liked')?.[0]).toEqual([true]);
    expect(wrapper.emitted('update:count')?.[0]).toEqual([6]);
  });

  it('debounces API call', async () => {
    (authStore as any).isAuthenticated = true;
    const wrapper = mountButton();
    vi.mocked(SocialService.toggleLike).mockResolvedValue({ liked: true, likes_count: 1 } as any);

    await wrapper.find('button').trigger('click');
    await nextTick();
    expect(SocialService.toggleLike).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(300);
    expect(SocialService.toggleLike).toHaveBeenCalledWith('photo-1');
  });

  it('rolls back on API error', async () => {
    (authStore as any).isAuthenticated = true;
    const wrapper = mountButton();
    vi.mocked(SocialService.toggleLike).mockRejectedValue(new Error('API failed'));

    await wrapper.find('button').trigger('click');
    await nextTick();
    expect(wrapper.text()).toContain('6'); // Optimistic change

    // Advance past the debounce timer so the API call fires
    await vi.advanceTimersByTimeAsync(300);
    // Let the rejected promise settle
    await nextTick();
    await nextTick();

    expect(wrapper.text()).toContain('5'); // Rolled back
  });

  it('subscribes to realtime updates on mount', async () => {
    const { supabase } = await import('@/lib/supabase');
    mountButton();
    expect(supabase.channel).toHaveBeenCalledWith('photo_likes_photo-1');
  });
});
