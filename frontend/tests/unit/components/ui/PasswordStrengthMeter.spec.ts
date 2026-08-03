import { nextTick } from 'vue';
import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string): string => {
      const labels: Record<string, string> = {
        'passwordStrength.weak': 'Weak',
        'passwordStrength.good': 'Good',
        'passwordStrength.strong': 'Strong',
      };
      return labels[key] ?? key;
    },
  }),
}));

describe('PasswordStrengthMeter.vue', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const mountMeter = (password: string) =>
    mount(PasswordStrengthMeter, {
      props: { password },
      global: {
        stubs: { transition: false },
      },
    });

  it('colors active bars for weak passwords and leaves remaining bars neutral', async () => {
    const wrapper = mountMeter('a');

    await vi.advanceTimersByTimeAsync(500);
    await nextTick();

    const bars = wrapper.findAll('.flex-1');
    expect(bars).toHaveLength(4);
    expect(bars[0].classes()).toContain('bg-[#f6c1b1]');
    expect(bars[1].classes()).toContain('bg-black/10');
    expect(wrapper.text()).toContain('Weak');
  });

  it('colors all bars for strong passwords', async () => {
    const wrapper = mountMeter('Password1!');

    await vi.advanceTimersByTimeAsync(500);
    await nextTick();

    expect(wrapper.findAll('.flex-1')).toHaveLength(4);
    for (const bar of wrapper.findAll('.flex-1')) {
      expect(bar.classes()).toContain('bg-[#7fb7a4]');
    }
    expect(wrapper.text()).toContain('Strong');
  });
});
