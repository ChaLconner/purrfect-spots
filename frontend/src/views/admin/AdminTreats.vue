<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-brown-900 font-display">
          {{ t('admin.treats.title') }}
        </h1>
        <p class="text-brown-600 mt-1">{{ t('admin.treats.subtitle') }}</p>
      </div>
      <button
        class="px-4 py-2 bg-terracotta-500 text-white rounded-lg hover:bg-terracotta-600 transition-all shadow-sm hover:shadow-md flex items-center gap-2"
        @click="openGrantModal"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"
            clip-rule="evenodd"
          />
        </svg>
        {{ t('admin.treats.grant_treats') }}
      </button>
    </div>

    <!-- Stats summary cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <template v-if="statsLoading">
        <div
          v-for="i in 3"
          :key="i"
          class="bg-white p-6 rounded-xl shadow-sm border border-sand-200 animate-pulse"
        >
          <div class="h-3 w-24 bg-sand-200 rounded mb-3"></div>
          <div class="h-8 w-32 bg-sand-200 rounded"></div>
        </div>
      </template>
      <template v-else>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-sand-200">
          <p class="text-xs text-brown-500 uppercase tracking-widest font-semibold mb-1">
            {{ t('admin.treats.total_in_circulation') }}
          </p>
          <p class="text-3xl font-bold text-terracotta-600">
            {{ stats.total_in_circulation?.toLocaleString() || 0 }}
          </p>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-sand-200">
          <p class="text-xs text-brown-500 uppercase tracking-widest font-semibold mb-1">
            {{ t('admin.treats.given_to_cats') }}
          </p>
          <p class="text-3xl font-bold text-brown-800">
            {{ stats.total_given_to_cats?.toLocaleString() || 0 }}
          </p>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-sand-200">
          <p class="text-xs text-brown-500 uppercase tracking-widest font-semibold mb-1">
            {{ t('admin.treats.users_with_treats') }}
          </p>
          <p class="text-3xl font-bold text-brown-800">{{ stats.user_count_with_balance || 0 }}</p>
        </div>
      </template>
    </div>

    <!-- Transactions section -->
    <div class="bg-white rounded-xl shadow-sm border border-sand-200 overflow-hidden">
      <div
        class="px-6 py-4 border-b border-sand-100 flex flex-wrap justify-between items-center gap-3 bg-sand-50/50"
      >
        <h2 class="text-lg font-bold text-brown-800">
          {{ t('admin.treats.transaction_history') }}
        </h2>
        <div class="flex items-center gap-3">
          <!-- Filter by type -->
          <select
            v-model="filterType"
            class="text-sm border border-sand-300 rounded-lg px-3 py-1.5 bg-white text-brown-700 focus:ring-2 focus:ring-terracotta-400 outline-none"
            @change="onFilterChange"
          >
            <option value="">{{ t('admin.treats.filter_all_types') }}</option>
            <option value="purchase">{{ t('admin.treats.type_purchase') }}</option>
            <option value="give">{{ t('admin.treats.type_give') }}</option>
            <option value="system_grant">{{ t('admin.treats.type_system_grant') }}</option>
            <option value="daily_bonus">{{ t('admin.treats.type_daily_bonus') }}</option>
          </select>
          <button
            class="text-sm text-brown-500 hover:text-brown-700 transition-colors flex items-center gap-1"
            @click="fetchTransactions"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              :class="{ 'animate-spin': loading }"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {{ t('common.refresh') }}
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead>
            <tr class="bg-sand-50/30 text-xs font-bold text-brown-600 uppercase tracking-wider">
              <th class="px-6 py-3">{{ t('admin.treats.table.date') }}</th>
              <th class="px-6 py-3">{{ t('admin.treats.table.type') }}</th>
              <th class="px-6 py-3 text-right">{{ t('admin.treats.table.amount') }}</th>
              <th class="px-6 py-3">{{ t('admin.treats.table.from') }}</th>
              <th class="px-6 py-3">{{ t('admin.treats.table.to') }}</th>
              <th class="px-6 py-3">{{ t('admin.treats.table.description') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-sand-100">
            <tr v-if="loading">
              <td colspan="6" class="px-6 py-4">
                <div v-for="i in 5" :key="i" class="flex gap-4 py-3 animate-pulse">
                  <div class="h-3 w-28 bg-sand-200 rounded"></div>
                  <div class="h-5 w-16 bg-sand-200 rounded-full"></div>
                  <div class="h-3 w-10 bg-sand-200 rounded ml-auto"></div>
                  <div class="h-3 w-24 bg-sand-200 rounded"></div>
                  <div class="h-3 w-24 bg-sand-200 rounded"></div>
                  <div class="h-3 w-32 bg-sand-200 rounded"></div>
                </div>
              </td>
            </tr>
            <tr v-else-if="!transactions.length" class="text-center text-brown-400">
              <td colspan="6" class="px-6 py-12">{{ t('admin.treats.table.no_transactions') }}</td>
            </tr>
            <tr
              v-for="txn in transactions"
              :key="txn.id"
              class="hover:bg-sand-50/50 transition-colors"
            >
              <td class="px-6 py-4 text-xs text-brown-500">
                {{ new Date(txn.created_at).toLocaleString() }}
              </td>
              <td class="px-6 py-4">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider"
                  :class="{
                    'bg-green-100 text-green-700': txn.transaction_type === 'purchase',
                    'bg-blue-100 text-blue-700': txn.transaction_type === 'give',
                    'bg-purple-100 text-purple-700': txn.transaction_type === 'system_grant',
                    'bg-amber-100 text-amber-700': txn.transaction_type === 'daily_bonus',
                    'bg-sand-100 text-sand-700': ![
                      'purchase',
                      'give',
                      'system_grant',
                      'daily_bonus',
                    ].includes(txn.transaction_type),
                  }"
                >
                  {{ t('admin.treats.type_' + txn.transaction_type) }}
                </span>
              </td>
              <td class="px-6 py-4 text-right font-bold text-brown-700">{{ txn.amount }}</td>
              <td class="px-6 py-4 text-sm">
                <div v-if="txn.from_user" class="leading-tight">
                  <p class="font-medium text-brown-800">{{ txn.from_user.name }}</p>
                  <p class="text-xs text-brown-400">{{ txn.from_user.email }}</p>
                </div>
                <span v-else class="text-xs text-brown-300 italic">{{
                  t('admin.treats.table.system')
                }}</span>
              </td>
              <td class="px-6 py-4 text-sm">
                <div v-if="txn.to_user" class="leading-tight">
                  <p class="font-medium text-brown-800">{{ txn.to_user.name }}</p>
                  <p class="text-xs text-brown-400">{{ txn.to_user.email }}</p>
                </div>
                <span v-else class="text-xs text-brown-300 italic">{{
                  t('admin.treats.table.na')
                }}</span>
              </td>
              <td class="px-6 py-4 text-sm text-brown-600 truncate max-w-[200px]">
                {{ txn.description }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="totalTransactions > 0"
        class="px-6 py-4 border-t border-sand-100 flex justify-between items-center bg-sand-50/30"
      >
        <p class="text-sm text-brown-500">
          {{
            t('admin.treats.pagination_showing', {
              from: paginationFrom,
              to: paginationTo,
              total: totalTransactions,
            })
          }}
        </p>
        <div class="flex items-center gap-2">
          <button
            :disabled="currentPage === 1"
            class="px-3 py-1.5 text-sm border border-sand-300 rounded-lg text-brown-600 hover:bg-sand-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            @click="prevPage"
          >
            {{ t('common.previous') }}
          </button>
          <span class="text-sm text-brown-600 font-medium">
            {{ t('admin.treats.pagination_page', { page: currentPage, total: totalPages }) }}
          </span>
          <button
            :disabled="currentPage >= totalPages"
            class="px-3 py-1.5 text-sm border border-sand-300 rounded-lg text-brown-600 hover:bg-sand-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            @click="nextPage"
          >
            {{ t('common.next') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Manual Grant Modal -->
    <div
      v-if="showGrantModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brown-900/60 backdrop-blur-sm"
      @click.self="closeGrantModal"
    >
      <div
        class="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-8 border border-sand-200 transform transition-all"
        @click.stop
      >
        <h3 class="text-2xl font-bold text-brown-900 mb-6 font-display">
          {{ t('admin.treats.grant_treats') }}
        </h3>

        <form class="space-y-4" @submit.prevent="submitGrant">
          <!-- User search -->
          <div class="relative">
            <label class="block text-sm font-bold text-brown-700 mb-1">{{
              t('admin.treats.user_search_label')
            }}</label>
            <input
              v-model="userSearchQuery"
              type="text"
              :placeholder="t('admin.treats.user_search_placeholder')"
              class="w-full px-4 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-400 outline-none text-brown-800 bg-sand-50"
              autocomplete="off"
              @input="onUserSearch"
              @focus="showUserDropdown = true"
            />
            <!-- User dropdown -->
            <div
              v-if="showUserDropdown && (userSearchResults.length || userSearching)"
              class="absolute z-10 w-full mt-1 bg-white border border-sand-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
            >
              <div v-if="userSearching" class="px-4 py-3 text-sm text-brown-400 italic">
                {{ t('common.searching') }}
              </div>
              <div
                v-for="user in userSearchResults"
                :key="user.id"
                class="px-4 py-2 hover:bg-sand-50 cursor-pointer transition-colors"
                @mousedown.prevent="selectUser(user)"
              >
                <p class="text-sm font-medium text-brown-800">{{ user.name }}</p>
                <p class="text-xs text-brown-400">{{ user.email }}</p>
              </div>
              <div
                v-if="
                  !userSearching && userSearchResults.length === 0 && userSearchQuery.length >= 2
                "
                class="px-4 py-3 text-sm text-brown-400 italic"
              >
                {{ t('admin.treats.no_users_found') }}
              </div>
            </div>
          </div>

          <!-- Selected user display -->
          <div
            v-if="grantForm.user_id"
            class="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-green-600"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clip-rule="evenodd"
              />
            </svg>
            <span class="text-sm text-green-800 font-medium">{{ selectedUserName }}</span>
            <button
              type="button"
              class="ml-auto text-green-600 hover:text-green-800"
              @click="clearSelectedUser"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          </div>

          <div>
            <label class="block text-sm font-bold text-brown-700 mb-1">{{
              t('admin.treats.amount')
            }}</label>
            <input
              v-model.number="grantForm.amount"
              type="number"
              required
              min="1"
              max="10000"
              class="w-full px-4 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-400 outline-none text-brown-800 bg-sand-50"
            />
          </div>
          <div>
            <label class="block text-sm font-bold text-brown-700 mb-1">{{
              t('admin.treats.reason')
            }}</label>
            <textarea
              v-model="grantForm.reason"
              required
              rows="3"
              maxlength="500"
              :placeholder="t('admin.treats.reason_placeholder')"
              class="w-full px-4 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-400 outline-none text-brown-800 bg-sand-50 resize-y"
            ></textarea>
            <p class="text-xs text-brown-400 mt-1 text-right">{{ grantForm.reason.length }}/500</p>
          </div>

          <div class="flex gap-4 pt-4">
            <button
              type="button"
              class="flex-1 px-4 py-2 border border-sand-300 text-brown-600 rounded-lg hover:bg-sand-50 transition-colors font-bold"
              @click="closeGrantModal"
            >
              {{ t('common.cancel') }}
            </button>
            <button
              type="submit"
              :disabled="submitting || !grantForm.user_id"
              class="flex-1 px-4 py-2 bg-terracotta-500 text-white rounded-lg hover:bg-terracotta-600 transition-all font-bold disabled:opacity-50 flex justify-center items-center"
            >
              <svg
                v-if="submitting"
                class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              {{ t('admin.treats.grant_btn') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { apiV1 } from '@/utils/api';
import { useToast } from '@/components/toast/use-toast';
import { useI18n } from 'vue-i18n';

interface TreatStats {
  total_in_circulation: number;
  total_given_to_cats: number;
  user_count_with_balance: number;
}

interface Transaction {
  id: string;
  created_at: string;
  transaction_type: string;
  amount: number;
  description: string;
  from_user?: { name: string; email: string };
  to_user?: { name: string; email: string };
}

interface UserSearchResult {
  id: string;
  name: string;
  email: string;
}

const PAGE_SIZE = 20;

const { toast } = useToast();
const { t } = useI18n();

const loading = ref(true);
const statsLoading = ref(true);
const submitting = ref(false);
const stats = ref<Partial<TreatStats>>({});
const transactions = ref<Transaction[]>([]);
const showGrantModal = ref(false);

// Pagination
const currentPage = ref(1);
const totalTransactions = ref(0);

const totalPages = computed(() => Math.max(1, Math.ceil(totalTransactions.value / PAGE_SIZE)));
const paginationFrom = computed(() =>
  totalTransactions.value === 0 ? 0 : (currentPage.value - 1) * PAGE_SIZE + 1
);
const paginationTo = computed(() =>
  Math.min(currentPage.value * PAGE_SIZE, totalTransactions.value)
);

// Filter
const filterType = ref('');

// User search
const userSearchQuery = ref('');
const userSearchResults = ref<UserSearchResult[]>([]);
const userSearching = ref(false);
const showUserDropdown = ref(false);
const selectedUserName = ref('');
let userSearchTimeout: ReturnType<typeof setTimeout> | null = null;

const grantForm = ref({
  user_id: '',
  amount: 10,
  reason: t('admin.treats.default_reason'),
});

const fetchStats = async (): Promise<void> => {
  statsLoading.value = true;
  try {
    const data = await apiV1.get<TreatStats>('/admin/treats/stats');
    stats.value = data || {};
  } catch (error) {
    console.error('Failed to fetch stats:', error);
    toast({
      title: t('common.error'),
      description: t('admin.treats.load_error'),
      variant: 'destructive',
    });
  } finally {
    statsLoading.value = false;
  }
};

const fetchTransactions = async (): Promise<void> => {
  loading.value = true;
  try {
    const offset = (currentPage.value - 1) * PAGE_SIZE;
    let url = `/admin/treats/transactions?limit=${PAGE_SIZE}&offset=${offset}`;
    if (filterType.value) {
      url += `&transaction_type=${filterType.value}`;
    }
    const data = await apiV1.get<{ data: Transaction[]; total: number }>(url);
    transactions.value = data?.data || [];
    totalTransactions.value = data?.total || 0;
  } catch (error) {
    console.error('Failed to fetch transactions:', error);
  } finally {
    loading.value = false;
  }
};

const onFilterChange = (): void => {
  currentPage.value = 1;
  fetchTransactions();
};

const prevPage = (): void => {
  if (currentPage.value > 1) {
    currentPage.value--;
    fetchTransactions();
  }
};

const nextPage = (): void => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    fetchTransactions();
  }
};

// User search
const onUserSearch = (): void => {
  if (userSearchTimeout) clearTimeout(userSearchTimeout);

  if (userSearchQuery.value.length < 2) {
    userSearchResults.value = [];
    return;
  }

  userSearchTimeout = setTimeout(async () => {
    userSearching.value = true;
    try {
      const data = await apiV1.get<{ data: UserSearchResult[] }>(
        `/admin/treats/users/search?q=${encodeURIComponent(userSearchQuery.value)}`
      );
      userSearchResults.value = data?.data || [];
      showUserDropdown.value = true;
    } catch (error) {
      console.error('Failed to search users:', error);
    } finally {
      userSearching.value = false;
    }
  }, 300);
};

const selectUser = (user: UserSearchResult): void => {
  grantForm.value.user_id = user.id;
  selectedUserName.value = `${user.name} (${user.email})`;
  userSearchQuery.value = '';
  userSearchResults.value = [];
  showUserDropdown.value = false;
};

const clearSelectedUser = (): void => {
  grantForm.value.user_id = '';
  selectedUserName.value = '';
  userSearchQuery.value = '';
};

const openGrantModal = (): void => {
  grantForm.value = { user_id: '', amount: 10, reason: t('admin.treats.default_reason') };
  selectedUserName.value = '';
  userSearchQuery.value = '';
  userSearchResults.value = [];
  showGrantModal.value = true;
};

const closeGrantModal = (): void => {
  showGrantModal.value = false;
  showUserDropdown.value = false;
};

const submitGrant = async (): Promise<void> => {
  if (!grantForm.value.user_id) return;

  submitting.value = true;
  try {
    await apiV1.post('/admin/treats/grant', grantForm.value);
    showGrantModal.value = false;

    toast({
      description: t('admin.treats.grant_success'),
      variant: 'success',
    });

    // Refresh data
    fetchStats();
    fetchTransactions();
  } catch (error) {
    console.error('Failed to grant treats:', error);
    toast({
      title: t('common.error'),
      description: t('admin.treats.grant_error'),
      variant: 'destructive',
    });
  } finally {
    submitting.value = false;
  }
};

// Close dropdown on outside click
const handleClickOutside = (e: MouseEvent): void => {
  const target = e.target as HTMLElement;
  if (!target.closest('.relative')) {
    showUserDropdown.value = false;
  }
};

onMounted(() => {
  fetchStats();
  fetchTransactions();
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  if (userSearchTimeout) clearTimeout(userSearchTimeout);
});
</script>

<style scoped>
.font-display {
  font-family: 'Outfit', sans-serif;
}
</style>
