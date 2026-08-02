<template>
  <AuthLayout :illustration-text="$t('auth.forgotPasswordIllustration')">
    <div class="text-center mb-8">
      <h1 class="font-heading text-2xl md:text-4xl font-extrabold text-mint-dark mb-2">
        {{ $t('auth.forgotPasswordTitle') }}
      </h1>
      <p class="font-body text-sm md:text-base text-mint-dark/80">
        {{ $t('auth.forgotPasswordSubtitle') }}
      </p>
    </div>

        <div
          v-if="isSuccess"
          class="text-center p-6 bg-mint/10 rounded-3xl border border-mint/30"
        >
          <div class="text-4xl mb-4">{{ $t('auth.checkInbox') }}</div>
          <p class="font-body text-mint-dark leading-relaxed mb-6">
            {{ $t('auth.resetInstructionsSent', { email }) }}
          </p>
          <BaseButton block size="lg" class="mt-6" @click="router.push('/login')">
            {{ $t('auth.backToSignIn') }}
          </BaseButton>
        </div>

        <form v-else class="flex flex-col gap-6" @submit.prevent="handleSubmit">
          <div class="flex flex-col gap-2">
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

          <BaseButton type="submit" block size="lg" class="mt-2" :loading="isLoading">
            {{ $t('auth.sendResetLink') }}
          </BaseButton>
        </form>

        <div v-if="!isSuccess" class="text-center mt-8">
          <router-link
            to="/login"
            class="inline-flex items-center gap-2 font-body text-mint-dark font-semibold text-sm no-underline transition-colors duration-200 hover:text-terracotta"
          >
            {{ $t('auth.backToSignIn') }}
          </router-link>
        </div>
  </AuthLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { formatFormErrorMessage } from '@/utils/apiErrors';
import { showSuccess, showError } from '@/stores/toast';
import AuthLayout from '@/components/auth/AuthLayout.vue';
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

const handleSubmit = async (): Promise<void> => {
  if (!email.value) return;

  isLoading.value = true;
  try {
    await apiV1.post('/auth/forgot-password', { email: email.value });
    isSuccess.value = true;
    showSuccess(t('auth.checkInbox'));
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
