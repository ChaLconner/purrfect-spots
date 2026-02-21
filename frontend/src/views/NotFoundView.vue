<template>
  <div class="flex flex-col items-center justify-center min-h-screen bg-gray-100">
    <h1 class="text-6xl font-bold text-gray-800">{{ $t('notFound.title') }}</h1>
    <p class="text-2xl text-gray-600 mt-4">{{ $t('notFound.message') }}</p>
    <router-link
      to="/"
      class="mt-8 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition duration-300"
    >
      {{ $t('notFound.goHome') }}
    </router-link>
  </div>
</template>

<script setup lang="ts">
// No script logic needed
</script>
