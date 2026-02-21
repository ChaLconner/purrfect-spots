<template>
  <div
    v-if="active"
    class="absolute inset-0 pointer-events-none z-50 flex items-center justify-center"
  >
    <div
      v-for="p in particles"
      :key="p.id"
      class="absolute w-6 h-6 opacity-0 animate-[burst_0.8s_cubic-bezier(0.1,0.8,0.3,1)_forwards]"
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
      <img src="/give-treat.png" alt="treat" class="w-full h-full object-contain" />
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
