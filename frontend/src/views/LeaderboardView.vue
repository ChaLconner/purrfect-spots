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
          role="tablist"
          aria-label="Leaderboard period filter"
          class="bg-white/80 backdrop-blur-sm rounded-full p-1 shadow-sm border border-stone-200 inline-flex"
        >
          <button
            v-for="p in periods"
            :key="p.value"
            role="tab"
            :aria-selected="period === p.value"
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
            :is-current-user="authStore.user?.id === user.id"
            @click.prevent="openProfileDrawer(user.username || user.id)"
          />
        </div>
      </div>

      <!-- Sticky Current User Rank Bar (if user logged in & present in top entries) -->
      <div
        v-if="currentUserEntry"
        class="sticky bottom-6 mt-6 bg-amber-500/95 backdrop-blur-md text-white rounded-2xl shadow-2xl p-4 border border-amber-300 flex items-center justify-between transition-all duration-300 transform hover:scale-[1.01]"
      >
        <div class="flex items-center gap-4">
          <span class="text-xl font-bold font-heading bg-white/20 px-3 py-1 rounded-lg">
            #{{ currentUserEntry.rank }}
          </span>
          <div>
            <div class="text-xs font-bold uppercase tracking-wider text-amber-100">
              {{ $t('common.you') || 'You' }}
            </div>
            <div class="font-bold text-lg font-heading">
              {{ currentUserEntry.user.name }}
            </div>
          </div>
        </div>
        <div class="text-right">
          <div class="text-2xl font-black font-heading leading-none">
            {{ currentUserEntry.user.total_treats_received }}
          </div>
          <div class="text-[10px] uppercase font-bold text-amber-100 mt-0.5">
            {{ $t('leaderboardPage.stats.treatsReceived') }}
          </div>
        </div>
      </div>
    </div>

    <!-- Profile Drawer -->
    <ProfileDrawer
      :is-open="isDrawerOpen"
      :user-id="selectedUserId"
      @close="isDrawerOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../stores/authStore';
import { TreatsService } from '../services/treatsService';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import { useSeo } from '@/composables/useSeo';
import LeaderboardItem, {
  type LeaderboardUser,
} from '@/components/leaderboard/LeaderboardItem.vue';
import ProfileDrawer from '@/components/profile/ProfileDrawer.vue';
import { showError } from '@/stores/toast';

const { setMetaTags } = useSeo();
const { t } = useI18n();
const authStore = useAuthStore();
const loading = ref(true);
const users = ref<LeaderboardUser[]>([]);
const period = ref<'weekly' | 'monthly' | 'all_time'>('all_time');

// Drawer State
const isDrawerOpen = ref(false);
const selectedUserId = ref<string | null>(null);
 
const openProfileDrawer = (userId?: string): void => {
  if (!userId) return;
  selectedUserId.value = userId;
  isDrawerOpen.value = true;
};

const periods = computed(() => [
  { label: t('leaderboardPage.periods.weekly'), value: 'weekly' },
  { label: t('leaderboardPage.periods.monthly'), value: 'monthly' },
  { label: t('leaderboardPage.periods.allTime'), value: 'all_time' },
]);

// Current User Position
const currentUserIndex = computed(() => {
  if (!authStore.user?.id) return -1;
  return users.value.findIndex((u) => u.id === authStore.user?.id);
});

const currentUserEntry = computed(() => {
  if (currentUserIndex.value >= 0) {
    return {
      user: users.value[currentUserIndex.value],
      rank: currentUserIndex.value + 1,
    };
  }
  return null;
});

let currentLeaderboardRequestId = 0;

const normalizeLeaderboardUsers = (data: unknown): LeaderboardUser[] => {
  if (!Array.isArray(data)) return [];
  return data.map((item: Record<string, unknown>, index: number) => {
    const rawId = item.id || item.user_id;
    const rawName = item.name || item.username;
    const rawPicture = item.picture || item.avatar_url;
    const treatsReceived = item.total_treats_received ?? item.treats_received ?? item.count ?? 0;

    return {
      id: String(rawId || `user-${index}`),
      name: String(rawName || 'Anonymous Spotter'),
      username: item.username ? String(item.username) : undefined,
      picture: rawPicture ? String(rawPicture) : undefined,
      total_treats_received: Number(treatsReceived),
    };
  });
};

const fetchLeaderboard = async (): Promise<void> => {
  const reqId = ++currentLeaderboardRequestId;
  loading.value = true;
  try {
    const data = await TreatsService.getLeaderboard(period.value);
    if (reqId === currentLeaderboardRequestId) {
      users.value = normalizeLeaderboardUsers(data);
    }
  } catch (e: unknown) {
    if (reqId === currentLeaderboardRequestId) {
      console.error('Failed to load leaderboard:', e);
      showError(t('leaderboardPage.errorLoad'));
    }
  } finally {
    if (reqId === currentLeaderboardRequestId) {
      loading.value = false;
    }
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
