<template>
  <div class="fixed inset-0 z-0 pointer-events-none overflow-hidden" style="background: linear-gradient(180deg, #EAF6F3 0%, #ffffff 100%);">
    <!-- Decorative Background Elements -->
    <div class="gallery-bg-decorations absolute inset-0 w-full h-full">
      <!-- CSS Clouds -->
      <div class="css-cloud cloud-1"></div>
      <div class="css-cloud cloud-2"></div>
      <div class="css-cloud cloud-3"></div>
      <!-- New Cloud Patterns -->
      <div class="css-cloud cloud-4 cloud-pattern-2"></div>
      <div class="css-cloud cloud-5 cloud-pattern-3"></div>
      <div class="css-cloud cloud-6 cloud-pattern-4"></div>
      
      <!-- CSS Soot Sprites (Susuwatari) -->
      <div class="soot-sprite soot-1">
        <div class="eyes"></div>
      </div>
      <div class="soot-sprite soot-2">
        <div class="eyes"></div>
      </div>
      
      <!-- CSS Fireflies -->
      <div class="firefly firefly-1"></div>
      <div class="firefly firefly-2"></div>
      <div class="firefly firefly-3"></div>
    </div>

    <ShootingStarBackground />
  </div>
</template>

<script setup lang="ts">
import ShootingStarBackground from '@/components/ui/ShootingStarBackground.vue';
</script>

<style scoped>
/* Background Decorations */
.gallery-bg-decorations {
  /* position handled by tailwind classes in template */
  z-index: 0;
}

/* --- CSS Clouds --- */
.css-cloud {
  background: rgba(255, 255, 255, 0.96);
  width: 120px;
  height: 40px;
  border-radius: 50px;
  position: absolute;
  filter: blur(8px); /* Soft Ghibli look */
  animation: float-cloud linear infinite;
}

.css-cloud::after, .css-cloud::before {
  content: '';
  position: absolute;
  background: inherit;
  border-radius: 50%;
}

.css-cloud::after {
  width: 50px;
  height: 50px;
  top: -25px;
  left: 20px;
}

.css-cloud::before {
  width: 40px;
  height: 40px;
  top: -15px;
  left: 55px;
}

/* Base Cloud Positions */
.cloud-1 { top: 15%; left: -150px; animation-duration: 45s; transform: scale(1.2); }
.cloud-2 { top: 35%; left: -150px; animation-duration: 60s; animation-delay: -20s; transform: scale(0.8); }
.cloud-3 { top: 5%; left: -150px; animation-duration: 50s; animation-delay: -10s; transform: scale(1.5); opacity: 0.72; }

/* New Cloud Positions */
.cloud-4 { top: 25%; left: -150px; animation-duration: 55s; animation-delay: -5s; transform: scale(1.1); }
.cloud-5 { top: 45%; left: -150px; animation-duration: 70s; animation-delay: -30s; transform: scale(0.9); }
.cloud-6 { top: 10%; left: -150px; animation-duration: 65s; animation-delay: -15s; transform: scale(1.3); }

/* New Cloud Patterns */
/* Pattern 2: Puffy Top (Tall & Narrow) */
.cloud-pattern-2 { width: 100px; height: 35px; }
.cloud-pattern-2::after { width: 45px; height: 45px; top: -25px; left: 15px; }
.cloud-pattern-2::before { width: 35px; height: 35px; top: -15px; left: 45px; }

/* Pattern 3: Wide & Flat (Cumulus) */
.cloud-pattern-3 { width: 140px; height: 45px; }
.cloud-pattern-3::after { width: 55px; height: 55px; top: -30px; left: 30px; }
.cloud-pattern-3::before { width: 45px; height: 45px; top: -20px; left: 75px; }

/* Pattern 4: Small & Scattered */
.cloud-pattern-4 { width: 90px; height: 30px; }
.cloud-pattern-4::after { width: 35px; height: 35px; top: -20px; left: 10px; }
.cloud-pattern-4::before { width: 25px; height: 25px; top: -12px; left: 45px; }

@keyframes float-cloud {
  0% { transform: translateX(0); }
  100% { transform: translateX(120vw); }
}

/* --- Soot Sprites (Susuwatari) --- */
.soot-sprite {
  width: 40px;
  height: 40px;
  background: #2a2a2a;
  border-radius: 50%;
  position: absolute;
  /* Fuzzy edges */
  box-shadow: 
    0 0 0 4px rgba(42, 42, 42, 0.1),
    0 0 0 8px rgba(42, 42, 42, 0.05);
  animation: soot-bounce 3s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite;
}

.eyes {
  position: absolute;
  top: 10px;
  left: 8px;
  width: 24px;
  height: 12px;
}

/* Whites of the eyes */
.eyes::before, .eyes::after {
  content: '';
  position: absolute;
  width: 10px;
  height: 10px;
  background: white;
  border-radius: 50%;
  animation: soot-blink 4s infinite;
}

.eyes::before { left: 0; }
.eyes::after { right: 0; }

.soot-1 { 
  bottom: 50px; 
  right: 50px; 
  animation-duration: 4s;
}

.soot-2 { 
  bottom: 80px; 
  left: 60px; 
  transform: scale(0.8);
  animation-duration: 5s;
  animation-delay: 1s;
}

@keyframes soot-bounce {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-15px) rotate(5deg); }
}

@keyframes soot-blink {
  0%, 96%, 100% { transform: scaleY(1); }
  98% { transform: scaleY(0.1); }
}

/* --- Fireflies --- */
.firefly {
  position: absolute;
  width: 6px;
  height: 6px;
  background: #fff9c4;
  border-radius: 50%;
  box-shadow: 0 0 10px 2px rgba(255, 249, 196, 0.6);
  opacity: 0;
  animation: float-firefly 8s ease-in-out infinite;
}

.firefly-1 { top: 40%; left: 20%; animation-delay: 0s; }
.firefly-2 { top: 60%; right: 30%; animation-delay: 2s; width: 4px; height: 4px; }
.firefly-3 { top: 20%; right: 15%; animation-delay: 4s; }

@keyframes float-firefly {
  0% { transform: translate(0, 0); opacity: 0; }
  10% { opacity: 0.8; }
  50% { transform: translate(20px, -30px); opacity: 0.4; }
  90% { opacity: 0.8; }
  100% { transform: translate(-10px, -50px); opacity: 0; }
}
</style>
