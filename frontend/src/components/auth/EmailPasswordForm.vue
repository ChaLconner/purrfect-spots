<script setup lang="ts">
import { ref, reactive } from 'vue';
import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';

interface Props {
  isLogin: boolean;
  isLoading: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'submit', form: { email: string; password: string; name: string }): void;
}>();

const showPassword = ref(false);

const form = reactive({
  email: '',
  password: '',
  name: '',
});

const handleSubmit = () => {
  emit('submit', { ...form });
};
</script>

<template>
  <form class="auth-form" novalidate @submit.prevent="handleSubmit">
    <!-- Email Field -->
    <div class="form-group">
      <label for="email" class="form-label"> Email </label>
      <div class="input-wrapper">
        <input
          id="email"
          v-model="form.email"
          type="email"
          required
          placeholder="your@email.com"
          class="form-input"
        />
      </div>
    </div>

    <!-- Password Field -->
    <div class="form-group">
      <label for="password" class="form-label"> Password </label>
      <div class="input-wrapper">
        <input
          id="password"
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          required
          placeholder="••••••••"
          class="form-input password-input"
        />
        <button
          type="button"
          class="password-toggle-btn"
          :aria-label="showPassword ? 'Hide password' : 'Show password'"
          @click="showPassword = !showPassword"
        >
          <!-- Eye Off Icon (Show Password) -->
          <svg
            v-if="!showPassword"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="eye-icon"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <!-- Eye Icon (Hide Password) -->
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="eye-icon"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
            />
          </svg>
        </button>
      </div>

      <!-- Password Strength Meter (Register only) -->
      <transition name="fade">
        <PasswordStrengthMeter v-if="!props.isLogin" :password="form.password" />
      </transition>

      <p v-if="!props.isLogin" class="form-hint">Must be at least 8 characters</p>
      <div v-if="props.isLogin" class="forgot-password-link">
        <router-link to="/forgot-password">Forgot Password?</router-link>
      </div>
    </div>

    <!-- Full Name Field (Sign Up only) -->
    <div v-if="!props.isLogin" class="form-group">
      <label for="name" class="form-label"> Full Name </label>
      <div class="input-wrapper">
        <input
          id="name"
          v-model="form.name"
          type="text"
          required
          placeholder="Your name"
          class="form-input"
        />
      </div>
    </div>

    <button :disabled="isLoading" class="submit-btn">
      <span v-if="isLoading" class="loading-spinner"></span>
      {{ isLoading ? 'Loading...' : props.isLogin ? 'Sign In' : 'Create Account' }}
    </button>
  </form>
</template>

<style scoped>
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
  color: #7d7d7d;
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
  color: #a0a0a0;
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
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a0a0a0;
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

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  padding: 1rem 2rem;
  margin-top: 0.5rem;
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

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(127, 183, 164, 0.5);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
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

/* Animations */
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
</style>
