<template>
  <div class="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 bg-stone-50">
    <GhibliBackground />
    <div class="max-w-4xl mx-auto relative z-10">
      <div class="text-center mb-12">
        <h1 class="text-4xl md:text-5xl font-heading font-black text-brown mb-4 drop-shadow-sm">
          Cat Leaderboard
        </h1>
        <p class="text-xl text-brown-light font-body max-w-2xl mx-auto">
          The most spoiled cats! Give treats to your favorites to help them climb the ranks.
        </p>
      </div>

      <!-- Leaderboard Card -->
      <div
        class="bg-white/80 backdrop-blur-md rounded-3xl shadow-xl overflow-hidden border border-white/50"
      >
        <!-- Loading State -->
        <div v-if="loading" class="p-12 flex justify-center">
          <GhibliLoader text="Calculating treations..." />
        </div>

        <!-- Empty State -->
        <div v-else-if="users.length === 0" class="p-12 text-center text-stone-500">
          No treats given yet. Be the first to spread some joy.
        </div>

        <!-- List -->
        <div v-else class="divide-y divide-stone-100">
          <router-link
            v-for="(user, index) in users"
            :key="user.id"
            :to="`/profile/${user.username || user.id}`"
            class="flex items-center p-6 hover:bg-white/50 transition-colors duration-300 gap-6 group cursor-pointer"
          >
            <div class="flex-shrink-0 w-12 text-center">
              <span
                class="text-2xl font-bold font-heading"
                :class="{
                  'text-yellow-500': index === 0,
                  'text-stone-400': index === 1,
                  'text-orange-400': index === 2,
                  'text-stone-300': index > 2,
                }"
                >#{{ index + 1 }}</span
              >
            </div>

            <!-- Avatar -->
            <div class="flex-shrink-0 relative">
              <img
                :src="user.picture || '/default-avatar.svg'"
                class="w-16 h-16 rounded-full object-cover border-4 border-white shadow-md transition-transform duration-300 group-hover:scale-105"
                :class="{
                  'ring-4 ring-yellow-400/30 animate-bounce-slow': index === 0,
                  'ring-4 ring-stone-300/30': index === 1,
                  'ring-4 ring-orange-300/30': index === 2,
                }"
                :alt="`${user.name || 'User'}'s avatar`"
              />
            </div>

            <!-- Info -->
            <div class="flex-grow min-w-0">
              <h3
                class="text-xl font-bold text-brown truncate font-heading group-hover:text-terracotta transition-colors"
              >
                {{ user.name || 'Anonymous Spotter' }}
              </h3>
              <p class="text-sm text-stone-500 font-medium">
                {{ getRankTitle(index) }}
              </p>
            </div>

            <div class="flex-shrink-0 text-right">
              <div class="flex items-center gap-2 justify-end">
                <span class="text-3xl font-black text-terracotta">{{
                  user.total_treats_received || 0
                }}</span>
              </div>
              <p class="text-xs text-stone-400 font-bold uppercase tracking-wider">
                Treats Received
              </p>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { TreatsService } from '../services/treatsService';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import { useSeo } from '@/composables/useSeo';

interface LeaderboardUser {
  id: string;
  name: string;
  username?: string;
  picture?: string;
  total_treats_received: number;
}

const { setMetaTags } = useSeo();
const loading = ref(true);
const users = ref<LeaderboardUser[]>([]);

const getRankTitle = (index: number) => {
  if (index === 0) return 'The Cat Whisperer';
  if (index === 1) return 'Treat Master';
  if (index === 2) return 'Feline Friend';
  return 'Spotter';
};

onMounted(async () => {
  setMetaTags({
    title: 'Leaderboard | Purrfect Spots',
    description: 'See the most spoiled cats and top contributors in the Purrfect Spots community.',
  });

  try {
    users.value = await TreatsService.getLeaderboard();
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.animate-bounce-slow {
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(-5%);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: translateY(0);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
}
</style>
