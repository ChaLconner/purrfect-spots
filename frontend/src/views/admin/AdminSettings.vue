<template>
  <div class="min-h-screen pb-12">
    <!-- Header Section: Simplified and aligned with other Admin views -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-brown-900 font-display">
        {{ t('admin.settings.title') }}
      </h1>
      <p class="mt-1 text-brown-500">{{ t('admin.settings.subtitle') }}</p>
    </div>

    <!-- Stats & Actions Bar -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-bold text-brown-900">
          {{ t('admin.settings.config_management') }}
        </h2>
        <div class="flex items-center gap-2">
            <button
              class="px-3 py-1.5 text-sm font-medium text-brown-600 bg-sand-50 border border-sand-200 rounded-lg hover:bg-sand-100 transition-colors flex items-center gap-2"
              :disabled="loading"
              @click="fetchSettings(true)"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                :class="{ 'animate-spin': loading }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
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
    </div>

    <!-- Navigation Tabs -->
    <div
      class="flex flex-wrap gap-2 mb-8 p-1.5 bg-sand-50/50 rounded-2xl border border-sand-100/50 backdrop-blur-sm"
    >
      <button
        v-for="cat in navCategories"
        :key="cat"
        class="px-5 py-2 rounded-lg text-xs font-medium transition-all duration-300 uppercase tracking-wider"
        :class="
          activeTab === cat
            ? 'bg-white text-terracotta-600 shadow-sm border border-sand-200'
            : 'text-brown-500 hover:bg-white/50 hover:text-brown-700'
        "
        @click="activeTab = cat"
      >
        {{ t(`admin.settings.categories.${cat}`) }}
        <span
          v-if="cat === 'pending' && pendingCount > 0"
          class="ml-2 px-1.5 py-0.5 bg-terracotta-500 text-white text-xs rounded-full"
        >
          {{ pendingCount }}
        </span>
      </button>
    </div>

    <!-- Content Sections -->
    <TransitionGroup name="fade-list" tag="div" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Pending Approvals Tab -->
      <template v-if="activeTab === 'pending'">
        <div
          v-if="pendingRequests.length === 0"
          class="col-span-full py-20 text-center bg-white rounded-2xl border border-sand-100 shadow-sm"
        >
          <div class="text-6xl mb-4">📜</div>
          <h3 class="text-xl font-bold text-brown-800">
            {{ t('admin.settings.approval.no_pending') }}
          </h3>
          <p class="text-brown-500 mt-2 text-sm italic">
            {{ t('admin.settings.approval.all_processed') }}
          </p>
        </div>        <div
          v-for="req in pendingRequests"
          :key="req.id"
          class="bg-white rounded-2xl shadow-sm border border-sand-100 overflow-hidden hover:shadow-md transition-all border-l-4 border-l-orange-400 group"
        >
          <div class="p-6">
            <div class="flex justify-between items-start mb-4">
              <div>
                <span
                  class="px-2 py-1 bg-orange-50 text-orange-700 text-xs font-semibold rounded-lg uppercase tracking-wider mb-2 inline-block"
                >
                  {{ t('admin.settings.requires_approval') }}
                </span>
                <h3 class="text-lg font-bold text-brown-800">
                  {{ t(`admin.settings.labels.${req.config_key}`, req.config_key) }}
                </h3>
              </div>
              <div class="text-right text-xs text-brown-400 font-mono">
                #{{ req.id.slice(0, 8) }}
              </div>
            </div>

            <div
              class="grid grid-cols-2 gap-4 mb-6 p-4 bg-sand-50/50 rounded-xl border border-sand-100 italic"
            >
              <div>
                <p class="text-xs text-brown-500 uppercase font-medium mb-1">
                  {{ t('admin.settings.history.old_value') }}
                </p>
                <code class="text-sm text-brown-600 truncate block">{{
                  formatValue(req.current_value)
                }}</code>
              </div>
              <div>
                <p class="text-xs text-orange-600 uppercase font-medium mb-1">
                  {{ t('admin.settings.history.new_value') }}
                </p>
                <code class="text-sm text-orange-700 font-bold truncate block">{{
                  formatValue(req.proposed_value)
                }}</code>
              </div>
            </div>

            <div class="flex items-center justify-between gap-4">
              <div class="flex items-center gap-2">
                <div
                  class="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 text-xs font-bold"
                >
                  {{ (req.requester_email ?? 'U').charAt(0).toUpperCase() }}
                </div>
                <div class="text-xs">
                  <p class="text-brown-400">{{ t('admin.settings.approval.maker') }}</p>
                  <p class="text-brown-700 font-medium">{{ req.requester_email }}</p>
                </div>
              </div>

              <div class="flex gap-2">
                <button
                  class="px-4 py-2 text-brown-500 hover:text-red-500 hover:bg-red-50 rounded-lg text-sm font-medium transition-all"
                  @click="rejectRequest(req.id)"
                >
                  {{ t('admin.settings.approval.reject') }}
                </button>
                <button
                  class="px-4 py-2 bg-terracotta-600 hover:bg-terracotta-700 text-white rounded-lg text-sm font-medium shadow-sm transition-all"
                  @click="approveRequest(req.id)"
                >
                  {{ t('admin.settings.approval.approve') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Settings List -->
      <template v-else>
        <div
          v-for="config in filteredSettings"
          :key="config.key"
          class="bg-white rounded-2xl shadow-sm border border-sand-100 overflow-hidden hover:shadow-md transition-all duration-300 group"
          :class="{ 'opacity-60 scale-[0.98]': saving === config.key }"
        >
          <div class="p-6">
            <div class="flex justify-between items-start mb-6">
              <div class="space-y-1.5 min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <h3
                    class="text-lg font-bold text-brown-900 truncate group-hover:text-terracotta-600 transition-colors"
                  >
                    {{ t(`admin.settings.labels.${config.key}`, config.key) }}
                  </h3>
                  <button
                    class="p-1.5 text-brown-300 hover:text-brown-600 hover:bg-sand-50 rounded-lg transition-all"
                    @click="showHistory(config.key)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </button>
                </div>
                <p class="text-xs text-brown-500 line-clamp-2 leading-relaxed opacity-80">
                  {{ config.description || t('admin.settings.no_description') }}
                </p>
              </div>
              <div class="flex flex-col items-end gap-2 ml-4 flex-shrink-0">
                <span
                  class="px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border"
                  :class="
                    config.is_public
                      ? 'bg-emerald-50 text-emerald-600 border-emerald-100'
                      : 'bg-sand-100 text-brown-500 border-sand-200'
                  "
                >
                  {{ config.is_public ? t('common.public') : t('common.private') }}
                </span>
                <span
                  v-if="config.requires_approval"
                  class="px-2 py-0.5 bg-orange-50 text-orange-600 border border-orange-100 rounded-full text-xs font-semibold uppercase tracking-wider"
                >
                  🛡️ {{ t('admin.settings.shielded') }}
                </span>
              </div>
            </div>

            <div class="mt-6 flex flex-col sm:flex-row items-end sm:items-center gap-4">
              <!-- Dynamic Input -->
              <div class="w-full flex-1">
                <template v-if="config.type === 'boolean'">
                  <div
                    class="flex items-center justify-between p-3.5 bg-sand-50/50 rounded-xl border border-sand-100"
                  >
                    <span class="text-sm font-bold text-brown-700">{{
                      editValues[config.key]
                        ? t('common.enabled')
                        : t('common.disabled')
                    }}</span>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input
                        v-model="editValues[config.key]"
                        type="checkbox"
                        class="sr-only peer"
                        @change="markDirty(config.key)"
                      />
                      <div
                        class="w-12 h-6 bg-sand-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-terracotta-500"
                      ></div>
                    </label>
                  </div>
                </template>

                <template v-else-if="config.type === 'integer' || config.type === 'float'">
                  <div class="relative">
                    <input
                      v-model.number="editValues[config.key]"
                      type="number"
                      class="w-full px-4 py-2.5 bg-white border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 transition-all text-brown-800 font-medium outline-none"
                      @input="markDirty(config.key)"
                    />
                  </div>
                </template>

                <template v-else-if="config.type === 'json'">
                  <textarea
                    v-model="editValues[config.key]"
                    rows="4"
                    class="w-full px-4 py-2.5 bg-brown-900 text-sand-50 border-none rounded-lg focus:ring-2 focus:ring-terracotta-500/30 transition-all font-mono text-xs outline-none"
                    @input="markDirty(config.key)"
                  ></textarea>
                </template>

                <template v-else>
                  <input
                    v-model="editValues[config.key]"
                    type="text"
                    class="w-full px-4 py-2.5 bg-white border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 transition-all text-brown-800 font-medium outline-none"
                    @input="markDirty(config.key)"
                  />
                </template>
              </div>

              <div class="flex gap-2 min-w-fit">
                <button
                  v-if="dirtyKeys.has(config.key)"
                  class="p-2 text-brown-400 hover:text-red-500 bg-sand-50 hover:bg-red-50 rounded-lg border border-sand-300 transition-colors"
                  @click="resetSetting(config.key)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
                <button
                  v-if="dirtyKeys.has(config.key)"
                  :disabled="saving === config.key"
                  class="px-4 py-2 bg-terracotta-600 hover:bg-terracotta-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors disabled:opacity-50 flex items-center gap-2"
                  @click="saveSetting(config.key)"
                >
                  <svg
                    v-if="saving === config.key"
                    class="animate-spin h-4 w-4 text-white"
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
                  <span v-else>{{
                    config.requires_approval
                      ? t('admin.settings.approval.approve')
                      : t('common.save')
                  }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </TransitionGroup>

    <!-- History Modal -->
    <Teleport to="body">
      <div
        v-if="historyKey"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black bg-opacity-50"
      >
        <div
          class="bg-white w-full max-w-2xl rounded-xl shadow-xl overflow-hidden border border-sand-100"
        >
          <div class="p-6 border-b border-sand-100 flex justify-between items-center bg-sand-50">
            <h3 class="text-xl font-bold text-brown-900 flex items-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-terracotta-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              {{ t('admin.settings.history.title') }}:
              <span class="text-brown-500 font-mono text-sm">#{{ historyKey }}</span>
            </h3>
            <button
              class="text-brown-400 hover:text-brown-600 p-2 hover:bg-sand-100 rounded-full transition-all"
              @click="historyKey = null"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div class="max-h-[60vh] overflow-y-auto p-6 space-y-4">
            <div v-if="historyLoading" class="flex justify-center py-12">
              <div
                class="animate-spin h-8 w-8 text-emerald-500 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full"
              ></div>
            </div>

            <div v-else-if="history.length === 0" class="text-center py-12 text-brown-400">
              {{ t('admin.settings.history.no_history') }}
            </div>

            <div
              v-for="entry in history"
              :key="entry.id"
              class="p-4 rounded-2xl border border-sand-100 bg-sand-50/30"
            >
              <div class="flex justify-between items-start mb-3">
                <div class="flex items-center gap-2">
                  <div
                    class="w-6 h-6 rounded-full bg-brown-100 flex items-center justify-center text-[10px] font-bold text-brown-600"
                  >
                    {{ (entry.user_email || 'S').charAt(0).toUpperCase() }}
                  </div>
                  <span class="text-sm font-bold text-brown-700">{{
                    entry.user_email || 'System'
                  }}</span>
                </div>
                <span class="text-xs text-brown-400 italic">{{
                  formatDate(entry.created_at)
                }}</span>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="p-2 bg-red-50/30 rounded-lg border border-red-50">
                  <p class="text-xs text-red-500 uppercase font-medium mb-1">
                    {{ t('common.from') }}
                  </p>
                  <code class="text-xs text-red-700 truncate block">{{
                    formatValue(entry.old_value)
                  }}</code>
                </div>
                <div class="p-2 bg-emerald-50/30 rounded-lg border border-emerald-50">
                  <p class="text-xs text-emerald-500 uppercase font-medium mb-1">
                    {{ t('common.to') }}
                  </p>
                  <code class="text-xs text-emerald-700 font-bold truncate block">{{
                    formatValue(entry.new_value)
                  }}</code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Rejection Reason Modal -->
    <BaseConfirmModal
      :is-open="isRejectModalOpen"
      :title="t('admin.settings.approval.reject_title')"
      :message="t('admin.settings.approval.reason_prompt')"
      :confirm-text="t('admin.settings.approval.reject')"
      variant="danger"
      @close="isRejectModalOpen = false"
      @confirm="confirmReject"
    >
      <div class="mt-4">
        <textarea
          v-model="rejectionReason"
          class="w-full px-4 py-2.5 bg-white border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 transition-colors text-brown-800 font-medium"
          :placeholder="t('admin.settings.approval.reason_placeholder')"
          rows="3"
        ></textarea>
      </div>
    </BaseConfirmModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { apiV1 } from '@/utils/api';
import { useToast } from '@/components/toast/use-toast';
import { useI18n } from 'vue-i18n';
import { BaseConfirmModal } from '@/components/ui';

interface SystemConfig {
  key: string;
  value: unknown;
  type: 'string' | 'boolean' | 'integer' | 'float' | 'json';
  description: string | null;
  category: string;
  is_public: boolean;
  is_encrypted: boolean;
  requires_approval: boolean;
  updated_at: string;
}

interface PendingRequest {
  id: string;
  config_key: string;
  current_value: unknown;
  proposed_value: unknown;
  requester_email: string | null;
  created_at: string;
}

interface ConfigHistory {
  id: string;
  old_value: unknown;
  new_value: unknown;
  user_email: string | null;
  created_at: string;
}

const { toast } = useToast();
const { t, locale } = useI18n();

const navCategories = ['all', 'general', 'security', 'infrastructure', 'pdpa', 'ui', 'pending'];
const activeTab = ref('all');
const loading = ref(true);
const saving = ref<string | null>(null);

const settings = ref<SystemConfig[]>([]);
const editValues = ref<Record<string, unknown>>({});
const dirtyKeys = ref<Set<string>>(new Set());

const pendingRequests = ref<PendingRequest[]>([]);
const pendingCount = computed(() => pendingRequests.value.length);

const historyKey = ref<string | null>(null);
const history = ref<ConfigHistory[]>([]);
const historyLoading = ref(false);

const isRejectModalOpen = ref(false);
const pendingRejectId = ref<string | null>(null);
const rejectionReason = ref('');

const filteredSettings = computed(() => {
  if (activeTab.value === 'all') return settings.value;
  if (activeTab.value === 'pending') return [];
  return settings.value.filter((s) => s.category === activeTab.value);
});

const fetchSettings = async (forceRefresh: boolean = false): Promise<void> => {
  loading.value = true;
  try {
    const cacheBust = forceRefresh ? Date.now().toString() : undefined;
    const [settingsData, pendingData] = await Promise.all([
      apiV1.get<SystemConfig[]>(
        cacheBust ? `/admin/settings?cache_bust=${cacheBust}` : '/admin/settings'
      ),
      apiV1.get<PendingRequest[]>(
        cacheBust ? `/admin/settings/pending?cache_bust=${cacheBust}` : '/admin/settings/pending'
      ),
    ]);

    settings.value = settingsData || [];
    pendingRequests.value = pendingData || [];

    const values: Record<string, unknown> = {};
    (settingsData || []).forEach((s) => {
      if (s.type === 'json' && s.value && typeof s.value === 'object') {
        values[s.key] = JSON.stringify(s.value, null, 2);
      } else {
        values[s.key] = s.value;
      }
    });
    editValues.value = values;
    dirtyKeys.value.clear();
  } catch {
    console.error('Failed to fetch settings');
  } finally {
    loading.value = false;
  }
};

const markDirty = (key: string): void => {
  dirtyKeys.value.add(key);
};

const resetSetting = (key: string): void => {
  const config = settings.value.find((s) => s.key === key);
  if (config) {
    if (config.type === 'json' && config.value && typeof config.value === 'object') {
      editValues.value[key] = JSON.stringify(config.value, null, 2);
    } else {
      editValues.value[key] = config.value;
    }
    dirtyKeys.value.delete(key);
  }
};

const saveSetting = async (key: string): Promise<void> => {
  saving.value = key;
  try {
    const config = settings.value.find((s) => s.key === key);
    if (!config) return;

    let value = editValues.value[key];

    if (config.type === 'json' && typeof value === 'string') {
      try {
        value = JSON.parse(value);
      } catch {
        toast({
          title: t('common.error'),
          description: t('admin.settings.invalid_json'),
          variant: 'destructive',
        });
        return;
      }
    }

    const response = await apiV1.put<SystemConfig | PendingRequest & { status: string }>(`/admin/settings/${key}`, {
      value,
    });

    if ('status' in response && response.status === 'pending') {
      toast({ description: t('admin.settings.approval.request_sent'), variant: 'success' });
      void fetchSettings();
    } else {
      const updatedConfig = response as SystemConfig;
      settings.value = settings.value.map((configItem) =>
        configItem.key === key ? updatedConfig : configItem
      );
      dirtyKeys.value.delete(key);
      toast({ description: t('admin.settings.save_success'), variant: 'success' });
    }
  } catch {
    toast({
      title: t('common.error'),
      description: t('admin.settings.save_error'),
      variant: 'destructive',
    });
  } finally {
    saving.value = null;
  }
};

const approveRequest = async (id: string): Promise<void> => {
  try {
    await apiV1.post(`/admin/settings/approve/${id}`, {});
    toast({ description: t('admin.settings.approval.approve_success'), variant: 'success' });
    void fetchSettings();
  } catch {
    toast({
      title: t('common.error'),
      description: t('admin.settings.approval.approve_error'),
      variant: 'destructive',
    });
  }
};

const rejectRequest = (id: string): void => {
  pendingRejectId.value = id;
  rejectionReason.value = '';
  isRejectModalOpen.value = true;
};

const confirmReject = async (): Promise<void> => {
  if (!pendingRejectId.value) return;

  try {
    await apiV1.post(`/admin/settings/reject/${pendingRejectId.value}`, {
      rejection_reason: rejectionReason.value,
    });
    toast({ description: t('admin.settings.approval.reject_success'), variant: 'success' });
    isRejectModalOpen.value = false;
    pendingRejectId.value = null;
    void fetchSettings();
  } catch {
    toast({
      title: t('common.error'),
      description: t('admin.settings.approval.reject_error'),
      variant: 'destructive',
    });
  }
};

const showHistory = async (key: string): Promise<void> => {
  historyKey.value = key;
  historyLoading.value = true;
  try {
    const data = await apiV1.get<ConfigHistory[]>(`/admin/settings/history/${key}`);
    history.value = data || [];
  } catch {
    console.error('Failed to fetch history');
  } finally {
    historyLoading.value = false;
  }
};

const formatValue = (val: unknown): string => {
  if (typeof val === 'boolean') return val ? t('common.enabled') : t('common.disabled');
  if (typeof val === 'object' && val !== null) return JSON.stringify(val);
  return String(val ?? '');
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleString(locale.value);
};

onMounted(() => {
  fetchSettings();
});
</script>

<style scoped>
.font-display {
  font-family: 'Outfit', sans-serif;
}

.fade-list-enter-active,
.fade-list-leave-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-list-enter-from,
.fade-list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
</style>
