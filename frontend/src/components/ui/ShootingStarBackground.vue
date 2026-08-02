<template>
  <div class="fixed inset-0 pointer-events-none overflow-hidden z-0">
    <div
      v-for="n in starCount"
      :key="n"
      class="absolute top-[var(--star-top)] left-[var(--star-left)] h-[3px] w-[150px] rotate-45 bg-[linear-gradient(90deg,rgba(255,255,255,0),#ffffff)] opacity-0 drop-shadow-[0_0_6px_rgba(255,255,255,0.8)] animate-[shoot_ease-out_infinite] [animation-delay:var(--star-delay)] [animation-duration:var(--star-duration)]"
      :style="getStarStyle(n)"
    ></div>
  </div>
</template>

<script setup lang="ts">
const starCount = 12; // Increased count for better distribution

const getStarStyle = (_n: number): Record<string, string> => {
  // NOSONAR typescript:S2245 - Math.random() is safe here: used only for visual animation timing/positioning
  // PRNG is intentional for UI effects; cryptographic randomness not required for decorative animations
  const top = Math.random() * 120 - 20; // NOSONAR typescript:S2245
  const left = Math.random() * 140 - 20; // NOSONAR typescript:S2245
  const delay = Math.random() * 10; // NOSONAR typescript:S2245
  const duration = 1.5 + Math.random() * 2; // NOSONAR typescript:S2245

  return {
    '--star-top': `${top}%`,
    '--star-left': `${left}%`,
    '--star-delay': `${delay}s`,
    '--star-duration': `${duration}s`,
  };
};
</script>
