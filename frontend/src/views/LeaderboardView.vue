<template>
  <div class="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 bg-stone-50">
    <GhibliBackground />
    <div class="max-w-4xl mx-auto relative z-10">
      <div class="text-center mb-12">
        <h1 class="text-4xl md:text-5xl font-heading font-black text-brown mb-4 drop-shadow-sm">
          {{ $t('leaderboardPage.title') }}
        </h1>
        <p class="text-xl text-brown-light font-body max-w-2xl mx-auto">
          {{ $t('leaderboardPage.subtitle') }}
        </p>
      </div>

      <!-- Time Period Filter -->
      <div class="flex justify-center mb-8">
        <div
          class="bg-white/80 backdrop-blur-sm rounded-full p-1 shadow-sm border border-stone-200 inline-flex"
        >
          <button
            v-for="p in periods"
            :key="p.value"
            :class="[
              'px-6 py-2 rounded-full text-sm font-medium transition-all duration-200',
              period === p.value
                ? 'bg-brown text-white shadow-md'
                : 'text-stone-600 hover:text-brown hover:bg-stone-100',
            ]"
            @click="period = p.value as any"
          >
            {{ p.label }}
          </button>
        </div>
      </div>

      <!-- Leaderboard Card -->
      <div
        class="bg-white/80 backdrop-blur-md rounded-3xl shadow-xl overflow-hidden border border-white/50"
      >
        <!-- Loading State -->
        <div v-if="loading" class="p-12 flex justify-center">
          <GhibliLoader :text="$t('leaderboardPage.loading')" />
        </div>

        <!-- Empty State -->
        <div v-else-if="users.length === 0" class="p-12 text-center text-stone-500">
          {{ $t('leaderboardPage.empty') }}
        </div>

        <!-- List -->
        <div v-else class="divide-y divide-stone-100">
          <LeaderboardItem
            v-for="(user, index) in users"
            :key="user.id"
            :user="user"
            :rank="index + 1"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { TreatsService } from '../services/treatsService';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import { useSeo } from '@/composables/useSeo';
import LeaderboardItem, {
  type LeaderboardUser,
} from '@/components/leaderboard/LeaderboardItem.vue';
import { showError } from '@/store/toast';

const { setMetaTags } = useSeo();
const { t } = useI18n();
const loading = ref(true);
const users = ref<LeaderboardUser[]>([]);
const period = ref<'weekly' | 'monthly' | 'all_time'>('all_time');

const periods = computed(() => [
  { label: t('leaderboardPage.periods.weekly'), value: 'weekly' },
  { label: t('leaderboardPage.periods.monthly'), value: 'monthly' },
  { label: t('leaderboardPage.periods.allTime'), value: 'all_time' },
]);

const fetchLeaderboard = async () => {
  loading.value = true;
  try {
    const data = await TreatsService.getLeaderboard(period.value);
    // Ensure data matches LeaderboardUser interface if not guaranteed by service
    users.value = data as LeaderboardUser[];
  } catch (e: unknown) {
    console.error('Failed to load leaderboard:', e);
    showError(t('leaderboardPage.errorLoad'));
  } finally {
    loading.value = false;
  }
};

watch(period, () => {
  fetchLeaderboard();
});

onMounted(async () => {
  setMetaTags({
    title: t('leaderboardPage.meta.title') + ' | Purrfect Spots',
    description: t('leaderboardPage.meta.description'),
  });

  await fetchLeaderboard();
});
</script>
