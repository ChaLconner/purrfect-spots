<template>
  <div class="auth-container">
    <GhibliBackground />

    <div class="auth-card">
      <div class="auth-illustration">
        <div class="illustration-content">
          <img src="/cat-illustration.png" alt="Cute cat" class="cat-image" />
          <div class="illustration-text">
            <h2 class="welcome-title">Welcome Back</h2>
            <p class="welcome-subtitle">Set your new password and start exploring!</p>
          </div>
        </div>
      </div>

      <div class="auth-form-section">
        <div class="form-header">
          <h1 class="form-title">Reset Password</h1>
          <p class="form-subtitle">Choose a strong password</p>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="password" class="form-label">New Password</label>
            <div class="input-wrapper">
              <input
                id="password"
                v-model="password"
                type="password"
                required
                placeholder="••••••••"
                class="form-input"
              />
            </div>
            <PasswordStrengthMeter :password="password" />
          </div>

          <div class="form-group">
            <label for="confirmParams" class="form-label">Confirm Password</label>
            <div class="input-wrapper">
              <input
                id="confirmPassword"
                v-model="confirmPassword"
                type="password"
                required
                placeholder="••••••••"
                class="form-input"
              />
            </div>
          </div>

          <button :disabled="isLoading" class="submit-btn">
            <span v-if="isLoading" class="loading-spinner"></span>
            {{ isLoading ? 'Updating...' : 'Set New Password' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiV1 } from '@/utils/api';
import { showSuccess, showError } from '@/store/toast';
import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useSeo } from '@/composables/useSeo';

const route = useRoute();
const router = useRouter();

const password = ref('');
const confirmPassword = ref('');
const isLoading = ref(false);
const token = ref('');

// SEO Setup
const { setMetaTags, resetMetaTags } = useSeo();

onMounted(() => {
  // Set SEO meta tags
  setMetaTags({
    title: 'Reset Password | Purrfect Spots',
    description: 'Set a new password for your Purrfect Spots account.',
    type: 'website',
  });

  // Handle Supabase Implicit Flow (Hash Fragment)
  const hash = globalThis.location.hash;
  const hashParams = new URLSearchParams(hash.substring(1)); // Remove leading '#'
  const accessToken = hashParams.get('access_token');

  // Handle specific Supabase "error" in hash
  const errorDescription = hashParams.get('error_description');
  if (errorDescription) {
    showError(decodeURIComponent(errorDescription), 'Error');
    router.push('/login');
    return;
  }

  // Fallback to query param (if used differently)
  const queryToken = route.query.token as string;

  token.value = accessToken || queryToken;

  if (!token.value) {
    showError('Invalid or expired reset link', 'Error');
    router.push('/login');
  }
});

onUnmounted(() => {
  resetMetaTags();
});

const handleSubmit = async (): Promise<void> => {
  if (password.value !== confirmPassword.value) {
    showError('Passwords do not match', 'Validation Error');
    return;
  }

  if (password.value.length < 8) {
    showError('Password must be at least 8 characters', 'Validation Error');
    return;
  }

  isLoading.value = true;
  try {
    await apiV1.post('/auth/reset-password', {
      token: token.value,
      new_password: password.value,
    });
    showSuccess('Password updated successfully. Please login.', 'Success');
    router.push('/login');
  } catch (err: unknown) {
    let message = (err as Error).message || 'Failed to reset password';
    if (message.includes('status code')) message = 'Invalid or expired token. Please try again.';
    showError(message, 'Error');
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Reusing styles... same as ForgotPasswordView */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background-color: #eaf6f3;
}
.auth-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
  max-width: 1000px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(20px);
  border-radius: 2rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}
.auth-illustration {
  background: linear-gradient(
    135deg,
    rgba(127, 183, 164, 0.85) 0%,
    rgba(149, 196, 180, 0.85) 50%,
    rgba(168, 212, 197, 0.85) 100%
  );
  padding: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.illustration-content {
  text-align: center;
}
.cat-image {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  border: 6px solid rgba(255, 255, 255, 0.4);
  object-fit: cover;
}
.welcome-title {
  font-family: 'Nunito', sans-serif;
  font-size: 1.8rem;
  font-weight: 800;
  color: white;
  margin-top: 1rem;
}
.welcome-subtitle {
  font-family: 'Inter', sans-serif;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 0.5rem;
}
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
}
.form-subtitle {
  font-family: 'Inter', sans-serif;
  color: #5a4632;
}
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
  font-family: 'Nunito', sans-serif;
  font-weight: 600;
  color: #5a4632;
}
.form-input {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid rgba(127, 183, 164, 0.2);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.7);
  outline: none;
  font-family: 'Inter', sans-serif;
}
.form-input:focus {
  background: white;
  border-color: #7fb7a4;
}
.submit-btn {
  width: 100%;
  padding: 1rem;
  font-family: 'Nunito', sans-serif;
  font-weight: 700;
  color: white;
  background: linear-gradient(135deg, #7fb7a4 0%, #6da491 100%);
  border: none;
  border-radius: 1rem;
  cursor: pointer;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .auth-card {
    grid-template-columns: 1fr;
    max-width: 450px;
  }
  .auth-illustration {
    display: none;
  }
}
</style>
