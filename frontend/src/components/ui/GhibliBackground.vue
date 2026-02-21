<template>
  <div
    class="fixed inset-0 z-0 pointer-events-none overflow-hidden box-border"
    style="background: linear-gradient(180deg, #eaf6f3 0%, #ffffff 100%)"
  >
    <!-- Decorative Background Elements -->
    <div class="absolute inset-0 w-full h-full z-0">
      <!-- CSS Clouds -->
      <div
        class="absolute bg-white/96 rounded-[50px] blur-[8px] animate-float-cloud before:content-[''] before:absolute before:bg-inherit before:rounded-full after:content-[''] after:absolute after:bg-inherit after:rounded-full w-[120px] h-[40px] before:w-[40px] before:h-[40px] before:-top-[15px] before:left-[55px] after:w-[50px] after:h-[50px] after:-top-[25px] after:left-[20px] top-[15%] -left-[150px] [animation-duration:45s] scale-[1.2]"
      ></div>
      <div
        class="absolute bg-white/96 rounded-[50px] blur-[8px] animate-float-cloud before:content-[''] before:absolute before:bg-inherit before:rounded-full after:content-[''] after:absolute after:bg-inherit after:rounded-full w-[120px] h-[40px] before:w-[40px] before:h-[40px] before:-top-[15px] before:left-[55px] after:w-[50px] after:h-[50px] after:-top-[25px] after:left-[20px] top-[35%] -left-[150px] [animation-duration:60s] [animation-delay:-20s] scale-[0.8]"
      ></div>
      <div
        class="absolute bg-white/96 rounded-[50px] blur-[8px] animate-float-cloud before:content-[''] before:absolute before:bg-inherit before:rounded-full after:content-[''] after:absolute after:bg-inherit after:rounded-full w-[120px] h-[40px] before:w-[40px] before:h-[40px] before:-top-[15px] before:left-[55px] after:w-[50px] after:h-[50px] after:-top-[25px] after:left-[20px] top-[5%] -left-[150px] [animation-duration:50s] [animation-delay:-10s] scale-[1.5] opacity-[0.72]"
      ></div>

      <!-- New Cloud Patterns -->
      <div
        class="absolute bg-white/96 rounded-[50px] blur-[8px] animate-float-cloud before:content-[''] before:absolute before:bg-inherit before:rounded-full after:content-[''] after:absolute after:bg-inherit after:rounded-full w-[100px] h-[35px] before:w-[35px] before:h-[35px] before:-top-[15px] before:left-[45px] after:w-[45px] after:h-[45px] after:-top-[25px] after:left-[15px] top-[25%] -left-[150px] [animation-duration:55s] [animation-delay:-5s] scale-[1.1]"
      ></div>
      <div
        class="absolute bg-white/96 rounded-[50px] blur-[8px] animate-float-cloud before:content-[''] before:absolute before:bg-inherit before:rounded-full after:content-[''] after:absolute after:bg-inherit after:rounded-full w-[140px] h-[45px] before:w-[45px] before:h-[45px] before:-top-[20px] before:left-[75px] after:w-[55px] after:h-[55px] after:-top-[30px] after:left-[30px] top-[45%] -left-[150px] [animation-duration:70s] [animation-delay:-30s] scale-[0.9]"
      ></div>
      <div
        class="absolute bg-white/96 rounded-[50px] blur-[8px] animate-float-cloud before:content-[''] before:absolute before:bg-inherit before:rounded-full after:content-[''] after:absolute after:bg-inherit after:rounded-full w-[90px] h-[30px] before:w-[25px] before:h-[25px] before:-top-[12px] before:left-[45px] after:w-[35px] after:h-[35px] after:-top-[20px] after:left-[10px] top-[10%] -left-[150px] [animation-duration:65s] [animation-delay:-15s] scale-[1.3]"
      ></div>

      <!-- CSS Fireflies -->
      <div
        class="absolute rounded-full bg-[#fff9c4] shadow-[0_0_10px_2px_rgba(255,249,196,0.6)] animate-float-firefly opacity-0 w-[6px] h-[6px] top-[40%] left-[20%] [animation-delay:0s]"
      ></div>
      <div
        class="absolute rounded-full bg-[#fff9c4] shadow-[0_0_10px_2px_rgba(255,249,196,0.6)] animate-float-firefly opacity-0 w-[4px] h-[4px] top-[60%] right-[30%] [animation-delay:2s]"
      ></div>
      <div
        class="absolute rounded-full bg-[#fff9c4] shadow-[0_0_10px_2px_rgba(255,249,196,0.6)] animate-float-firefly opacity-0 w-[6px] h-[6px] top-[20%] right-[15%] [animation-delay:4s]"
      ></div>
    </div>

    <ShootingStarBackground />
  </div>
</template>

<script setup lang="ts">
import ShootingStarBackground from '@/components/ui/ShootingStarBackground.vue';
</script>
