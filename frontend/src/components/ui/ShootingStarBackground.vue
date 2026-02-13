<template>
  <div class="shooting-stars-container fixed inset-0 pointer-events-none overflow-hidden z-0">
    <div v-for="n in starCount" :key="n" class="shooting-star" :style="getStarStyle(n)"></div>
  </div>
</template>

<script setup lang="ts">
const starCount = 12; // Increased count for better distribution

const getStarStyle = (_n: number): Record<string, string> => {
  // nosec typescript:S2245 - Math.random() is safe here: used only for visual animation timing/positioning
  // PRNG is intentional for UI effects; cryptographic randomness not required for decorative animations
  const top = Math.random() * 120 - 20; // Start from -20% to 100% height
  const left = Math.random() * 140 - 20; // Start from -20% to 120% width
  const delay = Math.random() * 10; // Slightly shorter max delay for more activity
  const duration = 1.5 + Math.random() * 2; // Faster: 1.5-3.5s

  return {
    top: `${top}%`,
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
  };
};
</script>

<style scoped>
.shooting-star {
  position: absolute;
  width: 150px; /* Longer tail */
  height: 3px; /* Thicker */
  background: linear-gradient(90deg, rgba(255, 255, 255, 0), #ffffff); /* Solid white head */
  filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.8)); /* Stronger glow */
  transform: rotate(45deg);
  opacity: 0;
  animation-name: shoot;
  animation-timing-function: ease-out;
  animation-iteration-count: infinite;
}

/* 
  Animation:
  Start: top-left area
  End: bottom-right area (further travel)
*/
@keyframes shoot {
  0% {
    transform: translateX(0) translateY(0) rotate(45deg);
    opacity: 1;
  }
  100% {
    transform: translateX(500px) translateY(500px) rotate(45deg); /* Longer travel */
    opacity: 0;
  }
}
</style>
