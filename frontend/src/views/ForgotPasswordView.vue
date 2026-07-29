<template>
  <div
    class="min-h-screen flex items-center justify-center p-4 sm:p-8 relative overflow-hidden bg-mint-light"
  >
    <!-- Animated Background Clouds -->
    <GhibliBackground />

    <!-- Main Content -->
    <div
      class="grid grid-cols-1 md:grid-cols-2 w-full max-w-5xl md:min-h-[550px] bg-white/50 backdrop-blur-xl rounded-3xl shadow-xl border border-white/40 overflow-hidden relative z-10 max-md:max-w-md max-md:min-h-fit"
    >
      <!-- Left Side - Illustration -->
      <div
        class="bg-gradient-to-br from-mint/85 via-mint-hover/85 to-sage/85 flex flex-col items-center justify-center p-6 sm:p-8 md:p-12 relative overflow-hidden max-md:order-first"
      >
        <div class="text-center z-10">
          <img
            src="/cat-illustration.webp"
            alt="Cute cat illustration"
            class="w-40 h-40 md:w-60 md:h-60 object-cover rounded-full border-4 border-white/40 shadow-lg animate-float block mx-auto"
          />
          <div class="mt-8">
            <h2
              class="font-heading text-2xl md:text-3xl font-extrabold text-white drop-shadow-sm mt-6"
            >
              Purrfect Spots
            </h2>
            <p
              class="font-body text-sm md:text-base text-white/90 max-w-xs mx-auto leading-relaxed mt-2"
            >
              {{ $t('auth.forgotPasswordIllustration') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Right Side - Form -->
      <div class="p-8 md:p-14 flex flex-col justify-center max-md:p-10 max-sm:p-8">
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { apiV1 } from '@/utils/api';
import { showSuccess, showError } from '@/stores/toast';
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

const handleSubmit = async (): Promise<void> => {
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
