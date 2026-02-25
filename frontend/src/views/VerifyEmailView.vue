<template>
  <div
    class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-[#eaf6f3]"
  >
    <!-- Animated Background -->
    <GhibliBackground />

    <!-- Main Card -->
    <div
      class="bg-white/85 backdrop-blur-[20px] rounded-[2rem] p-12 max-w-[450px] w-full shadow-[0_25px_50px_-12px_rgba(0,0,0,0.1),_0_0_0_1px_rgba(255,255,255,0.4)_inset] relative z-10 max-sm:p-8"
    >
      <!-- Header (No Icon) -->
      <div class="text-center mb-8">
        <h1 class="font-['Nunito'] text-[1.8rem] font-extrabold text-[#5a4632] mb-3">
          {{ t('auth.verifyEmail.title') }}
        </h1>
        <p class="font-sans text-[0.95rem] text-[#5a4632] leading-relaxed">
          {{ t('auth.verifyEmail.subtitle') }}<br />
          <strong class="text-[#2c3e50] break-all">{{ email }}</strong>
        </p>
      </div>

      <!-- OTP Input Section -->
      <div class="mb-6">
        <div class="flex gap-3 justify-center mb-4 w-full max-sm:gap-1">
          <input
            v-for="(_, index) in 6"
            :key="index"
            :ref="(el) => setInputRef(el, index)"
            v-model="otpDigits[index]"
            type="text"
            inputmode="numeric"
            maxlength="1"
            class="w-[50px] h-[60px] text-center font-mono text-2xl font-bold text-[#5a4632] bg-white/90 border-2 border-[rgba(127,183,164,0.3)] rounded-2xl outline-none transition-all duration-300 shrink-0 focus:border-[#7fb7a4] focus:shadow-[0_0_0_4px_rgba(127,183,164,0.15)] focus:scale-105 max-sm:flex-1 max-sm:w-auto max-sm:min-w-[36px] max-sm:h-[50px] max-sm:text-xl max-sm:p-0"
            :class="[
              otpDigits[index] ? 'bg-white border-[#7fb7a4]' : '',
              hasError ? 'border-[#e74c3c] animate-[shake_0.4s_ease-in-out]' : '',
            ]"
            @input="handleInput(index, $event)"
            @keydown="handleKeydown(index, $event)"
            @paste="handlePaste"
            @focus="hasError = false"
          />
        </div>

        <!-- Error Message -->
        <transition
          enter-active-class="transition-all duration-300 ease-out"
          leave-active-class="transition-all duration-300 ease-out"
          enter-from-class="opacity-0 -translate-y-[5px]"
          leave-to-class="opacity-0 -translate-y-[5px]"
        >
          <p
            v-if="errorMessage"
            class="flex items-center justify-center gap-2 text-[#e74c3c] text-[0.9rem] mt-4"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
              class="w-[18px] h-[18px]"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
            {{ errorMessage }}
          </p>
        </transition>
      </div>

      <!-- Verify Button -->
      <button
        class="flex items-center justify-center gap-3 w-full py-4 px-8 font-['Nunito'] text-[1.1rem] font-bold text-white bg-gradient-to-br from-[#7fb7a4] to-[#6da491] border-none rounded-2xl cursor-pointer transition-all duration-300 shadow-[0_4px_15px_rgba(127,183,164,0.4)] hover:not:disabled:-translate-y-0.5 hover:not:disabled:shadow-[0_8px_25px_rgba(127,183,164,0.5)] active:not:disabled:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed"
        :disabled="isLoading || otpCode.length !== 6"
        @click="handleVerify"
      >
        <span
          v-if="isLoading"
          class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-[spin_0.8s_linear_infinite]"
        ></span>
        {{ isLoading ? t('auth.verifyEmail.verifying') : t('auth.verifyEmail.verify') }}
      </button>

      <!-- Resend Section -->
      <div class="text-center mt-6 pt-6 border-t border-[rgba(127,183,164,0.2)]">
        <p class="font-sans text-[0.9rem] text-[#6b7280] mb-2">
          {{ t('auth.verifyEmail.didNotReceive') }}
        </p>
        <button
          v-if="resendCooldown === 0"
          class="bg-transparent border-none text-[#7fb7a4] font-['Nunito'] text-base font-semibold cursor-pointer transition-colors duration-200 hover:not:disabled:text-[#6da491] hover:not:disabled:underline disabled:opacity-60 disabled:cursor-not-allowed"
          :disabled="isResending"
          @click="handleResend"
        >
          {{ isResending ? t('auth.verifyEmail.resending') : t('auth.verifyEmail.resend') }}
        </button>
        <span v-else class="font-sans text-[0.9rem] text-[#5a4632]">
          {{ t('auth.verifyEmail.resendAvailable', { seconds: resendCooldown }) }}
        </span>
      </div>

      <!-- Back to Login -->
      <div class="text-center mt-6">
        <router-link
          to="/login"
          class="inline-flex items-center gap-2 text-[#5a4632] font-sans text-[0.9rem] no-underline transition-colors duration-200 hover:text-[#5a4632]"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="w-4 h-4"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
            />
          </svg>
          {{ t('auth.verifyEmail.backToLogin') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../store/authStore';
import { showSuccess, showError } from '../store/toast';
import { AuthService } from '../services/authService';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';

const router = useRouter();
const route = useRoute();
const { t } = useI18n();
const authStore = useAuthStore();

// State
const otpDigits = ref<string[]>(['', '', '', '', '', '']);
const isLoading = ref(false);
const isResending = ref(false);
const hasError = ref(false);
const errorMessage = ref('');
const resendCooldown = ref(0);
const inputRefs = ref<(HTMLInputElement | null)[]>([]);

// Get email from route query
const email = computed(() => {
  return (route.query.email as string) || '';
});

// Computed OTP code
const otpCode = computed(() => otpDigits.value.join(''));

// Cooldown timer
let cooldownInterval: ReturnType<typeof setInterval> | null = null;

const startCooldown = (seconds: number): void => {
  resendCooldown.value = seconds;
  if (cooldownInterval) clearInterval(cooldownInterval);
  cooldownInterval = setInterval(() => {
    resendCooldown.value--;
    if (resendCooldown.value <= 0) {
      if (cooldownInterval) clearInterval(cooldownInterval);
    }
  }, 1000);
};

// Input refs management
const setInputRef = (el: unknown, index: number): void => {
   
  inputRefs.value[index] = el as HTMLInputElement;
};

// Handle input
const handleInput = (index: number, event: Event): void => {
  const input = event.target as HTMLInputElement;
  const value = input.value;

  // Only allow digits
  if (value && !/^\d$/.test(value)) {
     
    otpDigits.value[index] = '';
    return;
  }

   
  otpDigits.value[index] = value;

  // Auto-focus next input
  if (value && index < 5) {
    inputRefs.value[index + 1]?.focus();
  }

  // Auto-submit when complete
  if (otpCode.value.length === 6) {
    handleVerify();
  }
};

// Handle keydown for backspace navigation
const handleKeydown = (index: number, event: KeyboardEvent): void => {
   
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
     
    inputRefs.value[index - 1]?.focus();
  }
};

// Handle paste
const handlePaste = (event: ClipboardEvent): void => {
  event.preventDefault();
  const pastedData = event.clipboardData?.getData('text') || '';
  const digits = pastedData.replaceAll(/\D/g, '').slice(0, 6);

  if (digits.length > 0) {
    for (let i = 0; i < 6; i++) {
       
      otpDigits.value[i] = digits[i] || '';
    }
    // Focus last filled input or first empty
    const focusIndex = Math.min(digits.length, 5);
     
    inputRefs.value[focusIndex]?.focus();

    // Auto-submit if complete
    if (digits.length === 6) {
      handleVerify();
    }
  }
};

// Verify OTP
const handleVerify = async (): Promise<void> => {
  if (otpCode.value.length !== 6 || isLoading.value) return;

  isLoading.value = true;
  hasError.value = false;
  errorMessage.value = '';

  try {
    const response = await AuthService.verifyOtp(email.value, otpCode.value);

    if (response.access_token && response.user) {
      authStore.setAuth(response);
      showSuccess(t('auth.verifyEmail.successMessage'), t('auth.verifyEmail.successTitle'));

      let redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/upload';
      sessionStorage.removeItem('redirectAfterAuth');

      // Security: Prevent Open Redirects
      // Ensure path starts with / and is not a protocol-relative URL (//)
      if (!redirectPath.startsWith('/') || redirectPath.startsWith('//')) {
        redirectPath = '/upload';
      }

      router.push(redirectPath);
    }
  } catch (err: unknown) {
    hasError.value = true;
    const message = err instanceof Error ? err.message : t('auth.verifyEmail.verificationFailed');
    errorMessage.value = message;

    // Clear inputs on error
    otpDigits.value = ['', '', '', '', '', ''];
    inputRefs.value[0]?.focus();
  } finally {
    isLoading.value = false;
  }
};

// Resend OTP
const handleResend = async (): Promise<void> => {
  if (isResending.value || resendCooldown.value > 0) return;

  isResending.value = true;
  errorMessage.value = '';

  try {
    await AuthService.resendOtp(email.value);
    showSuccess(t('auth.verifyEmail.codeSentMessage'), t('auth.verifyEmail.codeSentTitle'));
    startCooldown(60);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : t('auth.verifyEmail.resendFailedMessage');
    showError(message, t('auth.verifyEmail.resendFailedTitle'));
  } finally {
    isResending.value = false;
  }
};

// Lifecycle
onMounted(() => {
  if (!email.value) {
    router.push('/register');
    return;
  }

  // Focus first input
  inputRefs.value[0]?.focus();

  // Start initial cooldown (user just registered)
  startCooldown(60);
});

onUnmounted(() => {
  if (cooldownInterval) clearInterval(cooldownInterval);
});
</script>
