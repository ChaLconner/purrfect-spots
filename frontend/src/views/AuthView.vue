<template>
  <div>
    <AuthForm :initial-mode="mode" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue';
import AuthForm from '../components/AuthForm.vue';
import { useSeo } from '../composables/useSeo';

interface Props {
  mode?: 'login' | 'register';
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'login'
});

// SEO Setup
const { setMetaTags, resetMetaTags } = useSeo();
const pageTitle = computed(() => props.mode === 'register' ? 'Register | Purrfect Spots' : 'Login | Purrfect Spots');

onMounted(() => {
  setMetaTags({
    title: pageTitle.value,
    description: props.mode === 'register' 
      ? 'Create your Purrfect Spots account to share cat photos and discover cat-friendly locations.'
      : 'Sign in to your Purrfect Spots account to share cat photos and discover cat-friendly locations.',
    type: 'website'
  });
});

onUnmounted(() => {
  resetMetaTags();
});
</script>

<style scoped>
/* Additional styling if needed */
</style>
