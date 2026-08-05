import { nextTick } from 'vue';
import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';

const { useI18nMock } = vi.hoisted(() => {
  const labels: Record<string, string> = {
    'passwordStrength.weak': 'Weak',
    'passwordStrength.good': 'Good',
    'passwordStrength.strong': 'Strong',
  };

  return {
    useI18nMock: vi.fn((options?: { useScope?: string }) => ({
      t: (key: string): string => (options?.useScope === 'global' ? labels[key] ?? key : key),
    })),
  };
});

vi.mock('vue-i18n', () => ({
  useI18n: useI18nMock,
}));

import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';

describe('PasswordStrengthMeter global translations', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders password strength labels from the global locale scope', async () => {
    vi.useFakeTimers();
    const wrapper = mount(PasswordStrengthMeter, {
      props: { password: '123' },
      global: { stubs: { transition: false } },
    });

    await vi.advanceTimersByTimeAsync(500);
    await nextTick();

    expect(wrapper.get('p').text()).toBe('Weak');
    expect(useI18nMock).toHaveBeenCalledWith({ useScope: 'global' });
  });
});
