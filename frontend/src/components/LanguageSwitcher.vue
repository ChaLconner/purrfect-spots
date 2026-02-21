<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { computed } from 'vue';

const { locale } = useI18n();

const toggleLanguage = () => {
  const newLocale = locale.value === 'en' ? 'th' : 'en';
  locale.value = newLocale;
  localStorage.setItem('user-locale', newLocale);
};

const currentLabel = computed(() => {
  return locale.value === 'en' ? 'EN' : 'TH';
});
</script>

<template>
  <button
    class="group relative flex items-center gap-2 px-3 py-1.5 bg-[var(--color-btn-shade-e)] border-2 border-[var(--color-btn-shade-a)] rounded-2xl cursor-pointer min-h-[2.5rem] transition-all duration-[150ms] ease-out hover:bg-[var(--color-btn-shade-d)] hover:translate-y-[0.1rem] active:translate-y-[0.25rem]"
    style="transform-style: preserve-3d; will-change: transform"
    :aria-label="$t('common.switchLanguage')"
    @click="toggleLanguage"
  >
    <span
      class="absolute inset-0 bg-[var(--color-btn-shade-c)] rounded-[inherit] -z-10 transition-all duration-[150ms] ease-out shadow-[0_0_0_2px_var(--color-btn-shade-b),0_0.2rem_0_0_var(--color-btn-shade-a)] group-hover:translate-y-[0.2rem] group-active:translate-y-0 group-active:translate-z-[-1em] group-active:shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.1em_0_0_var(--color-btn-shade-b)]"
      style="transform: translate3d(0, 0.2rem, -1em); will-change: transform"
    ></span>
    <span class="font-accent font-bold text-[0.85rem] text-[var(--color-btn-shade-a)]">{{
      currentLabel
    }}</span>
  </button>
</template>
