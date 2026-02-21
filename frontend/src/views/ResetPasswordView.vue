<template>
  <div
    class="min-h-screen flex items-center justify-center p-4 sm:p-8 relative overflow-hidden bg-[#eaf6f3]"
  >
    <!-- Animated Background Clouds -->
    <GhibliBackground />

    <!-- Main Content -->
    <div
      class="grid grid-cols-1 md:grid-cols-2 w-full max-w-[1000px] md:min-h-[580px] bg-white/50 backdrop-blur-[20px] rounded-[2rem] shadow-[0_25px_50px_-12px_rgba(0,0,0,0.1),_0_0_0_1px_rgba(255,255,255,0.4)_inset] overflow-hidden relative z-10 max-md:max-w-[480px] max-md:min-h-fit"
    >
      <!-- Left Side - Illustration -->
      <div
        class="bg-gradient-to-br from-[rgba(127,183,164,0.85)] via-[rgba(149,196,180,0.85)] to-[rgba(168,212,197,0.85)] flex flex-col items-center justify-center p-6 sm:p-8 md:p-12 relative overflow-hidden max-md:order-[-1]"
      >
        <div class="text-center z-10">
          <img
            src="/cat-illustration.png"
            alt="Cute cat illustration"
            class="w-[160px] h-[160px] md:w-[240px] md:h-[240px] object-cover rounded-full border-6 border-white/40 shadow-[0_15px_30px_rgba(0,0,0,0.1)] animate-[float_6s_ease-in-out_infinite] block mx-auto"
          />
          <div class="mt-8">
            <h2
              class="font-['Nunito'] text-[1.4rem] md:text-[1.8rem] font-extrabold text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.1)] mt-6"
            >
              {{ $t('auth.resetPasswordIllustrationTitle') }}
            </h2>
            <p
              class="font-sans text-[0.9rem] md:text-base text-white/90 max-w-[280px] mx-auto leading-relaxed mt-2"
            >
              {{ $t('auth.resetPasswordIllustrationSubtitle') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Right Side - Form -->
      <div class="p-8 md:p-14 flex flex-col justify-center max-md:p-10 max-sm:p-8">
        <div class="text-center mb-8">
          <h1 class="font-['Nunito'] text-[1.6rem] md:text-4xl font-extrabold text-[#5a4632] mb-2">
            {{ $t('auth.resetPasswordTitle') }}
          </h1>
          <p class="font-sans text-[0.95rem] text-[#5a4632] opacity-80">
            {{ $t('auth.resetPasswordSubtitle') }}
          </p>
        </div>

        <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
          <div class="flex flex-col gap-2">
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

          <div class="flex flex-col gap-2 mb-2">
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
            class="mt-4"
            :loading="isLoading"
            :disabled="passwordMismatch || password.length < 8"
          >
            {{ $t('auth.updatePassword') }}
          </BaseButton>
        </form>

        <div class="text-center mt-8">
          <router-link
            to="/login"
            class="inline-flex items-center gap-2 font-sans text-[#5a4632] font-semibold text-[0.95rem] no-underline transition-colors duration-200 hover:text-[#a65d37]"
          >
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
