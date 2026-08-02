import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import LeaderboardView from '@/views/LeaderboardView.vue';
import { TreatsService } from '@/services/treatsService';

vi.mock('@/components/profile/ProfileDrawer.vue', () => ({
  default: {
    name: 'ProfileDrawer',
    template: '<div></div>',
  },
}));

vi.mock('@/services/treatsService', () => ({
  TreatsService: {
    getLeaderboard: vi.fn(),
  },
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock('@/composables/useSeo', () => ({
  useSeo: () => ({
    setMetaTags: vi.fn(),
  }),
}));

vi.mock('@/stores/toast', () => ({
  showError: vi.fn(),
}));

describe('LeaderboardView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('fetches leaderboard data and mounts correctly', async () => {
    const mockData = [
      {
        id: 'user-1',
        name: 'Cat Master',
        username: 'catmaster',
        picture: 'https://example.com/cat.jpg',
        total_treats_received: 150,
      },
    ];

    vi.mocked(TreatsService.getLeaderboard).mockResolvedValue(mockData);

    const wrapper = shallowMount(LeaderboardView);

    await vi.dynamicImportSettled();
    expect(TreatsService.getLeaderboard).toHaveBeenCalledWith('all_time');
    expect(wrapper.exists()).toBe(true);
  });
});
