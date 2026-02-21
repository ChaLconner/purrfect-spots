<template>
  <div class="min-h-screen bg-sand-50 py-12 px-4 sm:px-6 lg:px-8">
    <div
      class="max-w-4xl mx-auto bg-white rounded-2xl shadow-sm border border-sand-100 p-8 sm:p-12"
    >
      <h1 class="text-3xl font-bold text-brown-900 font-display mb-8">
        {{ $t('privacyPolicy.title') }}
      </h1>

      <div ref="contentRef" class="prose prose-brown max-w-none text-brown-700"></div>

      <div class="mt-8 pt-8 border-t border-sand-200">
        <router-link to="/" class="text-terracotta-600 hover:text-terracotta-700 font-medium">
          {{ $t('privacyPolicy.backHome') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const contentRef = ref<HTMLElement | null>(null);

onMounted(() => {
  watchEffect(() => {
    if (contentRef.value) {
      contentRef.value.innerHTML = t('privacyPolicy.content', {
        date: new Date().toLocaleDateString(),
      });
    }
  });
});
</script>
