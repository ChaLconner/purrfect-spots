/**
 * Standardized date and time formatting utilities for the application.
 * Enforces DD/MM/YYYY format across all views.
 */

function resolveLocale(locale: string): string {
  return locale === 'th' ? 'th-TH' : 'en-US';
}

/**
 * Formats a date string into DD/MM/YYYY by default, or an Intl-based string
 * when explicit format options are provided.
 */
export const formatDate = (
  dateStr: string | null | undefined,
  options?: Intl.DateTimeFormatOptions,
  locale: string = 'en'
): string => {
  if (!dateStr) return 'N/A';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return 'N/A';

    if (options) {
      return new Intl.DateTimeFormat(resolveLocale(locale), options).format(date);
    }

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    return `${day}/${month}/${year}`;
  } catch {
    return 'N/A';
  }
};

/**
 * Formats a date string into DD/MM/YYYY hh:mm AM/PM.
 * @param dateStr - The date string to format.
 * @param locale - The current locale (e.g., from i18n).
 * @returns Formatted timestamp string or 'N/A' if invalid.
 */
export const formatTimestamp = (
  dateStr: string | null | undefined,
  locale: string = 'en'
): string => {
  if (!dateStr) return 'N/A';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return 'N/A';

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    const time = date.toLocaleTimeString(resolveLocale(locale), {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });

    return `${day}/${month}/${year} ${time}`;
  } catch {
    return 'N/A';
  }
};
