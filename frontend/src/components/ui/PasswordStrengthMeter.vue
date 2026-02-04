<template>
  <transition name="slide-fade">
    <div v-if="isVisible" class="password-strength-meter">
      <div class="strength-bars">
        <div
          v-for="i in 4"
          :key="i"
          class="bar"
          :class="{
            filled: strength >= i,
            weak: strength <= 2 && strength >= i,
            medium: strength === 3 && strength >= i,
            strong: strength === 4 && strength >= i,
          }"
        ></div>
      </div>
      <p class="strength-label" :class="labelColorClass">
        {{ strengthLabel }}
      </p>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  password: string;
}>();

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
      return 'Weak';
    case 3:
      return 'Good';
    case 4:
      return 'Strong';
    default:
      return 'Weak';
  }
});

const labelColorClass = computed(() => {
  switch (strength.value) {
    case 1:
    case 2:
      return 'text-terracotta';
    case 3:
      return 'text-yellow-600';
    case 4:
      return 'text-sage-dark';
    default:
      return 'text-gray-400';
  }
});
</script>

<style scoped>
.password-strength-meter {
  margin-top: 0.5rem;
  width: 100%;
}

.strength-bars {
  display: flex;
  gap: 4px;
  height: 4px;
  margin-bottom: 4px;
}

.bar {
  flex: 1;
  border-radius: 2px;
  background-color: rgba(0, 0, 0, 0.1); /* Base empty color */
  transition: all 0.3s ease;
}

.bar.filled.weak {
  background-color: #f6c1b1; /* Terracotta Light */
}

.bar.filled.medium {
  background-color: #ebc968; /* Golden/Yellowish */
}

.bar.filled.strong {
  background-color: #7fb7a4; /* Sage */
}

.strength-label {
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  font-weight: 500;
  text-align: right;
  transition: color 0.3s ease;
}

.text-terracotta {
  color: #c97b49;
}
.text-sage-dark {
  color: #5a7558;
}
.text-yellow-600 {
  color: #d9a030;
}
.text-gray-400 {
  color: #9ca3af;
}

/* Transition Styles */
.slide-fade-enter-active {
  transition: all 0.5s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-5px);
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  opacity: 1;
  max-height: 50px; /* Approximate height */
  margin-top: 0.5rem;
}
</style>
