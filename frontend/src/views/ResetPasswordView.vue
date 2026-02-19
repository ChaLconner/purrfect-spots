<template>
  <div class="auth-container">
    <!-- Animated Background Clouds -->
    <GhibliBackground />

    <!-- Main Content -->
    <div class="auth-card">
      <!-- Left Side - Illustration -->
      <div class="auth-illustration">
        <div class="illustration-content">
          <img src="/cat-illustration.png" alt="Cute cat illustration" class="cat-image" />
          <div class="illustration-text">
            <h2 class="welcome-title">{{ $t('auth.resetPasswordIllustrationTitle') }}</h2>
            <p class="welcome-subtitle">{{ $t('auth.resetPasswordIllustrationSubtitle') }}</p>
          </div>
        </div>
      </div>

      <!-- Right Side - Form -->
      <div class="auth-form-section">
        <div class="form-header">
          <h1 class="form-title">{{ $t('auth.resetPasswordTitle') }}</h1>
          <p class="form-subtitle">{{ $t('auth.resetPasswordSubtitle') }}</p>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <BaseInput
              id="password"
              v-model="password"
              type="password"
              required
              :placeholder="$t('auth.passwordPlaceholder')"
              :label="$t('auth.newPassword')"
              block
              autocomplete="new-password"
              :disabled="isLoading"
            />
            <PasswordStrengthMeter :password="password" />
          </div>

          <div class="form-group confirm-group">
            <BaseInput
              id="confirmPassword"
              v-model="confirmPassword"
              type="password"
              required
              :placeholder="$t('auth.passwordPlaceholder')"
              :label="$t('auth.confirmNewPassword')"
              block
              autocomplete="new-password"
              :disabled="isLoading"
              :error="passwordMismatch ? $t('auth.passwordsDoNotMatch') : ''"
            />
          </div>

          <BaseButton
            type="submit"
            block
            size="lg"
            class="submit-mt"
            :loading="isLoading"
            :disabled="passwordMismatch || password.length < 8"
          >
            {{ $t('auth.updatePassword') }}
          </BaseButton>
        </form>

        <div class="switch-mode">
          <router-link to="/login" class="switch-link">
            {{ $t('auth.rememberPassword') }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { showSuccess, showError } from '@/store/toast';
import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { BaseButton, BaseInput } from '@/components/ui';
import { useSeo } from '@/composables/useSeo';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const password = ref('');
const confirmPassword = ref('');
const isLoading = ref(false);
const token = ref('');

const passwordMismatch = computed(() => {
  return confirmPassword.value && password.value !== confirmPassword.value;
});

// SEO Setup
const { setMetaTags, resetMetaTags } = useSeo();

onMounted(() => {
  setMetaTags({
    title: `${t('auth.resetPasswordTitle')} | Purrfect Spots`,
    description: t('auth.resetPasswordSubtitle'),
    type: 'website',
  });

  // Handle Supabase Implicit Flow (Hash Fragment)
  const hash = globalThis.location.hash;
  const hashParams = new URLSearchParams(hash.substring(1));
  const accessToken = hashParams.get('access_token');
  const errorDescription = hashParams.get('error_description');

  if (errorDescription) {
    showError(decodeURIComponent(errorDescription), 'Error');
    router.push('/login');
    return;
  }

  const queryToken = route.query.token as string;
  token.value = accessToken || queryToken;

  if (!token.value) {
    showError(t('auth.invalidToken'), t('common.error'));
    router.push('/login');
  }
});

onUnmounted(() => {
  resetMetaTags();
});

const handleSubmit = async (): Promise<void> => {
  if (password.value !== confirmPassword.value) {
    showError(t('auth.passwordsDoNotMatch'), t('common.validationError'));
    return;
  }

  if (password.value.length < 8) {
    showError(t('auth.passwordTooShort'), t('common.validationError'));
    return;
  }

  isLoading.value = true;
  try {
    await apiV1.post('/auth/reset-password', {
      token: token.value,
      new_password: password.value,
    });
    showSuccess(t('auth.passwordUpdated'), 'Success');
    router.push('/login');
  } catch (err: unknown) {
    let message = (err as Error).message || t('common.somethingWentWrong');
    if (message.includes('status code')) message = t('common.unableToProcess');
    showError(message, t('common.error'));
  } finally {
    isLoading.value = false;
  }
};
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
  background-color: #eaf6f3;
}

/* ============================================
 * AUTH CARD - Main Container
 * ============================================ */
.auth-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
  max-width: 1000px;
  min-height: 580px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 2rem;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.4) inset;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* ============================================
 * LEFT SIDE - ILLUSTRATION
 * ============================================ */
.auth-illustration {
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
  width: 240px;
  height: 240px;
  object-fit: cover;
  border-radius: 50%;
  border: 6px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
  animation: float 6s ease-in-out infinite;
  display: block;
  margin: 0 auto;
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

.welcome-title {
  font-family: 'Nunito', sans-serif;
  font-size: 1.8rem;
  font-weight: 800;
  color: white;
  margin-top: 1.5rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.welcome-subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.9);
  max-width: 280px;
  margin: 0.5rem auto 0;
  line-height: 1.4;
}

/* ============================================
 * RIGHT SIDE - FORM SECTION
 * ============================================ */
.auth-form-section {
  padding: 3.5rem;
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
  color: #5a4632;
  opacity: 0.8;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.confirm-group {
  margin-bottom: 0.5rem;
}

.submit-mt {
  margin-top: 1rem;
}

/* ============================================
 * SWITCH MODE LINK
 * ============================================ */
.switch-mode {
  text-align: center;
  margin-top: 2rem;
}

.switch-link {
  font-family: 'Inter', sans-serif;
  color: #5a4632;
  font-weight: 600;
  text-decoration: none;
  font-size: 0.95rem;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.switch-link:hover {
  color: #a65d37;
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

  .auth-form-section {
    padding: 2.5rem;
  }
}

@media (max-width: 480px) {
  .auth-container {
    padding: 1rem;
  }

  .auth-form-section {
    padding: 2rem;
  }
}
</style>
