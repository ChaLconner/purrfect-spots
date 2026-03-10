<template>
  <div
    class="flex items-center justify-center transition-all duration-300"
    :class="[size === 'small' ? 'flex-row gap-3 p-0' : 'flex-col p-8']"
  >
    <div
      class="flex items-end transition-all duration-500"
      :class="[size === 'small' ? 'gap-2 h-6 scale-75' : 'gap-6 h-[60px] scale-125 transform']"
    >
      <!-- Sprite 1: Large Bouncer (Hidden in small) -->
      <div
        v-if="size !== 'small'"
        class="relative w-[50px] h-[50px] bg-[#2a2a2a] rounded-full shadow-[0_0_0_3px_rgba(42,42,42,0.1),0_0_0_6px_rgba(42,42,42,0.05)] before:absolute before:inset-[-2px] before:bg-inherit before:rounded-inherit before:blur-[2px] before:z-[-1] animate-[big-bounce_1s_infinite_alternate_cubic-bezier(0.5,0.05,1,0.5)]"
      >
        <div
          class="absolute bg-white rounded-full top-[35%] left-[10px] w-[14px] h-[14px] after:absolute after:bg-black after:rounded-full after:w-[40%] after:h-[40%] after:top-[30%] after:left-[30%]"
        ></div>
        <div
          class="absolute bg-white rounded-full top-[35%] right-[10px] w-[14px] h-[14px] after:absolute after:bg-black after:rounded-full after:w-[40%] after:h-[40%] after:top-[30%] after:left-[30%]"
        ></div>
      </div>

      <!-- Sprite 2: The Observer -->
      <div
        class="relative bg-[#2a2a2a] rounded-full shadow-[0_0_0_2px_rgba(42,42,42,0.1)] before:absolute before:inset-[-1px] before:bg-inherit before:rounded-inherit before:blur-[1px] before:z-[-1] animate-[gentle-sway_2s_infinite_ease-in-out]"
        :class="
          size === 'small'
            ? 'w-6 h-6'
            : 'w-[40px] h-[40px] shadow-[0_0_0_3px_rgba(42,42,42,0.1),0_0_0_6px_rgba(42,42,42,0.05)] before:inset-[-2px] before:blur-[2px]'
        "
      >
        <div
          class="absolute bg-white rounded-full"
          :class="
            size === 'small'
              ? 'top-[35%] left-[4px] w-[7px] h-[7px]'
              : 'top-[35%] left-[6px] w-[12px] h-[12px]'
          "
        >
          <div class="absolute bg-black rounded-full w-[40%] h-[40%] top-[30%] left-[30%]"></div>
        </div>
        <div
          class="absolute bg-white rounded-full"
          :class="
            size === 'small'
              ? 'top-[35%] right-[4px] w-[7px] h-[7px]'
              : 'top-[35%] right-[6px] w-[12px] h-[12px]'
          "
        >
          <div class="absolute bg-black rounded-full w-[40%] h-[40%] top-[30%] left-[30%]"></div>
        </div>
      </div>

      <!-- Sprite 3: The Little One -->
      <div
        class="relative bg-[#2a2a2a] rounded-full shadow-[0_0_0_2px_rgba(42,42,42,0.1)] before:absolute before:inset-[-1px] before:bg-inherit before:rounded-inherit before:blur-[1px] before:z-[-1] animate-[small-jump_0.6s_infinite_alternate_cubic-bezier(0.4,0,0.2,1)]"
        :class="
          size === 'small'
            ? 'w-5 h-5'
            : 'w-[30px] h-[30px] shadow-[0_0_0_3px_rgba(42,42,42,0.1),0_0_0_6px_rgba(42,42,42,0.05)] before:inset-[-2px] before:blur-[2px]'
        "
      >
        <div
          class="absolute bg-white rounded-full"
          :class="
            size === 'small'
              ? 'top-[35%] left-[3px] w-[6px] h-[6px]'
              : 'top-[35%] left-[4px] w-[10px] h-[10px]'
          "
        >
          <div
            class="absolute bg-black rounded-full w-[40%] h-[40%] top-[30%] left-[30%] animate-[look-around_2s_infinite]"
          ></div>
        </div>
        <div
          class="absolute bg-white rounded-full"
          :class="
            size === 'small'
              ? 'top-[35%] right-[3px] w-[6px] h-[6px]'
              : 'top-[35%] right-[4px] w-[10px] h-[10px]'
          "
        >
          <div
            class="absolute bg-black rounded-full w-[40%] h-[40%] top-[30%] left-[30%] animate-[look-around_2s_infinite]"
          ></div>
        </div>
      </div>
    </div>

    <!-- Loading Text -->
    <div v-if="text" :class="[size === 'small' ? 'mt-0' : 'mt-6 text-center']">
      <p
        class="text-brown font-serif tracking-wide animate-pulse font-medium"
        :class="[size === 'small' ? 'text-sm' : 'text-lg']"
      >
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
  size: {
    type: String,
    default: 'normal',
    validator: (value: string) => ['normal', 'small'].includes(value),
  },
});
</script>
