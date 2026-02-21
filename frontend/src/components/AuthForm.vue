<template>
  <div
    class="min-h-screen flex items-center justify-center p-4 sm:p-8 relative overflow-hidden bg-[#eaf6f3]"
  >
    <!-- Animated Background Clouds -->
    <GhibliBackground />

    <!-- Main Content -->
    <div
      class="grid grid-cols-1 md:grid-cols-2 w-full max-w-[1000px] md:min-h-[600px] bg-white/50 backdrop-blur-[20px] rounded-[2rem] shadow-[0_25px_50px_-12px_rgba(0,0,0,0.1),_0_0_0_1px_rgba(255,255,255,0.4)_inset,_-0_-2px_0_rgba(255,255,255,0.1)_inset] overflow-hidden relative z-10 max-md:max-w-[480px] max-md:min-h-fit"
    >
      <!-- Left Side - Illustration -->
      <div
        class="bg-gradient-to-br from-[rgba(127,183,164,0.85)] via-[rgba(149,196,180,0.85)] to-[rgba(168,212,197,0.85)] flex flex-col items-center justify-center p-6 sm:p-8 md:p-12 relative overflow-hidden max-md:order-[-1]"
      >
        <div class="text-center z-10">
          <img
            :src="catIllustrationUrl"
            :alt="$t('auth.catIllustrationAlt')"
            class="w-[120px] h-[120px] sm:w-[160px] sm:h-[160px] md:w-[280px] md:h-[280px] object-cover rounded-full border-4 md:border-6 border-white/40 shadow-[0_20px_40px_rgba(0,0,0,0.15),_0_0_0_8px_rgba(255,255,255,0.1)] md:shadow-[0_20px_40px_rgba(0,0,0,0.15),_0_0_0_12px_rgba(255,255,255,0.1)] animate-[float_6s_ease-in-out_infinite] transition-transform duration-300 hover:scale-105 block mx-auto"
          />
          <div class="mt-8">
            <h2
              class="font-['Nunito'] text-[1.4rem] md:text-[1.8rem] font-extrabold text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.1)] mb-2"
            >
              Purrfect Spots
            </h2>
            <p
              class="font-sans text-[0.9rem] md:text-base text-white/90 max-w-[250px] mx-auto leading-relaxed"
            >
              {{ $t('auth.discoverSpots') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Right Side - Form -->
      <div class="p-6 sm:p-8 md:p-12 flex flex-col justify-center">
        <div class="text-center mb-8">
          <h1 class="font-['Nunito'] text-[1.6rem] md:text-4xl font-extrabold text-[#5a4632] mb-2">
            {{ isLogin ? $t('auth.welcomeBack') : $t('auth.joinUs') }}
          </h1>
          <p class="font-sans text-[0.95rem] text-[#5a4632]">
            {{ isLogin ? $t('auth.signInToContinue') : $t('auth.createAccountToStart') }}
          </p>
        </div>

        <form class="flex flex-col gap-5" novalidate @submit.prevent="throttledSubmit">
          <!-- Email Field -->
          <div class="flex flex-col gap-2">
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
          <div class="flex flex-col gap-2">
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

            <p v-if="!isLogin" class="font-sans text-sm text-[#5a4632] mt-1 ml-2">
              {{ $t('auth.minPasswordLength') }}
            </p>
            <div v-if="isLogin" class="text-right mt-1">
              <router-link
                to="/forgot-password"
                class="font-sans text-[0.85rem] text-[#7fb7a4] no-underline font-medium hover:underline"
              >
                {{ $t('auth.forgotPassword') }}
              </router-link>
            </div>
          </div>

          <!-- Full Name Field (Sign Up only) -->
          <div v-if="!isLogin" class="flex flex-col gap-2">
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
        <div class="flex items-center gap-4 my-6">
          <span
            class="flex-1 h-px bg-gradient-to-r from-transparent via-[rgba(127,183,164,0.3)] to-transparent"
          ></span>
          <span class="font-sans text-[0.85rem] text-gray-500 whitespace-nowrap">{{
            $t('auth.orContinueWith')
          }}</span>
          <span
            class="flex-1 h-px bg-gradient-to-r from-transparent via-[rgba(127,183,164,0.3)] to-transparent"
          ></span>
        </div>

        <!-- Google OAuth Button -->
        <BaseButton
          type="button"
          variant="outline"
          block
          size="lg"
          class="bg-white border-2 border-[#a8d4c5] text-[#8b5a2b] shadow-sm hover:bg-white hover:border-[#7fb7a4] hover:shadow-md transition-all"
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
          <span class="text-[#8b5a2b]">Google</span>
        </BaseButton>

        <!-- Switch Mode Link -->
        <div class="text-center mt-6 font-sans text-[0.9rem]">
          <span class="text-[#5a4632]">
            {{ isLogin ? $t('auth.dontHaveAccount') : $t('auth.alreadyHaveAccount') }}
          </span>
          <router-link
            :to="isLogin ? '/register' : '/login'"
            class="text-[#a65d37] font-bold no-underline ml-1 transition-colors duration-200 hover:text-[#6da491] hover:underline"
          >
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
