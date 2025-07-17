<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <AuthForm :initial-mode="mode" />
  </div>
</template>

<script setup lang="ts">
import AuthForm from '../components/AuthForm.vue';

interface Props {
  mode?: 'login' | 'signin';
}

withDefaults(defineProps<Props>(), {
  mode: 'login'
});
</script>

<style scoped>
/* Additional styling if needed */
</style>
