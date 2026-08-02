<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import BaseConfirmModal from '@/components/ui/BaseConfirmModal.vue';

defineProps<{
  isOpen: boolean;
  isDeleting: boolean;
}>();

const { t } = useI18n();

defineEmits<{
  close: [];
  confirm: [];
}>();
</script>

<template>
  <BaseConfirmModal
    :is-open="isOpen"
    :is-loading="isDeleting"
    variant="danger"
    :title="t('profile.deleteMemoryTitle')"
    :message="t('profile.deleteMemoryMessage')"
    :confirm-text="isDeleting ? t('common.deleting') : t('common.yesDelete')"
    :cancel-text="t('common.keepIt')"
    @close="$emit('close')"
    @confirm="$emit('confirm')"
  />
</template>
