import { ref, watchEffect, onMounted, type Ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { sanitizeRichHtml } from '@/utils/security';
import { formatDate } from '@/utils/date';

export function useLegalPageContent(i18nKey: string): { contentRef: Ref<HTMLElement | null> } {
  const { t } = useI18n();
  const contentRef = ref<HTMLElement | null>(null);

  onMounted(() => {
    watchEffect(() => {
      if (contentRef.value) {
        contentRef.value.innerHTML = sanitizeRichHtml(
          t(i18nKey, {
            date: formatDate(new Date().toISOString()),
          })
        );
      }
    });
  });

  return { contentRef };
}
