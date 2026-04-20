import { createI18n } from 'vue-i18n';
import en from './locales/en.json';

const SUPPORTED_LOCALES = ['en', 'th'] as const;
type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];
const DEFAULT_LOCALE: SupportedLocale = 'en';

function isSupportedLocale(locale: string | null): locale is SupportedLocale {
  return locale !== null && SUPPORTED_LOCALES.includes(locale as SupportedLocale);
}

function getSavedLocale(): SupportedLocale {
  if (typeof window === 'undefined') {
    return DEFAULT_LOCALE;
  }

  const savedLocale = localStorage.getItem('user-locale');
  return isSupportedLocale(savedLocale) ? savedLocale : DEFAULT_LOCALE;
}

const localeLoaders: Partial<Record<SupportedLocale, () => Promise<{ default: typeof en }>>> = {
  th: () => import('./locales/th.json'),
};
const loadedLocales = new Set<SupportedLocale>(['en']);

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: DEFAULT_LOCALE, // set locale after lazy-loading if needed
  fallbackLocale: DEFAULT_LOCALE, // set fallback locale
  messages: {
    en,
  },
});

export async function ensureLocaleMessages(locale: SupportedLocale): Promise<void> {
  if (loadedLocales.has(locale)) {
    return;
  }

  const loadLocale = localeLoaders[locale];
  if (!loadLocale) {
    return;
  }

  const messages = await loadLocale();
  i18n.global.setLocaleMessage(locale, messages.default);
  loadedLocales.add(locale);
}

export async function setLocale(locale: SupportedLocale): Promise<void> {
  await ensureLocaleMessages(locale);
  i18n.global.locale.value = locale;

  if (typeof window !== 'undefined') {
    localStorage.setItem('user-locale', locale);
  }
}

export async function initializeI18n(): Promise<void> {
  await setLocale(getSavedLocale());
}

export default i18n;
