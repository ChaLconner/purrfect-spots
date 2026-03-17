<template>
  <img
    src="/logo.png"
    alt="Purrfect Spots Logo"
    class="purrfect-logo-img"
  />
</template>

<script lang="ts" setup>
/**
 * Modern Purrfect Spots visual identity component.
 * Features the signature orange cat mascot and location pin.
 */
</script>

<style scoped>
.purrfect-logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.purrfect-logo-img:hover {
  transform: scale(1.05) rotate(-2deg);
}
</style>

