<template>
  <div class="flex flex-col items-center justify-center min-h-screen bg-gray-100">
    <h1 class="text-6xl font-bold text-gray-800">404</h1>
    <p class="text-2xl text-gray-600 mt-4">Page Not Found</p>
    <router-link
      to="/"
      class="mt-8 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition duration-300"
    >
      Go Home
    </router-link>
  </div>
</template>

<script setup lang="ts">
// No script needed for simple 404 page
</script>
