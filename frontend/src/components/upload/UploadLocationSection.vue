<template>
  <div class="space-y-6">
    <div class="flex items-baseline justify-between border-b border-stone-200 pb-4">
      <h2 class="text-2xl font-heading font-bold text-brown flex items-center">
        {{ t('upload.locationSection.title') }}
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
      <div class="flex items-center gap-2">
        <button
          type="button"
          :disabled="gettingLocation"
          class="text-xs font-bold uppercase tracking-wider text-terracotta hover:text-terracotta-dark transition-colors disabled:opacity-50 cursor-pointer"
          @click="$emit('get-location')"
        >
          {{
            gettingLocation
              ? t('upload.locationSection.locating')
              : t('upload.locationSection.useMyLocation')
          }}
        </button>
      </div>
    </div>

    <div
      class="relative rounded-2xl overflow-hidden border-2 border-white shadow-sm h-[300px] bg-stone-100 group"
    >
      <div :id="mapId" class="w-full h-full opacity-90 transition-opacity duration-300"></div>

      <!-- Login Overlay for Map -->
      <div
        v-if="!isAuthenticated"
        class="absolute inset-0 z-10 cursor-pointer bg-transparent"
        :title="t('upload.locationSection.loginToUseMap')"
        @click="$emit('check-auth')"
      ></div>

      <!-- Map Instruction Overlay -->
      <div
        class="absolute bottom-4 left-4 right-4 bg-white/80 backdrop-blur-sm p-3 rounded-lg text-xs text-brown text-center pointer-events-none border border-white/50 shadow-sm transition-all duration-300"
      >
        <span
          v-if="!hasSelectedLocation"
          class="flex items-center justify-center gap-2 animate-pulse"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          {{ t('upload.locationSection.tapToPin') }}
        </span>
        <span v-else> {{ t('upload.locationSection.dragMarker') }} </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

withDefaults(
  defineProps<{
    mapId?: string;
    isAuthenticated: boolean;
    gettingLocation: boolean;
    hasSelectedLocation: boolean;
  }>(),
  {
    mapId: 'uploadMap',
  }
);

defineEmits<{
  'get-location': [];
  'check-auth': [];
}>();
</script>
