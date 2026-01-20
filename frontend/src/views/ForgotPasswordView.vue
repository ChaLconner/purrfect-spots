<template>
  <div class="auth-container">
    <GhibliBackground />

    <div class="auth-card">
      <div class="auth-illustration">
        <div class="illustration-content">
          <img src="/cat-illustration.png" alt="Cute cat illustration" class="cat-image" />
          <div class="illustration-text">
            <h2 class="welcome-title">Purrfect Spots</h2>
            <p class="welcome-subtitle">Reset your password to get back to the cute cats!</p>
          </div>
        </div>
      </div>

      <div class="auth-form-section">
        <div class="form-header">
          <h1 class="form-title">Forgot Password?</h1>
          <p class="form-subtitle">Enter your email to receive reset instructions</p>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="email" class="form-label">Email</label>
            <div class="input-wrapper">
              <input
                id="email"
                v-model="email"
                type="email"
                required
                placeholder="your@email.com"
                class="form-input"
              />
            </div>
          </div>

          <button :disabled="isLoading" class="submit-btn">
            <span v-if="isLoading" class="loading-spinner"></span>
            {{ isLoading ? 'Sending...' : 'Send Reset Link' }}
          </button>
        </form>

        <div class="switch-mode">
          <router-link to="/login" class="switch-link">Back to Sign In</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { apiV1 } from '@/utils/api';
import { showSuccess, showError } from '@/store/toast';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useSeo } from '@/composables/useSeo';

const email = ref('');
const isLoading = ref(false);

// SEO Setup
const { setMetaTags, resetMetaTags } = useSeo();

onMounted(() => {
  setMetaTags({
    title: 'Forgot Password | Purrfect Spots',
    description: 'Reset your Purrfect Spots password to regain access to your account.',
    type: 'website'
  });
});

onUnmounted(() => {
  resetMetaTags();
});

const handleSubmit = async () => {
    isLoading.value = true;
    try {
        await apiV1.post('/auth/forgot-password', { email: email.value });
        showSuccess('If an account exists, you will receive an email shortly.', 'Check your inbox');
        // We don't clear email or redirect immediately so user can see message
    } catch (err: unknown) {
        showError((err as Error).message || 'Something went wrong', 'Error');
    } finally {
        isLoading.value = false;
    }
};
</script>

<style scoped>
/* Reusing styles from AuthForm.vue for consistency */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
  background-color: #EAF6F3;
}



.auth-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
  max-width: 1000px;
  min-height: 500px; /* Slightly shorter than login */
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(20px);
  border-radius: 2rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.auth-illustration {
  background: linear-gradient(135deg, rgba(127, 183, 164, 0.85) 0%, rgba(149, 196, 180, 0.85) 50%, rgba(168, 212, 197, 0.85) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}

.illustration-content {
    text-align: center;
}

.cat-image {
  width: 200px; /* Slightly smaller */
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
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.9);
  max-width: 250px;
  margin: 0 auto;
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
  color: #5A4632;
}

.form-subtitle {
  font-family: 'Inter', sans-serif;
  color: #7D7D7D;
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
    color: #5A4632;
}

.form-input {
  width: 100%;
  padding: 1rem 1.25rem;
  font-family: 'Inter', sans-serif;
  border: 2px solid rgba(127, 183, 164, 0.2);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.7);
  outline: none;
  transition: all 0.3s ease;
}

.form-input:focus {
    background: white;
    border-color: #7FB7A4;
}

.submit-btn {
  width: 100%;
  padding: 1rem;
  margin-top: 0.5rem;
  font-family: 'Nunito', sans-serif;
  font-weight: 700;
  color: white;
  background: linear-gradient(135deg, #7FB7A4 0%, #6DA491 100%);
  border: none;
  border-radius: 1rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.submit-btn:hover:not(:disabled) {
    transform: translateY(-2px);
}

.submit-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.switch-mode {
    margin-top: 1.5rem;
    text-align: center;
}

.switch-link {
    color: #7FB7A4;
    font-weight: 600;
    text-decoration: none;
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
