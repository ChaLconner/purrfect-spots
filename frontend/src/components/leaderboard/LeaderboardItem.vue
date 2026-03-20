<template>
  <router-link
    :to="`/profile/${user.username || user.id}`"
    class="flex items-center p-3 md:p-6 hover:bg-white/50 transition-colors duration-300 gap-3 md:gap-6 group cursor-pointer"
  >
    <!-- Rank -->
    <div class="flex-shrink-0 w-8 md:w-12 text-center">
      <span
        class="text-lg md:text-2xl font-bold font-heading"
        :class="{
          'text-yellow-500': rank === 1,
          'text-stone-400': rank === 2,
          'text-orange-400': rank === 3,
          'text-stone-300': rank > 3,
        }"
      >#{{ rank }}</span>
    </div>

    <!-- Avatar -->
    <div class="flex-shrink-0 relative bg-stone-100 rounded-full">
      <img
        :src="user.picture || getAvatarFallback(user.name)"
        loading="lazy"
        class="w-12 h-12 md:w-16 md:h-16 rounded-full object-cover border-2 md:border-4 border-white shadow-md transition-transform duration-300 group-hover:scale-105"
        :class="{
          'ring-2 md:ring-4 ring-yellow-400/30 animate-bounce-slow': rank === 1,
          'ring-2 md:ring-4 ring-stone-300/30': rank === 2,
          'ring-2 md:ring-4 ring-orange-300/30': rank === 3,
        }"
        :alt="`${user.name || 'User'}'s avatar`"
        @error="handleAvatarError($event, user.name)"
      />
    </div>

    <!-- Info -->
    <div class="flex-grow min-w-0">
      <h3
        class="text-base md:text-xl font-bold text-brown truncate font-heading group-hover:text-terracotta transition-colors"
      >
        {{ user.name || 'Anonymous Spotter' }}
      </h3>
      <p class="text-xs md:text-sm text-stone-500 font-medium truncate">
        {{ getRankTitle(rank - 1) }}
      </p>
    </div>

    <!-- Score -->
    <div class="flex-shrink-0 text-right">
      <div class="flex items-center gap-1 md:gap-2 justify-end">
        <span class="text-xl md:text-3xl font-black text-terracotta leading-none">{{
          user.total_treats_received || 0
        }}</span>
      </div>
      <p
        class="text-[10px] md:text-xs text-stone-400 font-bold uppercase tracking-wider mt-0.5 md:mt-0"
      >
        <span class="hidden sm:inline">Treats Received</span>
        <span class="sm:hidden">Treats</span>
      </p>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { getAvatarFallback, handleAvatarError } from '@/utils/avatar';

export interface LeaderboardUser {
  id: string;
  name: string;
  username?: string;
  picture?: string;
  total_treats_received: number;
}

defineProps<{
  user: LeaderboardUser;
  rank: number;
}>();

const getRankTitle = (index: number): string => {
  if (index === 0) return 'The Cat Whisperer';
  if (index === 1) return 'Treat Master';
  if (index === 2) return 'Feline Friend';
  return 'Spotter';
};
</script>
