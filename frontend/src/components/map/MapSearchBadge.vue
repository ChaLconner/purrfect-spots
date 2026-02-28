<template>
  <transition
    enter-active-class="transition-all duration-300 ease-out"
    leave-active-class="transition-all duration-200 ease-in"
    enter-from-class="opacity-0 -translate-y-4"
    leave-to-class="opacity-0 -translate-y-4"
  >
    <div
      v-if="show"
      class="absolute top-20 lg:top-6 left-1/2 transform -translate-x-1/2 z-10 w-[95%] sm:w-auto max-w-sm sm:max-w-md pointer-events-none"
    >
      <div
        class="relative flex items-center justify-between gap-2 sm:gap-3 py-2 sm:py-2.5 pl-4 sm:pl-5 pr-2 sm:pr-2.5 bg-btn-shade-e border-2 border-btn-shade-a rounded-full shadow-[0_0_0_2px_var(--color-btn-shade-b),_0_0.3em_0_0_var(--color-btn-shade-a)] pointer-events-auto"
        style="animation: float-gentle 4s ease-in-out infinite"
      >
        <i18n-t
          keypath="map.foundCats"
          tag="span"
          class="font-accent text-sm font-medium text-btn-shade-a truncate flex-1 min-w-0 flex items-center gap-1.5 flex-wrap"
        >
          <template #count>
            <strong class="text-btn-accent-a font-bold text-sm sm:text-base">{{ count }}</strong>
          </template>
          <template #query>
            <span
              class="italic text-btn-brown-b truncate inline-block align-bottom max-w-[120px] sm:max-w-[180px]"
              :title="query"
              >{{ query }}</span
            >
          </template>
        </i18n-t>
        <button
          class="group relative w-8 h-8 sm:w-7 sm:h-7 shrink-0 flex items-center justify-center bg-btn-accent-e border-2 border-btn-accent-a rounded-full text-btn-accent-a cursor-pointer outline-none transition-transform duration-[175ms] ease-[cubic-bezier(0,0,1,1)] hover:bg-btn-accent-d hover:translate-y-[0.1em] active:translate-y-[0.2em]"
          style="transform-style: preserve-3d"
          :aria-label="$t('map.clearSearch')"
          @click="$emit('clear')"
        >
          <span
            class="absolute inset-0 bg-btn-accent-c rounded-[inherit] shadow-[0_0_0_2px_var(--color-btn-accent-b),_0_0.2em_0_0_var(--color-btn-accent-a)] transition-all duration-[175ms] ease-[cubic-bezier(0,0,1,1)] group-active:translate-y-0 group-active:shadow-[0_0_0_2px_var(--color-btn-accent-b),_0_0.05em_0_0_var(--color-btn-accent-b)]"
            style="transform: translate3d(0, 0.2em, -1em)"
          ></span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="relative z-10 w-4 h-4 sm:w-3.5 sm:h-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean;
  count: number;
  query: string;
}>();

defineEmits<{
  (e: 'clear'): void;
}>();
</script>
