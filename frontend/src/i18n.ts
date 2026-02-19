import { createI18n } from 'vue-i18n';
import en from './locales/en.json';
import th from './locales/th.json';

// Get saved language from localStorage or default to 'en'
const savedLocale = localStorage.getItem('user-locale') || 'en';

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: savedLocale, // set locale
  fallbackLocale: 'en', // set fallback locale
  messages: {
    en,
    th,
  },
});

export default i18n;
