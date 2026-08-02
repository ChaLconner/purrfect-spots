<template>
  <AuthLayout :illustration-text="$t('auth.resetPasswordIllustrationSubtitle')">
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
  </AuthLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { formatFormErrorMessage } from '@/utils/apiErrors';
import { showSuccess, showError } from '@/stores/toast';
import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';
import AuthLayout from '@/components/auth/AuthLayout.vue';
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
    const message = formatFormErrorMessage(
      err,
      t('common.somethingWentWrong'),
      t('common.unableToProcess')
    );
    showError(message, t('common.error'));
  } finally {
    isLoading.value = false;
  }
};
</script>
