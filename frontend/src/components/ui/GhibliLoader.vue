<template>
  <div class="flex flex-col items-center justify-center p-8">
    <div class="flex items-end gap-6 h-[60px] scale-125 transform">
      <!-- Sprite 1: Large Bouncer -->
      <div
        class="relative w-[50px] h-[50px] bg-[#2a2a2a] rounded-full shadow-[0_0_0_3px_rgba(42,42,42,0.1),0_0_0_6px_rgba(42,42,42,0.05)] before:absolute before:inset-[-2px] before:bg-inherit before:rounded-inherit before:blur-[2px] before:z-[-1] animate-[big-bounce_1s_infinite_alternate_cubic-bezier(0.5,0.05,1,0.5)]"
      >
        <div
          class="absolute bg-white rounded-full top-[35%] left-[10px] w-[14px] h-[14px] after:absolute after:bg-black after:rounded-full after:w-[40%] after:h-[40%] after:top-[30%] after:left-[30%]"
        ></div>
        <div
          class="absolute bg-white rounded-full top-[35%] right-[10px] w-[14px] h-[14px] after:absolute after:bg-black after:rounded-full after:w-[40%] after:h-[40%] after:top-[30%] after:left-[30%]"
        ></div>
      </div>

      <!-- Sprite 2: The Observer (Holding Candy) -->
      <div
        class="relative w-[40px] h-[40px] bg-[#2a2a2a] rounded-full shadow-[0_0_0_3px_rgba(42,42,42,0.1),0_0_0_6px_rgba(42,42,42,0.05)] before:absolute before:inset-[-2px] before:bg-inherit before:rounded-inherit before:blur-[2px] before:z-[-1] animate-[gentle-sway_2s_infinite_ease-in-out]"
      >
        <div
          class="absolute bg-white rounded-full top-[35%] left-[6px] w-[12px] h-[12px] after:absolute after:bg-black after:rounded-full after:w-[40%] after:h-[40%] after:top-[30%] after:left-[30%]"
        ></div>
        <div
          class="absolute bg-white rounded-full top-[35%] right-[6px] w-[12px] h-[12px] after:absolute after:bg-black after:rounded-full after:w-[40%] after:h-[40%] after:top-[30%] after:left-[30%]"
        ></div>
        <!-- Star Candy (Konpeito) -->
        <div
          class="absolute w-3 h-3 bg-[#ffb7b2] top-[-15px] left-1/2 -translate-x-1/2 rotate-45 animate-[spin-candy_3s_linear_infinite] before:absolute before:w-full before:h-full before:bg-inherit before:rotate-[30deg] after:absolute after:w-full after:h-full after:bg-inherit after:rotate-[60deg]"
        ></div>
      </div>

      <!-- Sprite 3: The Little One -->
      <div
        class="relative w-[30px] h-[30px] bg-[#2a2a2a] rounded-full shadow-[0_0_0_3px_rgba(42,42,42,0.1),0_0_0_6px_rgba(42,42,42,0.05)] before:absolute before:inset-[-2px] before:bg-inherit before:rounded-inherit before:blur-[2px] before:z-[-1] animate-[small-jump_0.6s_infinite_alternate_cubic-bezier(0.4,0,0.2,1)]"
      >
        <div
          class="absolute bg-white rounded-full top-[35%] left-[4px] w-[10px] h-[10px] after:absolute after:bg-black after:rounded-full after:w-[40%] after:h-[40%] after:top-[30%] after:left-[30%] after:animate-[look-around_2s_infinite]"
        ></div>
        <div
          class="absolute bg-white rounded-full top-[35%] right-[4px] w-[10px] h-[10px] after:absolute after:bg-black after:rounded-full after:w-[40%] after:h-[40%] after:top-[30%] after:left-[30%] after:animate-[look-around_2s_infinite]"
        ></div>
      </div>
    </div>

    <!-- Loading Text -->
    <div v-if="text" class="mt-6 text-center">
      <p class="text-brown font-serif text-lg tracking-wide animate-pulse font-medium">
        {{ text }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  text: {
    type: String,
    default: undefined,
  },
});
</script>
