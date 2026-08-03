<template>
  <div
    class="absolute top-6 left-6 z-[var(--z-map-controls)] w-[min(21rem,calc(100%-3rem))]"
    aria-live="polite"
  >
    <div
      class="overflow-hidden rounded-2xl border-2 border-[var(--color-btn-shade-a)] bg-white/95 shadow-[0_0.35rem_0_0_var(--color-btn-shade-a),0_0.8rem_1.5rem_rgba(66,33,16,0.16)] backdrop-blur-md"
    >
      <div class="flex items-start gap-3 p-3">
        <span
          class="mt-1.5 h-3 w-3 shrink-0 rounded-full border-2 border-white shadow-sm"
          :class="statusDotClass"
          aria-hidden="true"
        ></span>

        <div class="min-w-0 flex-1">
          <p class="font-heading text-sm font-bold leading-tight text-[var(--color-text-primary)]">
            {{ statusLabel }}
          </p>
          <p class="mt-1 font-accent text-xs leading-snug text-[var(--color-brown-meta)]">
            {{ detailText }}
          </p>
        </div>

        <button
          type="button"
          class="shrink-0 rounded-xl border-2 border-[var(--color-btn-accent-a)] bg-[var(--color-btn-accent-e)] px-2.5 py-2 font-heading text-xs font-bold text-[var(--color-btn-accent-a)] transition hover:bg-[var(--color-btn-accent-d)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-btn-accent-a)] focus-visible:ring-offset-2 disabled:cursor-wait disabled:opacity-60"
          :disabled="isLoading"
          :aria-label="actionLabel"
          @click="handleLocationAction"
        >
          {{ actionLabel }}
        </button>
      </div>

      <div
        v-if="manualSelectMode"
        class="border-t border-[var(--color-btn-accent-a)]/20 bg-[var(--color-btn-accent-e)]/70 px-3 py-2 font-accent text-xs font-bold text-[var(--color-btn-accent-a)]"
      >
        {{ $t('map.location.manualSelectHint') }}
      </div>

      <div class="border-t border-[var(--color-btn-shade-a)]/15 px-3 pb-3 pt-2">
        <div class="flex items-center justify-between gap-2">
          <span class="font-heading text-xs font-bold text-[var(--color-text-primary)]">
            {{ $t('map.location.radiusLabel') }}
          </span>
          <span class="font-accent text-[0.65rem] text-[var(--color-brown-meta)]">
            {{ radiusHelpText }}
          </span>
        </div>

        <div class="mt-2 grid grid-cols-4 gap-1.5" role="group" :aria-label="$t('map.location.radiusLabel')">
          <button
            type="button"
            class="rounded-lg border px-2 py-1.5 font-accent text-xs font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-btn-shade-a)] focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-45"
            :class="radius === null ? selectedRadiusClasses : unselectedRadiusClasses"
            :aria-pressed="radius === null"
            @click="selectRadius(null)"
          >
            {{ $t('map.location.allRadius') }}
          </button>
          <button
            v-for="option in radiusOptions"
            :key="option"
            type="button"
            class="rounded-lg border px-2 py-1.5 font-accent text-xs font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-btn-shade-a)] focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-45"
            :class="radius === option ? selectedRadiusClasses : unselectedRadiusClasses"
            :disabled="!canFilterRadius"
            :aria-pressed="radius === option"
            @click="selectRadius(option)"
          >
            {{ option }} km
          </button>
        </div>

        <button
          v-if="canChooseManualLocation"
          type="button"
          class="mt-2 w-full rounded-lg border border-dashed border-[var(--color-btn-shade-a)]/45 px-2 py-1.5 font-accent text-xs font-bold text-[var(--color-btn-shade-a)] transition hover:border-[var(--color-btn-shade-a)] hover:bg-[var(--color-btn-shade-e)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-btn-shade-a)] focus-visible:ring-offset-1"
          @click="emit('manual-select')"
        >
          {{ manualSelectLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type {
  GeolocationSource,
  GeolocationStatus,
} from '@/composables/useGeolocation';

const props = defineProps<{
  status: GeolocationStatus;
  source: GeolocationSource;
  accuracy: number | null;
  lowAccuracy: boolean;
  lastUpdatedAt: number | null;
  showRecenter: boolean;
  manualSelectMode: boolean;
  radius: number | null;
  canFilterRadius: boolean;
}>();

const emit = defineEmits<{
  (event: 'locate' | 'recenter' | 'manual-select'): void;
  (event: 'radius-change', value: number | null): void;
}>();

const { t } = useI18n();
const radiusOptions = [1, 5, 10];

const isLoading = computed(() => props.status === 'loading');

const statusDotClass = computed(() => {
  if (props.lowAccuracy && props.status === 'available') {
    return 'bg-amber-500';
  }

  switch (props.status) {
    case 'loading':
      return 'bg-[var(--color-btn-accent-b)] animate-pulse';
    case 'available':
      return 'bg-[#4285F4]';
    case 'stale':
      return 'bg-slate-400';
    case 'denied':
    case 'unavailable':
      return 'bg-[var(--color-btn-accent-a)]';
    default:
      return 'bg-[var(--color-btn-shade-b)]';
  }
});

const statusLabel = computed(() => {
  if (props.source === 'manual' && props.status === 'available') {
    return t('map.location.selected');
  }
  if (props.lowAccuracy && props.status === 'available') {
    return t('map.location.lowAccuracy');
  }

  switch (props.status) {
    case 'loading':
      return t('map.location.searching');
    case 'available':
      return t('map.location.available');
    case 'stale':
      return t('map.location.lastKnown');
    case 'denied':
      return t('map.location.denied');
    case 'unavailable':
      return t('map.location.unavailable');
    default:
      return t('map.location.notRequested');
  }
});

const formatAccuracy = (accuracy: number | null): string => {
  if (accuracy === null || !Number.isFinite(accuracy)) {
    return t('map.location.accuracyUnknown');
  }

  if (accuracy < 1000) {
    return t('map.location.accuracy', { distance: `${Math.round(accuracy)} m` });
  }

  return t('map.location.accuracy', { distance: `${(accuracy / 1000).toFixed(1)} km` });
};

const formattedLastUpdated = computed(() => {
  if (!props.lastUpdatedAt) return '';
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(props.lastUpdatedAt);
});

const detailText = computed(() => {
  if (props.source === 'manual' && props.status === 'available') {
    return t('map.location.selectedHint');
  }
  if (props.lowAccuracy && props.status === 'available') {
    return `${formatAccuracy(props.accuracy)} ${t('map.location.lowAccuracyHint')}`;
  }

  switch (props.status) {
    case 'loading':
      return t('map.location.searchingHint');
    case 'available':
      return formatAccuracy(props.accuracy);
    case 'stale':
      return formattedLastUpdated.value
        ? t('map.location.lastKnownAt', { time: formattedLastUpdated.value })
        : t('map.location.lastKnownHint');
    case 'denied':
      return t('map.location.deniedHint');
    case 'unavailable':
      return t('map.location.unavailableHint');
    default:
      return t('map.location.notRequestedHint');
  }
});

const actionLabel = computed(() => {
  if (props.status === 'loading') return t('map.location.searching');
  if (props.source === 'manual') return t('map.location.useCurrent');
  if (props.status === 'available') {
    return props.showRecenter ? t('map.location.recenter') : t('map.location.myLocation');
  }
  return props.status === 'idle'
    ? t('map.location.useCurrent')
    : t('map.location.retry');
});

const radiusHelpText = computed(() =>
  props.canFilterRadius
    ? t('map.location.radiusHelp')
    : t('map.location.radiusRequiresLive')
);

const canChooseManualLocation = computed(
  () => props.status !== 'available' || props.source === 'manual'
);
const manualSelectLabel = computed(() =>
  props.manualSelectMode ? t('map.location.cancelManualSelect') : t('map.location.selectOnMap')
);

const selectedRadiusClasses =
  'border-[var(--color-btn-shade-a)] bg-[var(--color-btn-shade-e)] text-[var(--color-btn-shade-a)]';
const unselectedRadiusClasses =
  'border-[var(--color-btn-shade-a)]/25 bg-white/70 text-[var(--color-brown-meta)] hover:border-[var(--color-btn-shade-a)] hover:text-[var(--color-btn-shade-a)]';

const handleLocationAction = (): void => {
  if (props.status === 'available' && props.source !== 'manual') {
    emit('recenter');
  } else {
    emit('locate');
  }
};

const selectRadius = (value: number | null): void => {
  if (value !== null && !props.canFilterRadius) return;
  emit('radius-change', value);
};
</script>
