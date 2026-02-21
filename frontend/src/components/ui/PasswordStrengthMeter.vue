<template>
  <transition
    enter-active-class="transition-all duration-500 ease-out overflow-hidden"
    leave-active-class="transition-all duration-300 ease-[cubic-bezier(1,0.5,0.8,1)] overflow-hidden"
    enter-from-class="opacity-0 -translate-y-1 max-h-0 !mt-0"
    enter-to-class="opacity-100 max-h-[50px] mt-2 translate-y-0"
    leave-from-class="opacity-100 max-h-[50px] mt-2 translate-y-0"
    leave-to-class="opacity-0 -translate-y-1 max-h-0 !mt-0"
  >
    <div v-if="isVisible" class="mt-2 w-full">
      <div class="flex gap-1 h-1 mb-1">
        <div
          v-for="i in 4"
          :key="i"
          class="flex-1 rounded-sm bg-black/10 transition-colors duration-300 ease-in-out"
          :class="{
            'bg-[#f6c1b1]': strength <= 2 && strength >= i,
            'bg-[#ebc968]': strength === 3 && strength >= i,
            'bg-[#7fb7a4]': strength === 4 && strength >= i,
          }"
        ></div>
      </div>
      <p
        class="font-sans text-xs font-medium text-right transition-colors duration-300 ease-in-out"
        :class="labelColorClass"
      >
        {{ strengthLabel }}
      </p>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps<{
  password: string;
}>();

const { t } = useI18n();

const debouncedPassword = ref('');
const isTyping = ref(false);
let timeout: ReturnType<typeof setTimeout> | null = null;

watch(
  () => props.password,
  (newVal) => {
    isTyping.value = true;
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => {
      debouncedPassword.value = newVal;
      isTyping.value = false;
    }, 500); // 500ms debounce
  },
  { immediate: true }
);

const isVisible = computed(() => {
  return debouncedPassword.value.length > 0;
});

const strength = computed(() => {
  const pwd = debouncedPassword.value;
  if (!pwd) return 0;

  let score = 0;

  // Criteria 1: Length >= 8
  if (pwd.length >= 8) score++;

  // Criteria 2: Contains number
  if (/\d/.test(pwd)) score++;

  // Criteria 3: Contains special char
  if (/[^A-Za-z0-9]/.test(pwd)) score++;

  // Criteria 4: Mixed case
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++;

  // Adjustment for very short passwords even if complex
  if (pwd.length < 6) return 1;

  return score || 1; // Minimum 1 if not empty
});

const strengthLabel = computed(() => {
  // While typing (debounce wait), we show the *previous* calculated state (which is in debouncedPassword)
  // We prefer this over flashing "Analyzing..." or hiding/showing repeatedly
  switch (strength.value) {
    case 1:
    case 2:
      return t('passwordStrength.weak');
    case 3:
      return t('passwordStrength.good');
    case 4:
      return t('passwordStrength.strong');
    default:
      return t('passwordStrength.weak');
  }
});

const labelColorClass = computed(() => {
  switch (strength.value) {
    case 1:
    case 2:
      return 'text-[#c97b49]';
    case 3:
      return 'text-[#d9a030]';
    case 4:
      return 'text-[#5a7558]';
    default:
      return 'text-gray-400';
  }
});
</script>
