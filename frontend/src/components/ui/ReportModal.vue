<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="relative z-[1000]"
        aria-labelledby="modal-title"
        role="dialog"
        aria-modal="true"
      >
        <!-- Backdrop -->
        <div
          class="fixed inset-0 bg-stone-900/75 backdrop-blur-sm transition-opacity"
          aria-hidden="true"
          @click="close"
        ></div>

        <!-- Modal Panel Container -->
        <div class="fixed inset-0 z-10 w-screen overflow-y-auto">
          <div
            class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0"
          >
            <Transition
              enter-active-class="transition ease-out duration-300"
              enter-from-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enter-to-class="opacity-100 translate-y-0 sm:scale-100"
              leave-active-class="transition ease-in duration-200"
              leave-from-class="opacity-100 translate-y-0 sm:scale-100"
              leave-to-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <div
                v-if="isOpen"
                class="relative transform overflow-hidden rounded-2xl bg-white text-left shadow-2xl transition-all sm:my-8 sm:w-full sm:max-w-lg border border-stone-100"
                @click.stop
              >
                <!-- Close Button -->
                <button
                  class="absolute top-4 right-4 text-stone-400 hover:text-brown transition-colors focus:outline-none"
                  @click="close"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>

                <!-- Header -->
                <div
                  class="bg-stone-50 px-4 py-5 sm:px-6 border-b border-stone-100 flex items-center"
                >
                  <div
                    class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10"
                  >
                    <svg
                      class="h-6 w-6 text-red-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="1.5"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                      />
                    </svg>
                  </div>
                  <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                    <h3
                      id="modal-title"
                      class="text-xl font-bold leading-6 text-brown-dark font-heading"
                    >
                      {{ t('report.title') }}
                    </h3>
                    <p class="text-sm text-stone-500 mt-1">{{ t('report.subtitle') }}</p>
                  </div>
                </div>

                <!-- Body -->
                <div class="px-4 py-5 sm:p-6 bg-white space-y-5">
                  <div>
                    <label for="reason" class="block text-sm font-bold leading-6 text-brown">
                      {{ t('report.reasonLabel') }}
                    </label>
                    <div class="mt-2">
                      <select
                        id="reason"
                        v-model="form.reason"
                        name="reason"
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
                <div
                  class="bg-stone-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6 border-t border-stone-100"
                >
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
                      <circle
                        class="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        stroke-width="4"
                      />
                      <path
                        class="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    {{ isSubmitting ? t('report.submitting') : t('report.submit') }}
                  </button>
                  <button
                    type="button"
                    class="mt-3 inline-flex w-full justify-center rounded-lg bg-white px-3 py-2.5 text-sm font-semibold text-stone-900 shadow-sm ring-1 ring-inset ring-stone-300 hover:bg-stone-50 sm:mt-0 sm:w-auto transition-colors"
                    @click="close"
                  >
                    {{ t('report.cancel') }}
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { apiV1 } from '@/utils/api';
import { REPORT_REASONS } from '@/constants/moderation';
import { useToast } from '@/components/toast/use-toast';
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

const close = () => {
  if (isSubmitting.value) return;
  emit('close');
};

const submitReport = async () => {
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
