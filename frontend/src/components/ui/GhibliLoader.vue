<template>
  <div class="ghibli-loader-container">
    <div class="sprites-group">
      <!-- Sprite 1: The Bouncer -->
      <div class="soot-sprite sprite-1">
        <div class="eyes left"></div>
        <div class="eyes right"></div>
      </div>
      
      <!-- Sprite 2: The Observer -->
      <div class="soot-sprite sprite-2">
        <div class="eyes left"></div>
        <div class="eyes right"></div>
        <div class="star-candy"></div>
      </div>
      
      <!-- Sprite 3: The Little One -->
      <div class="soot-sprite sprite-3">
        <div class="eyes left"></div>
        <div class="eyes right"></div>
      </div>
    </div>
    
    <!-- Loading Text -->
    <div v-if="text" class="mt-6 text-center">
      <p class="text-brown font-serif text-lg tracking-wide animate-pulse font-medium">{{ text }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  text: {
    type: String,
    default: undefined
  }
});
</script>

<style scoped>
.ghibli-loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.sprites-group {
  display: flex;
  align-items: flex-end;
  gap: 1.5rem;
  height: 60px; /* Define height for bounce consistency */
  transform: scale(1.2); 
}

/* Base Soot Sprite */
.soot-sprite {
  background: #2a2a2a;
  border-radius: 50%;
  position: relative;
  /* Fuzzy edges using box-shadows */
  box-shadow: 
    0 0 0 3px rgba(42, 42, 42, 0.1),
    0 0 0 6px rgba(42, 42, 42, 0.05);
}

.soot-sprite::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: inherit;
  border-radius: inherit;
  filter: blur(2px);
  z-index: -1;
}

/* Eyes */
.eyes {
  position: absolute;
  background: white;
  border-radius: 50%;
  top: 35%;
}

.eyes::after {
  content: '';
  position: absolute;
  background: black;
  border-radius: 50%;
  width: 40%;
  height: 40%;
  top: 30%;
  left: 30%;
}

/* Sprite 1: Large Bouncer */
.sprite-1 {
  width: 50px;
  height: 50px;
  animation: big-bounce 1s infinite alternate cubic-bezier(0.5, 0.05, 1, 0.5);
}
.sprite-1 .eyes { width: 14px; height: 14px; }
.sprite-1 .eyes.left { left: 10px; }
.sprite-1 .eyes.right { right: 10px; }

/* Sprite 2: Holding Candy */
.sprite-2 {
  width: 40px;
  height: 40px;
  animation: gentle-sway 2s infinite ease-in-out;
}
.sprite-2 .eyes { width: 12px; height: 12px; }
.sprite-2 .eyes.left { left: 6px; }
.sprite-2 .eyes.right { right: 6px; }

/* Star Candy (Konpeito) */
.star-candy {
  position: absolute;
  width: 12px;
  height: 12px;
  background: #ffb7b2; /* Soft pink */
  top: -15px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  animation: spin-candy 3s linear infinite;
}
.star-candy::before, .star-candy::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: inherit;
  top: 0;
  left: 0;
}
.star-candy::before { transform: rotate(30deg); }
.star-candy::after { transform: rotate(60deg); }

/* Sprite 3: Small Runner */
.sprite-3 {
  width: 30px;
  height: 30px;
  animation: small-jump 0.6s infinite alternate cubic-bezier(0.4, 0, 0.2, 1);
}
.sprite-3 .eyes { width: 10px; height: 10px; }
.sprite-3 .eyes.left { left: 4px; }
.sprite-3 .eyes.right { right: 4px; }
.sprite-3 .eyes.left::after, .sprite-3 .eyes.right::after {
  animation: look-around 2s infinite;
}

/* Animations */
@keyframes big-bounce {
  from { transform: translateY(0) scaleY(1.1); }
  to { transform: translateY(-20px) scaleY(0.9); }
}

@keyframes gentle-sway {
  0%, 100% { transform: rotate(-5deg); }
  50% { transform: rotate(5deg); }
}

@keyframes small-jump {
  from { transform: translateY(0); }
  to { transform: translateY(-10px); }
}

@keyframes look-around {
  0%, 100% { transform: translate(0, 0); }
  25% { transform: translate(-2px, 0); }
  75% { transform: translate(2px, 0); }
}

@keyframes spin-candy {
  from { transform: translateX(-50%) rotate(0deg); }
  to { transform: translateX(-50%) rotate(360deg); }
}
</style>
