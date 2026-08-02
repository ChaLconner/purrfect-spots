<template>
  <BaseModal
    :is-open="isOpen"
    max-width="lg"
    @close="close"
  >
    <!-- Modal Header -->
    <div class="px-6 pt-6 pb-4 border-b border-stone-100 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-red-50 rounded-xl text-red-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h3 id="modal-title" class="text-lg font-bold text-brown font-heading">
            {{ t('report.title') }}
          </h3>
          <p class="text-xs text-stone-500 font-body">
            {{ t('report.subtitle') }}
          </p>
        </div>
      </div>
    </div>

    <!-- Modal Body -->
    <div class="p-6 space-y-4 font-body">
      <div>
        <label for="reason" class="block text-sm font-bold leading-6 text-brown">
          {{ t('report.reasonLabel') }} <span class="text-red-500">*</span>
        </label>
        <div class="mt-2">
          <select
            id="reason"
            v-model="form.reason"
            class="block w-full rounded-lg border-0 py-2.5 px-3 text-brown shadow-sm ring-1 ring-inset ring-sand-300 focus:ring-2 focus:ring-inset focus:ring-terracotta sm:text-sm sm:leading-6 bg-stone-50"
          >
            <option value="" disabled>{{ t('report.reasonPlaceholder') }}</option>
            <option
              v-for="reason in REPORT_REASONS"
              :key="reason.value"
              :value="reason.value"
            >
              {{ t(`report.reasons.${reason.value}`) }}
            </option>
          </select>
        </div>
      </div>

      <div>
        <label for="details" class="block text-sm font-bold leading-6 text-brown">
          {{ t('report.detailsLabel') }}
        </label>
        <div class="mt-2">
          <textarea
            id="details"
            v-model="form.details"
            rows="4"
            class="block w-full rounded-lg border-0 py-2.5 px-3 text-brown shadow-sm ring-1 ring-inset ring-sand-300 placeholder:text-stone-400 focus:ring-2 focus:ring-inset focus:ring-terracotta sm:text-sm sm:leading-6 bg-stone-50 resize-none"
            :placeholder="t('report.detailsPlaceholder')"
          ></textarea>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="bg-stone-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6 border-t border-stone-100 -mx-6 -mb-6 mt-4">
      <button
        type="button"
        class="inline-flex w-full justify-center rounded-lg bg-red-600 px-3 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-red-500 sm:ml-3 sm:w-auto transition-all disabled:opacity-50 disabled:cursor-not-allowed items-center gap-2"
        :disabled="isSubmitting || !form.reason"
        @click="submitReport"
      >
        <svg
          v-if="isSubmitting"
          class="animate-spin h-4 w-4 text-white"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        {{ t('report.submit') }}
      </button>
      <button
        type="button"
        class="mt-3 inline-flex w-full justify-center rounded-lg bg-white px-3 py-2.5 text-sm font-semibold text-stone-900 shadow-sm ring-1 ring-inset ring-stone-300 hover:bg-stone-50 sm:mt-0 sm:w-auto transition-all"
        :disabled="isSubmitting"
        @click="close"
      >
        {{ t('common.cancel') }}
      </button>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import BaseModal from './BaseModal.vue';
import { ref, reactive, watch } from 'vue';
import { apiV1 } from '@/utils/api';
import { REPORT_REASONS } from '@/constants/moderation';
import { useToast } from '@/composables/useToast';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps<{
  isOpen: boolean;
  photoId: string;
}>();

const emit = defineEmits(['close', 'submitted']);
const { toast } = useToast();

const isSubmitting = ref(false);
const form = reactive({
  reason: '',
  details: '',
});

// Reset form when modal opens/closes
watch(
  () => props.isOpen,
  (newVal) => {
    if (!newVal) {
      // Delay reset slightly to wait for exit transition
      setTimeout(() => {
        form.reason = '';
        form.details = '';
      }, 300);
    }
  }
);

const close = (): void => {
  if (isSubmitting.value) return;
  emit('close');
};

const submitReport = async (): Promise<void> => {
  if (!form.reason) return;

  isSubmitting.value = true;
  try {
    await apiV1.post('/reports/', {
      photo_id: props.photoId,
      reason: form.reason,
      details: form.details,
    });

    toast({
      title: t('report.successTitle'),
      description: t('report.successMessage'),
      variant: 'default',
    });
    emit('submitted');
    emit('close'); // Close immediately on success
  } catch (error) {
    console.error('Failed to submit report', error);
    toast({
      title: t('report.errorTitle'),
      description: t('report.errorMessage'),
      variant: 'destructive',
    });
  } finally {
    isSubmitting.value = false;
  }
};
</script>
