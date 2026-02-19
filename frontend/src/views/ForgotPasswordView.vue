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
            <h2 class="welcome-title">Purrfect Spots</h2>
            <p class="welcome-subtitle">
              {{ $t('auth.forgotPasswordIllustration') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Right Side - Form -->
      <div class="auth-form-section">
        <div class="form-header">
          <h1 class="form-title">{{ $t('auth.forgotPasswordTitle') }}</h1>
          <p class="form-subtitle">{{ $t('auth.forgotPasswordSubtitle') }}</p>
        </div>

        <div v-if="isSuccess" class="success-message">
          <div class="success-icon">{{ $t('auth.checkInbox') }}</div>
          <p>
            {{ $t('auth.resetInstructionsSent', { email }) }}
          </p>
          <BaseButton block size="lg" class="mt-6" @click="router.push('/login')">
            {{ $t('auth.backToSignIn') }}
          </BaseButton>
        </div>

        <form v-else class="auth-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <BaseInput
              id="email"
              v-model="email"
              type="email"
              required
              :placeholder="$t('auth.emailPlaceholder')"
              :label="$t('auth.emailLabel')"
              block
              autocomplete="email"
              :disabled="isLoading"
            />
          </div>

          <BaseButton type="submit" block size="lg" class="submit-mt" :loading="isLoading">
            {{ $t('auth.sendResetLink') }}
          </BaseButton>
        </form>

        <div v-if="!isSuccess" class="switch-mode">
          <router-link to="/login" class="switch-link"> {{ $t('auth.backToSignIn') }} </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { showSuccess, showError } from '@/store/toast';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { BaseButton, BaseInput } from '@/components/ui';
import { useSeo } from '@/composables/useSeo';

const router = useRouter();
const { t } = useI18n();
const email = ref('');
const isLoading = ref(false);
const isSuccess = ref(false);

// SEO Setup
const { setMetaTags, resetMetaTags } = useSeo();

onMounted(() => {
  setMetaTags({
    title: `${t('auth.forgotPasswordTitle')} | Purrfect Spots`,
    description: t('auth.forgotPasswordSubtitle'),
    type: 'website',
  });
});

onUnmounted(() => {
  resetMetaTags();
});

const handleSubmit = async () => {
  if (!email.value) return;

  isLoading.value = true;
  try {
    await apiV1.post('/auth/forgot-password', { email: email.value });
    isSuccess.value = true;
    showSuccess(t('auth.checkInbox'));
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
  min-height: 550px;
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
  gap: 1.5rem;
}

.submit-mt {
  margin-top: 0.5rem;
}

/* ============================================
 * SUCCESS MESSAGE
 * ============================================ */
.success-message {
  text-align: center;
  padding: 1.5rem;
  background: rgba(127, 183, 164, 0.1);
  border-radius: 1.5rem;
  border: 1px solid rgba(127, 183, 164, 0.3);
}

.success-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.success-message p {
  font-family: 'Inter', sans-serif;
  color: #5a4632;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.success-message strong {
  color: #2f5244;
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
