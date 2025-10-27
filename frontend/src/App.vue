<script setup lang="ts">
import NavBar from './components/NavBar.vue';
import { onErrorCaptured } from 'vue';
import { isBrowserExtensionError, logBrowserExtensionError } from './utils/browserExtensionHandler';

// Handle browser extension errors at the app level
onErrorCaptured((err) => {
  if (isBrowserExtensionError(err)) {
    logBrowserExtensionError(err, 'App component');
    return false;
  }
  return true;
});
</script>

<template>
<div class="flex flex-col min-h-screen">
  <NavBar />
  <div class="flex-1 overflow-auto">
    <router-view />
  </div>
</div>
</template>


