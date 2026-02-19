<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

interface PhotoData {
  location_name: string;
  description: string;
}

const props = defineProps<{
  isOpen: boolean;
  initialLocationName?: string;
  initialDescription?: string;
  isSaving: boolean;
}>();

defineEmits<{
  close: [];
  save: [data: PhotoData];
}>();

const { t } = useI18n();

const form = ref<PhotoData>({
  location_name: '',
  description: '',
});

watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      form.value = {
        location_name: props.initialLocationName || '',
        description: props.initialDescription || '',
      };
    }
  }
);
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4"
  >
    <div
      class="bg-white rounded-xl md:rounded-2xl shadow-xl p-4 sm:p-6 md:p-8 w-full max-w-md relative"
    >
      <h3 class="text-xl sm:text-2xl font-heading font-bold text-brown mb-4 sm:mb-6">
        {{ t('profile.editPhotoDetails') }}
      </h3>
      <form @submit.prevent="$emit('save', form)">
        <div class="mb-3 sm:mb-4">
          <label
            for="edit-location-name"
            class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-wide"
          >{{ t('map.locationName') }}</label>
          <input
            id="edit-location-name"
            v-model="form.location_name"
            type="text"
            class="w-full px-3 sm:px-4 py-2 border border-stone-200 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-terracotta/20 focus:border-terracotta outline-none transition-all text-sm sm:text-base"
            required
            maxlength="50"
          />
        </div>
        <div class="mb-4 sm:mb-6">
          <label
            for="edit-description"
            class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-wide"
          >{{ t('map.description') }}</label>
          <textarea
            id="edit-description"
            v-model="form.description"
            rows="4"
            class="w-full px-3 sm:px-4 py-2 border border-stone-200 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-terracotta/20 focus:border-terracotta outline-none transition-all resize-none text-sm sm:text-base"
            maxlength="500"
          ></textarea>
        </div>
        <div class="flex justify-end gap-2 sm:gap-3">
          <button
            type="button"
            class="px-3 sm:px-4 py-2 text-stone-500 hover:text-brown font-medium transition-colors cursor-pointer text-sm sm:text-base"
            @click="$emit('close')"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="submit"
            :disabled="isSaving"
            class="px-4 sm:px-6 py-2 bg-terracotta hover:bg-terracotta-dark text-white rounded-lg sm:rounded-xl shadow-md font-bold transition-all disabled:opacity-50 cursor-pointer text-sm sm:text-base"
          >
            {{ isSaving ? t('common.saving') : t('common.saveChanges') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
