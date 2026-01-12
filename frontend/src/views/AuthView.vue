<template>
  <div>
    <AuthForm :initial-mode="mode" />
  </div>
</template>

<script setup lang="ts">
import AuthForm from '../components/AuthForm.vue';

interface Props {
  mode?: 'login' | 'register';
}

withDefaults(defineProps<Props>(), {
  mode: 'login'
});
</script>

<style scoped>
/* Additional styling if needed */
</style>
