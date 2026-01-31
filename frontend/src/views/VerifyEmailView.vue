<template>
  <div class="verify-container">
    <!-- Animated Background -->
    <GhibliBackground />

    <!-- Main Card -->
    <div class="verify-card">
      <!-- Header (No Icon) -->
      <div class="verify-header">
        <h1 class="verify-title">Verify Your Email</h1>
        <p class="verify-subtitle">
          We sent a 6-digit code to<br />
          <strong class="email-display">{{ email }}</strong>
        </p>
      </div>

      <!-- OTP Input Section -->
      <div class="otp-section">
        <div class="otp-inputs">
          <input
            v-for="(_, index) in 6"
            :key="index"
            :ref="(el) => setInputRef(el, index)"
            v-model="otpDigits[index]"
            type="text"
            inputmode="numeric"
            maxlength="1"
            class="otp-input"
            :class="{ 'has-value': otpDigits[index], error: hasError }"
            @input="handleInput(index, $event)"
            @keydown="handleKeydown(index, $event)"
            @paste="handlePaste"
            @focus="hasError = false"
          />
        </div>

        <!-- Error Message -->
        <transition name="fade">
          <p v-if="errorMessage" class="error-message">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
              class="error-icon"
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
        class="verify-btn"
        :disabled="isLoading || otpCode.length !== 6"
        @click="handleVerify"
      >
        <span v-if="isLoading" class="loading-spinner"></span>
        {{ isLoading ? 'Verifying...' : 'Verify Email' }}
      </button>

      <!-- Resend Section -->
      <div class="resend-section">
        <p class="resend-text">Didn't receive the code?</p>
        <button
          v-if="resendCooldown === 0"
          class="resend-btn"
          :disabled="isResending"
          @click="handleResend"
        >
          {{ isResending ? 'Sending...' : 'Resend Code' }}
        </button>
        <span v-else class="cooldown-text"> Resend available in {{ resendCooldown }}s </span>
      </div>

      <!-- Back to Login -->
      <div class="back-link">
        <router-link to="/login">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="back-icon"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
            />
          </svg>
          Back to Login
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../store/authStore';
import { showSuccess, showError } from '../store/toast';
import { AuthService } from '../services/authService';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';

const router = useRouter();
const route = useRoute();
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

const startCooldown = (seconds: number) => {
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
const setInputRef = (el: unknown, index: number) => {
  inputRefs.value[index] = el as HTMLInputElement;
};

// Handle input
const handleInput = (index: number, event: Event) => {
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
const handleKeydown = (index: number, event: KeyboardEvent) => {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    inputRefs.value[index - 1]?.focus();
  }
};

// Handle paste
const handlePaste = (event: ClipboardEvent) => {
  event.preventDefault();
  const pastedData = event.clipboardData?.getData('text') || '';
  const digits = pastedData.replace(/\D/g, '').slice(0, 6);

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
const handleVerify = async () => {
  if (otpCode.value.length !== 6 || isLoading.value) return;

  isLoading.value = true;
  hasError.value = false;
  errorMessage.value = '';

  try {
    const response = await AuthService.verifyOtp(email.value, otpCode.value);

    if (response.access_token && response.user) {
      authStore.setAuth(response);
      showSuccess('Email verified successfully!', 'Welcome');

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
    const message = err instanceof Error ? err.message : 'Verification failed';
    errorMessage.value = message;

    // Clear inputs on error
    otpDigits.value = ['', '', '', '', '', ''];
    inputRefs.value[0]?.focus();
  } finally {
    isLoading.value = false;
  }
};

// Resend OTP
const handleResend = async () => {
  if (isResending.value || resendCooldown.value > 0) return;

  isResending.value = true;
  errorMessage.value = '';

  try {
    await AuthService.resendOtp(email.value);
    showSuccess('Verification code sent!', 'Check your email');
    startCooldown(60);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Failed to resend code';
    showError(message, 'Resend Failed');
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

<style scoped>
/* Container */
.verify-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  position: relative;
  overflow: hidden;
  background-color: #eaf6f3;
}

/* Card */
.verify-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 2rem;
  padding: 3rem;
  max-width: 450px;
  width: 100%;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.4) inset;
  position: relative;
  z-index: 1;
}

/* Header */
.verify-header {
  text-align: center;
  margin-bottom: 2rem;
}

/* DELETED: .email-icon style blocks */

.verify-title {
  font-family: 'Nunito', sans-serif;
  font-size: 1.8rem;
  font-weight: 800;
  color: #5a4632;
  margin-bottom: 0.75rem;
}

.verify-subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  color: #7d7d7d;
  line-height: 1.6;
}

.email-display {
  color: #5a4632;
  word-break: break-all;
}

/* OTP Section */
.otp-section {
  margin-bottom: 1.5rem;
}

.otp-inputs {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-bottom: 1rem;
  width: 100%;
}

.otp-input {
  width: 50px;
  height: 60px;
  text-align: center;
  font-family: 'Courier New', monospace;
  font-size: 1.5rem;
  font-weight: bold;
  color: #5a4632;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(127, 183, 164, 0.3);
  border-radius: 1rem;
  outline: none;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.otp-input:focus {
  border-color: #7fb7a4;
  box-shadow: 0 0 0 4px rgba(127, 183, 164, 0.15);
  transform: scale(1.05);
}

.otp-input.has-value {
  background: white;
  border-color: #7fb7a4;
}

.otp-input.error {
  border-color: #e74c3c;
  animation: shake 0.4s ease-in-out;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-5px);
  }
  75% {
    transform: translateX(5px);
  }
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #e74c3c;
  font-size: 0.9rem;
  margin-top: 1rem;
}

.error-icon {
  width: 18px;
  height: 18px;
}

/* Verify Button */
.verify-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  padding: 1rem 2rem;
  font-family: 'Nunito', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: white;
  background: linear-gradient(135deg, #7fb7a4 0%, #6da491 100%);
  border: none;
  border-radius: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(127, 183, 164, 0.4);
}

.verify-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(127, 183, 164, 0.5);
}

.verify-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Resend Section */
.resend-section {
  text-align: center;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(127, 183, 164, 0.2);
}

.resend-text {
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  color: #7d7d7d;
  margin-bottom: 0.5rem;
}

.resend-btn {
  background: none;
  border: none;
  color: #7fb7a4;
  font-family: 'Nunito', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s ease;
}

.resend-btn:hover:not(:disabled) {
  color: #6da491;
  text-decoration: underline;
}

.resend-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cooldown-text {
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  color: #888;
}

/* Back Link */
.back-link {
  text-align: center;
  margin-top: 1.5rem;
}

.back-link a {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #7d7d7d;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  text-decoration: none;
  transition: color 0.2s ease;
}

.back-link a:hover {
  color: #5a4632;
}

.back-icon {
  width: 16px;
  height: 16px;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

/* Responsive */
@media (max-width: 480px) {
  .verify-card {
    padding: 2rem 1.5rem;
  }

  .otp-inputs {
    gap: 0.25rem; /* Smaller gap for mobile */
  }

  /* Make inputs flexible to fit screen */
  .otp-input {
    flex: 1; /* Grow to fill available space */
    width: auto; /* Allow shrink/growth */
    min-width: 36px; /* Minimum touch target */
    height: 50px;
    font-size: 1.25rem;
    padding: 0;
  }
}
</style>
