<template>
  <div class="space-y-6">
    <div class="flex items-baseline justify-between border-b border-stone-200 pb-4">
      <h2 class="text-2xl font-heading font-bold text-brown flex items-center">
        {{ t('upload.detailsSection.title') }}
        <svg
          v-if="!isAuthenticated"
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5 ml-2 text-stone-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          title="Login required"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
          />
        </svg>
      </h2>
      <span class="text-sm font-medium text-stone-500 uppercase tracking-widest">{{
        t('upload.detailsSection.info')
      }}</span>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div class="space-y-2">
        <label
          for="place-name"
          class="block text-xs font-bold text-brown-light uppercase tracking-wider pl-1"
          >{{ t('upload.detailsSection.nameOfPlace') }}</label
        >
        <BaseInput
          id="place-name"
          :model-value="locationName"
          type="text"
          :placeholder="t('upload.detailsSection.namePlaceholder')"
          required
          class="bg-white/70 border-stone-200"
          @update:model-value="$emit('update:locationName', $event as string)"
          @focus="$emit('focus-auth', $event)"
        />
      </div>

      <div class="space-y-2">
        <label
          for="place-description"
          class="block text-xs font-bold text-brown-light uppercase tracking-wider pl-1"
          >{{ t('upload.detailsSection.description') }}</label
        >
        <textarea
          id="place-description"
          :value="description"
          rows="1"
          :placeholder="t('upload.detailsSection.descriptionPlaceholder')"
          class="w-full px-4 py-3 bg-white/70 border-2 border-stone-200 rounded-xl focus:outline-none focus:border-terracotta focus:ring-4 focus:ring-terracotta/10 transition-all font-medium text-brown placeholder-stone-500 min-h-[52px]"
          @input="$emit('update:description', ($event.target as HTMLTextAreaElement).value)"
          @focus="$emit('focus-auth', $event)"
        ></textarea>
      </div>

      <div class="space-y-2 md:col-span-2">
        <label
          for="tags-input"
          class="block text-xs font-bold text-brown-light uppercase tracking-wider pl-1"
          >{{ t('upload.detailsSection.tagsOptional') }}</label
        >
        <TagsInput
          id="tags-input"
          :model-value="tags"
          :placeholder="t('upload.detailsSection.tagsPlaceholder')"
          :max-tags="20"
          :max-tag-length="50"
          :disabled="!isAuthenticated"
          @update:model-value="$emit('update:tags', $event)"
          @focus="$emit('focus-auth', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TagsInput from '@/components/ui/TagsInput.vue';
import { BaseInput } from '@/components/ui';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

defineProps<{
  locationName: string;
  description: string;
  tags: string[];
  isAuthenticated: boolean;
}>();

defineEmits<{
  'update:locationName': [value: string];
  'update:description': [value: string];
  'update:tags': [value: string[]];
  'focus-auth': [event: Event];
}>();
</script>
