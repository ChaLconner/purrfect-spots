<template>
  <div v-if="active" class="treat-burst-container">
    <div
      v-for="p in particles"
      :key="p.id"
      class="particle"
      :style="{
        '--tx': p.tx + 'px',
        '--ty': p.ty + 'px',
        '--r': p.r + 'deg',
        '--s': p.s,
        left: '50%',
        top: '50%',
        animationDelay: p.delay + 'ms',
      }"
    >
      <img src="/give-treat.png" alt="treat" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  trigger: boolean;
}>();

const active = ref(false);
interface Particle {
  id: number;
  tx: number;
  ty: number;
  r: number;
  s: number;
  delay: number;
}

const particles = ref<Particle[]>([]);

function createBurst(): void {
  active.value = true;
  const count = 12;
  const newParticles = [];

  for (let i = 0; i < count; i++) {
    const angle = (i / count) * 360;
    const distance = 80 + Math.random() * 60;
    const tx = Math.cos(angle * (Math.PI / 180)) * distance;
    const ty = Math.sin(angle * (Math.PI / 180)) * distance;

    newParticles.push({
      id: Date.now() + i,
      tx,
      ty,
      r: Math.random() * 360,
      s: 0.5 + Math.random() * 0.5,
      delay: Math.random() * 100,
    });
  }

  particles.value = newParticles;

  setTimeout(() => {
    active.value = false;
    particles.value = [];
  }, 1000);
}

watch(
  () => props.trigger,
  (newVal) => {
    if (newVal) {
      createBurst();
    }
  }
);
</script>

<style scoped>
.treat-burst-container {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
}

.particle {
  position: absolute;
  width: 24px;
  height: 24px;
  opacity: 0;
  animation: burst 0.8s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
}

.particle img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

@keyframes burst {
  0% {
    transform: translate(-50%, -50%) scale(0) rotate(0deg);
    opacity: 0;
  }
  20% {
    opacity: 1;
  }
  100% {
    transform: translate(calc(-50% + var(--tx)), calc(-50% + var(--ty))) scale(var(--s))
      rotate(var(--r));
    opacity: 0;
  }
}
</style>
