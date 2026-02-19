<template>
  <div>
    <AuthForm :initial-mode="mode" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import AuthForm from '../components/AuthForm.vue';
import { useSeo } from '../composables/useSeo';

interface Props {
  mode?: 'login' | 'register';
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'login',
});

const { t } = useI18n();

// SEO Setup
const { setMetaTags, resetMetaTags } = useSeo();
const pageTitle = computed(() =>
  props.mode === 'register'
    ? `${t('auth.register')} | Purrfect Spots`
    : `${t('auth.login')} | Purrfect Spots`
);

onMounted(() => {
  setMetaTags({
    title: pageTitle.value,
    description:
      props.mode === 'register' ? t('auth.createAccountToStart') : t('auth.signInToContinue'),
    type: 'website',
  });
});

onUnmounted(() => {
  resetMetaTags();
});
</script>

<style scoped>
/* Additional styling if needed */
</style>
