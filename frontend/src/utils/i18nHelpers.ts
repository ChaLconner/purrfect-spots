/**
 * i18n Helper Functions
 *
 * ฟังก์ชันช่วยเหลือสำหรับการจัดการ internationalization (i18n)
 * รองรับ pluralization, date formatting, number formatting และ interpolation
 */

import { useI18n } from 'vue-i18n';

/**
 * ประเภทข้อมูลสำหรับ pluralization rules
 */
export interface PluralRules {
  [key: string]: (count: number) => string;
}

/**
 * กฎ pluralization สำหรับภาษาต่างๆ
 */
export const pluralRules: PluralRules = {
  // English: 0 items, 1 item, 2 items, 3 items...
  en: (count: number) => {
    return count === 1 ? 'one' : 'other';
  },
  // Thai: ไม่มีการเปลี่ยนรูปแบบตามจำนวน
  th: (_count: number) => {
    return 'other';
  },
};

/**
 * ฟังก์ชันจัดรูปแบบตัวเลขตาม locale
 * @param value - ค่าตัวเลข
 * @param options - ตัวเลือกการจัดรูปแบบ
 * @returns สตริงตัวเลขที่จัดรูปแบบแล้ว
 */
export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  const { locale } = useI18n();
  return new Intl.NumberFormat(locale.value, options).format(value);
}

/**
 * ฟังก์ชันจัดรูปแบบวันที่ตาม locale
 * @param date - วันที่ (Date object หรือ string)
 * @param options - ตัวเลือกการจัดรูปแบบ
 * @returns สตริงวันที่ที่จัดรูปแบบแล้ว
 */
export function formatDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
  const { locale } = useI18n();
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(locale.value, options).format(dateObj);
}

/**
 * ฟังก์ชันจัดรูปแบบสกุลเงินตาม locale
 * @param value - ค่าเงิน
 * @param currency - รหัสสกุลเงิน (เช่น 'USD', 'THB')
 * @returns สตริงเงินที่จัดรูปแบบแล้ว
 */
export function formatCurrency(value: number, currency: string = 'USD'): string {
  const { locale } = useI18n();
  return new Intl.NumberFormat(locale.value, {
    style: 'currency',
    currency,
  }).format(value);
}

/**
 * ฟังก์ชันจัดรูปแบบเปอร์เซ็นต์ตาม locale
 * @param value - ค่าเปอร์เซ็นต์ (0-100)
 * @returns สตริงเปอร์เซ็นต์ที่จัดรูปแบบแล้ว
 */
export function formatPercent(value: number): string {
  const { locale } = useI18n();
  return new Intl.NumberFormat(locale.value, {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value / 100);
}

/**
 * ฟังก์ชันจัดรูปแบบระยะเวลา (relative time)
 * @param date - วันที่เป้าหมาย
 * @returns สตริงระยะเวลาที่จัดรูปแบบแล้ว (เช่น "2 minutes ago")
 */
export function formatRelativeTime(date: Date | string): string {
  const { locale } = useI18n();
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);

  const rtf = new Intl.RelativeTimeFormat(locale.value, { numeric: 'auto' });

  const intervals = [
    { unit: 'year' as const, seconds: 31536000 },
    { unit: 'month' as const, seconds: 2592000 },
    { unit: 'day' as const, seconds: 86400 },
    { unit: 'hour' as const, seconds: 3600 },
    { unit: 'minute' as const, seconds: 60 },
  ];

  for (const interval of intervals) {
    const count = Math.floor(diffInSeconds / interval.seconds);
    if (count >= 1) {
      return rtf.format(-count, interval.unit);
    }
  }

  return rtf.format(-diffInSeconds, 'second');
}

/**
 * ฟังก์ชันแปลงข้อความด้วย pluralization
 * @param key - คีย์ translation
 * @param count - จำนวนสำหรับการเลือกรูปแบบ
 * @param params - พารามิเตอร์เพิ่มเติมสำหรับ interpolation
 * @returns ข้อความที่แปลแล้ว
 */
export function tPlural(key: string, count: number, params?: Record<string, unknown>): string {
  const { t, locale } = useI18n();
  const rule = pluralRules[locale.value] || pluralRules.en;
  const pluralForm = rule(count);

  return t(`${key}.${pluralForm}`, { count, ...params });
}

/**
 * ฟังก์ชันแปลงข้อความด้วย interpolation ที่ปลอดภัย
 * @param key - คีย์ translation
 * @param params - พารามิเตอร์สำหรับ interpolation
 * @returns ข้อความที่แปลแล้ว
 */
export function tSafe(key: string, params?: Record<string, unknown>): string {
  const { t } = useI18n();

  // Sanitize params to prevent XSS
  const sanitizedParams = params
    ? Object.fromEntries(
        Object.entries(params).map(([k, v]) => [
          k,
          typeof v === 'string' ? v.replace(/</g, '<').replace(/>/g, '>') : v,
        ])
      )
    : undefined;

  return t(key, sanitizedParams);
}

/**
 * ฟังก์ชันตรวจสอบว่ามี translation key หรือไม่
 * @param key - คีย์ translation
 * @returns true ถ้ามี key, false ถ้าไม่มี
 */
export function hasTranslation(key: string): boolean {
  const { te } = useI18n();
  return te(key);
}

/**
 * ฟังก์ชันรับ translation key ที่มีอยู่ หรือค่าเริ่มต้น
 * @param key - คีย์ translation
 * @param fallback - ค่าเริ่มต้นถ้าไม่พบ key
 * @returns ข้อความที่แปลแล้ว หรือค่าเริ่มต้น
 */
export function tOrFallback(key: string, fallback: string): string {
  const { t } = useI18n();
  if (hasTranslation(key)) {
    return t(key);
  }
  return fallback;
}

/**
 * ฟังก์ชันสำหรับการจัดรูปแบบรายการ (list formatting)
 * @param items - รายการข้อความ
 * @returns สตริงที่จัดรูปแบบแล้ว (เช่น "A, B, and C")
 */
export function formatList(items: string[]): string {
  const { locale } = useI18n();
  return new Intl.ListFormat(locale.value, {
    style: 'long',
    type: 'conjunction',
  }).format(items);
}

/**
 * ฟังก์ชันแปลงข้อความ error ที่มี interpolation
 * @param errorKey - คีย์ error
 * @param params - พารามิเตอร์สำหรับ interpolation
 * @returns ข้อความ error ที่แปลแล้ว
 */
export function tError(errorKey: string, params?: Record<string, unknown>): string {
  return tSafe(`errors.${errorKey}`, params);
}

/**
 * ฟังก์ชันสำหรับการจัดรูปแบบขนาดไฟล์
 * @param bytes - ขนาดไฟล์ใน bytes
 * @returns สตริงขนาดไฟล์ที่จัดรูปแบบแล้ว (เช่น "1.5 MB")
 */
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];

  if (bytes === 0) return '0 B';

  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const size = bytes / Math.pow(k, i);

  return `${formatNumber(size, { maximumFractionDigits: 1 })} ${units[i]}`;
}

/**
 * ฟังก์ชันสำหรับการจัดรูปแบบเวลา
 * @param seconds - เวลาในวินาที
 * @returns สตริงเวลาที่จัดรูปแบบแล้ว (เช่น "1:30:45")
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  const parts: string[] = [];

  if (hours > 0) {
    parts.push(hours.toString().padStart(2, '0'));
  }
  parts.push(minutes.toString().padStart(2, '0'));
  parts.push(secs.toString().padStart(2, '0'));

  return parts.join(':');
}

/**
 * ฟังก์ชันสำหรับการจัดรูปแบบเวลาสั้นๆ
 * @param seconds - เวลาในวินาที
 * @returns สตริงเวลาที่จัดรูปแบบแล้ว (เช่น "2m 30s")
 */
export function formatShortDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  const parts: string[] = [];

  if (hours > 0) {
    parts.push(tPlural('time.hour', hours) || `${hours}h`);
  }
  if (minutes > 0) {
    parts.push(tPlural('time.minute', minutes) || `${minutes}m`);
  }
  if (secs > 0 || parts.length === 0) {
    parts.push(tPlural('time.second', secs) || `${secs}s`);
  }

  return parts.join(' ');
}

/**
 * Composable สำหรับใช้ฟังก์ชัน i18n ใน Vue components
 */
export function useI18nHelpers() {
  return {
    formatNumber,
    formatDate,
    formatCurrency,
    formatPercent,
    formatRelativeTime,
    tPlural,
    tSafe,
    hasTranslation,
    tOrFallback,
    tError,
    formatList,
    formatFileSize,
    formatDuration,
    formatShortDuration,
  };
}
