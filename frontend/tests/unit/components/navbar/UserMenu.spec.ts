import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import UserMenu from '@/components/navbar/UserMenu.vue';

const authStoreMock = vi.hoisted(() => ({
  user: {
    name: 'Professor Codex',
    email: 'professor@example.com',
    picture: 'https://cdn.example.com/avatar.png',
    is_pro: false,
  },
  canAccessAdmin: false,
  clearAuth: vi.fn(),
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => authStoreMock,
}));

vi.mock('@/services/authService', () => ({
  AuthService: {
    logout: vi.fn(),
  },
}));

vi.mock('@/store/toast', () => ({
  showSuccess: vi.fn(),
}));

vi.mock('@/utils/env', () => ({
  isDev: () => false,
}));

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}));

describe('UserMenu', () => {
  beforeEach(() => {
    authStoreMock.user = {
      name: 'Professor Codex',
      email: 'professor@example.com',
      picture: 'https://cdn.example.com/avatar.png',
      is_pro: false,
    };
    authStoreMock.canAccessAdmin = false;
    vi.clearAllMocks();
  });

  it('shows local initials while the remote avatar is still loading', () => {
    const wrapper = mount(UserMenu, {
      global: {
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
        mocks: {
          $t: (key: string) => key,
        },
      },
    });

    const fallback = wrapper.get('[data-testid="user-avatar-fallback"]');
    const image = wrapper.get('[data-testid="user-avatar-image"]');

    expect(fallback.text()).toBe('PC');
    expect(image.classes()).toContain('opacity-0');
  });

  it('fades the remote avatar in after it loads', async () => {
    const wrapper = mount(UserMenu, {
      global: {
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
        mocks: {
          $t: (key: string) => key,
        },
      },
    });

    const image = wrapper.get('[data-testid="user-avatar-image"]');
    await image.trigger('load');

    expect(image.classes()).toContain('opacity-100');
  });

  it('keeps the local initials when the remote avatar fails', async () => {
    const wrapper = mount(UserMenu, {
      global: {
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
        mocks: {
          $t: (key: string) => key,
        },
      },
    });

    await wrapper.get('[data-testid="user-avatar-image"]').trigger('error');
    await nextTick();

    expect(wrapper.get('[data-testid="user-avatar-fallback"]').text()).toBe('PC');
    expect(wrapper.find('[data-testid="user-avatar-image"]').exists()).toBe(false);
  });
});
