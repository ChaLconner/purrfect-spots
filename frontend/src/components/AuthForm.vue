<template>
  <div class="auth-container">
    <!-- Animated Background Clouds -->
    <GhibliBackground />

    <!-- Main Content -->
    <div class="auth-card">
      <!-- Left Side - Illustration -->
      <div class="auth-illustration">
        <div class="illustration-content">
          <img :src="catIllustrationUrl" :alt="$t('auth.catIllustrationAlt')" class="cat-image" />
          <div class="illustration-text">
            <h2 class="welcome-title">Purrfect Spots</h2>
            <p class="welcome-subtitle">{{ $t('auth.discoverSpots') }}</p>
          </div>
        </div>
      </div>

      <!-- Right Side - Form -->
      <div class="auth-form-section">
        <div class="form-header">
          <h1 class="form-title">{{ isLogin ? $t('auth.welcomeBack') : $t('auth.joinUs') }}</h1>
          <p class="form-subtitle">
            {{ isLogin ? $t('auth.signInToContinue') : $t('auth.createAccountToStart') }}
          </p>
        </div>

        <form class="auth-form" novalidate @submit.prevent="throttledSubmit">
          <!-- Email Field -->
          <div class="form-group">
            <BaseInput
              id="email"
              v-model="form.email"
              type="email"
              required
              :placeholder="$t('auth.emailPlaceholder')"
              :label="$t('auth.email')"
              block
              autocomplete="username"
              :error="formErrors.email"
            />
          </div>

          <!-- Password Field -->
          <div class="form-group">
            <BaseInput
              id="password"
              v-model="form.password"
              type="password"
              required
              :placeholder="$t('auth.passwordPlaceholder')"
              :label="$t('auth.password')"
              block
              :autocomplete="isLogin ? 'current-password' : 'new-password'"
              :error="formErrors.password"
            />

            <!-- Password Strength Meter (Register only) -->
            <transition name="fade">
              <PasswordStrengthMeter v-if="!isLogin" :password="form.password" />
            </transition>

            <p v-if="!isLogin" class="form-hint">{{ $t('auth.minPasswordLength') }}</p>
            <div v-if="isLogin" class="forgot-password-link">
              <router-link to="/forgot-password">{{ $t('auth.forgotPassword') }}</router-link>
            </div>
          </div>

          <!-- Full Name Field (Sign Up only) -->
          <div v-if="!isLogin" class="form-group">
            <BaseInput
              id="name"
              v-model="form.name"
              type="text"
              required
              :placeholder="$t('auth.yourNamePlaceholder')"
              :label="$t('auth.fullName')"
              block
              autocomplete="name"
              :error="formErrors.name"
            />
          </div>

          <BaseButton type="submit" block size="lg" class="mt-2" :loading="isEmailLoading">
            {{ isLogin ? $t('auth.login') : $t('auth.createAccount') }}
          </BaseButton>
        </form>

        <!-- OAuth Divider -->
        <div class="divider">
          <span class="divider-line"></span>
          <span class="divider-text">{{ $t('auth.orContinueWith') }}</span>
          <span class="divider-line"></span>
        </div>

        <!-- Google OAuth Button -->
        <BaseButton
          type="button"
          variant="outline"
          block
          size="lg"
          class="bg-white border-2 border-sage/60 text-brown shadow-sm hover:bg-white hover:border-sage hover:shadow-md transition-all"
          :loading="isGoogleLoading"
          @click="handleGoogleLogin"
        >
          <template #icon-left>
            <svg class="w-5 h-5 mr-3" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
          </template>
          <span class="text-brown">Google</span>
        </BaseButton>

        <!-- Switch Mode Link -->
        <div class="switch-mode">
          <span class="switch-text">
            {{ isLogin ? $t('auth.dontHaveAccount') : $t('auth.alreadyHaveAccount') }}
          </span>
          <router-link :to="isLogin ? '/register' : '/login'" class="switch-link">
            {{ isLogin ? $t('auth.signUp') : $t('auth.login') }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const catIllustrationUrl = '/cat-illustration.png';

import { useAuthForm } from '@/composables/useAuthForm';
import { useAuthStore } from '@/store/authStore';
import { useThrottleFn } from '@/composables/useThrottle';
import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { BaseButton, BaseInput } from '@/components/ui';

interface Props {
  initialMode?: 'login' | 'register';
}

const props = withDefaults(defineProps<Props>(), {
  initialMode: 'login',
});

const router = useRouter();
const {
  isLogin,
  isEmailLoading,
  isGoogleLoading,
  form,
  formErrors,
  handleSubmit,
  handleGoogleLogin,
} = useAuthForm(props.initialMode);

// Throttle submit to prevent double-click issues even before loading state kicks in
const throttledSubmit = useThrottleFn(handleSubmit, 1000, { trailing: false });

// Watch for changes in initialMode prop to sync external changes
watch(
  () => props.initialMode,
  (newMode) => {
    isLogin.value = newMode !== 'register';
  }
);

// Check if user is already logged in
const checkAuthAndRedirect = () => {
  const authStore = useAuthStore();
  if (authStore.isUserReady) {
    // 1. Priority: Deep Linking (Return to intended page)
    const deepLink = globalThis.sessionStorage?.getItem('redirectAfterAuth');
    if (deepLink) {
      globalThis.sessionStorage?.removeItem('redirectAfterAuth');
      router.push(deepLink);
      return;
    }

    // 2. Priority: Admin User -> Admin Dashboard
    if (authStore.isAdmin) {
      router.push('/admin');
      return;
    }

    // 3. Priority: General User -> Home/Map (Contextual default)
    router.push('/');
  }
};

onMounted(() => {
  checkAuthAndRedirect();
});

// Watch for delayed auth initialization (e.g. refresh token success)
watch(
  () => useAuthStore().isUserReady,
  (isReady) => {
    if (isReady) {
      checkAuthAndRedirect();
    }
  }
);
</script>

<style scoped>
/* ============================================
 * AUTH CONTAINER - Full Page Layout
 * ============================================ */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
  background-color: #eaf6f3; /* Solid mint color for seamless look */
  /* background: linear-gradient(135deg, #EAF6F3 0%, #D4EFE6 50%, #C8E6DC 100%); Removed gradient */
}

/* ============================================
 * ANIMATED CLOUDS BACKGROUND
 * ============================================ */

/* ============================================
 * AUTH CARD - Main Container
 * ============================================ */
.auth-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
  max-width: 1000px;
  min-height: 600px;
  /* Increased transparency for better blending */
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 2rem;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.4) inset,
    0 -2px 0 rgba(255, 255, 255, 0.1) inset;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* ============================================
 * LEFT SIDE - ILLUSTRATION
 * ============================================ */
.auth-illustration {
  /* Semi-transparent gradient to let clouds show through slightly */
  background: linear-gradient(
    135deg,
    rgba(127, 183, 164, 0.85) 0%,
    rgba(149, 196, 180, 0.85) 50%,
    rgba(168, 212, 197, 0.85) 100%
  );
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  position: relative;
  overflow: hidden;
}

.illustration-content {
  text-align: center;
  z-index: 2;
}

.cat-image {
  width: 280px;
  height: 280px;
  object-fit: cover;
  border-radius: 50%;
  border: 6px solid rgba(255, 255, 255, 0.4);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.15),
    0 0 0 12px rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
  transition: transform 0.3s ease;
  display: block;
  margin: 0 auto;
}

.cat-image:hover {
  transform: scale(1.05);
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-15px);
  }
}

.illustration-text {
  margin-top: 2rem;
}

.welcome-title {
  font-family: 'Nunito', sans-serif;
  font-size: 1.8rem;
  font-weight: 800;
  color: white;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 0.5rem;
}

.welcome-subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.9);
  max-width: 250px;
  margin: 0 auto;
  line-height: 1.5;
}

/* Floating Decorations */
.floating-paw {
  position: absolute;
  font-size: 1.5rem;
  opacity: 0.6;
  animation: floatPaw 4s ease-in-out infinite;
}

.paw-1 {
  top: 15%;
  left: 15%;
  animation-delay: 0s;
}

.paw-2 {
  top: 25%;
  right: 20%;
  animation-delay: 1s;
  font-size: 1.2rem;
}

.paw-3 {
  bottom: 20%;
  left: 25%;
  animation-delay: 2s;
  font-size: 1.8rem;
}

@keyframes floatPaw {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
    opacity: 0.6;
  }
  50% {
    transform: translateY(-10px) rotate(10deg);
    opacity: 0.9;
  }
}

/* ============================================
 * RIGHT SIDE - FORM SECTION
 * ============================================ */
.auth-form-section {
  padding: 3rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-header {
  text-align: center;
  margin-bottom: 2rem;
}

.form-title {
  font-family: 'Nunito', sans-serif;
  font-size: 2rem;
  font-weight: 800;
  color: #5a4632;
  margin-bottom: 0.5rem;
}

.form-subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  color: #5a4632; /* Darkened from #7d7d7d */
}

/* ============================================
 * FORM ELEMENTS
 * ============================================ */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: 'Nunito', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  color: #5a4632;
}

.form-hint {
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem;
  color: #5a4632; /* Darkened from #7d7d7d */
  margin-top: 0.25rem;
  margin-left: 0.5rem;
}

.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 1rem 1.25rem;
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  color: #5a4632;
  background: rgba(255, 255, 255, 0.7);
  border: 2px solid rgba(127, 183, 164, 0.2);
  border-radius: 1rem;
  outline: none;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: #6b7280; /* gray-500 */
}

.form-input:focus {
  background: rgba(255, 255, 255, 0.95);
  border-color: #7fb7a4;
  box-shadow: 0 0 0 4px rgba(127, 183, 164, 0.15);
}

.form-input:hover:not(:focus) {
  border-color: rgba(127, 183, 164, 0.4);
}

.password-input {
  padding-right: 3rem;
}

.password-toggle-btn {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  cursor: pointer;
  pointer-events: auto;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280; /* gray-500 */
  transition: color 0.3s ease;
}

.password-toggle-btn:hover {
  color: #7fb7a4;
}

.eye-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.forgot-password-link {
  text-align: right;
  margin-top: 0.25rem;
}

.forgot-password-link a {
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  color: #7fb7a4;
  text-decoration: none;
  font-weight: 500;
}

.forgot-password-link a:hover {
  text-decoration: underline;
}

/* ============================================
 * BUTTONS (Obsolete - Migrated to BaseButton)
 * ============================================ */
/* Removed .submit-btn, .google-btn as they are replaced by BaseButton */

/* ============================================
 * DIVIDER
 * ============================================ */
.divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(127, 183, 164, 0.3), transparent);
}

.divider-text {
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  color: #6b7280; /* gray-500 */
  white-space: nowrap;
}

/* Removed google-btn styles */

/* ============================================
 * SWITCH MODE LINK
 * ============================================ */
.switch-mode {
  text-align: center;
  margin-top: 1.5rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
}

.switch-text {
  color: #5a4632; /* Darkened from #7d7d7d */
}

.switch-link {
  color: #a65d37;
  font-weight: 700;
  text-decoration: none;
  margin-left: 0.25rem;
  transition: color 0.2s ease;
}

.switch-link:hover {
  color: #6da491;
  text-decoration: underline;
}

/* ============================================
 * RESPONSIVE DESIGN
 * ============================================ */
@media (max-width: 900px) {
  .auth-card {
    grid-template-columns: 1fr;
    max-width: 480px;
    min-height: auto;
  }

  .auth-illustration {
    padding: 2rem;
    order: -1;
  }

  .cat-image {
    width: 160px;
    height: 160px;
  }

  .welcome-title {
    font-size: 1.4rem;
  }

  .welcome-subtitle {
    font-size: 0.9rem;
  }

  .auth-form-section {
    padding: 2rem;
  }

  .form-title {
    font-size: 1.6rem;
  }
}

@media (max-width: 480px) {
  .auth-container {
    padding: 1rem;
  }

  .auth-illustration {
    padding: 1.5rem;
  }

  .cat-image {
    width: 120px;
    height: 120px;
  }

  .auth-form-section {
    padding: 1.5rem;
  }

  .form-input {
    padding: 0.875rem 1rem;
  }

  .submit-btn {
    padding: 0.875rem 1.5rem;
  }
}
</style>
