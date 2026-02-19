<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { computed } from 'vue';

const { locale } = useI18n();

const toggleLanguage = () => {
  const newLocale = locale.value === 'en' ? 'th' : 'en';
  locale.value = newLocale;
  localStorage.setItem('user-locale', newLocale);
};

const currentFlag = computed(() => {
  return locale.value === 'en' ? '🇺🇸' : '🇹🇭';
});

const currentLabel = computed(() => {
  return locale.value === 'en' ? 'EN' : 'TH';
});
</script>

<template>
  <button class="language-btn" :aria-label="$t('common.switchLanguage')" @click="toggleLanguage">
    <span class="language-label">{{ currentLabel }}</span>
  </button>
</template>

<style scoped>
/* 3D Language Button */
.language-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  background: var(--color-btn-shade-e);
  border: 2px solid var(--color-btn-shade-a);
  border-radius: 1em;
  cursor: pointer;
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
  transform-style: preserve-3d;
  min-height: 2.5rem;
}

.language-btn::before {
  position: absolute;
  content: '';
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: var(--color-btn-shade-c);
  border-radius: inherit;
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.3em 0 0 var(--color-btn-shade-a);
  transform: translate3d(0, 0.3em, -1em);
  transition: all 175ms cubic-bezier(0, 0, 1, 1);
  z-index: -1;
}

.language-btn:hover {
  background: var(--color-btn-shade-d);
  transform: translate(0, 0.15em);
}

.language-btn:hover::before {
  transform: translate3d(0, 0.3em, -1em);
}

.language-btn:active {
  transform: translate(0, 0.3em);
}

.language-btn:active::before {
  transform: translate3d(0, 0, -1em);
  box-shadow:
    0 0 0 2px var(--color-btn-shade-b),
    0 0.1em 0 0 var(--color-btn-shade-b);
}

.language-label {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--color-btn-shade-a);
}
</style>
